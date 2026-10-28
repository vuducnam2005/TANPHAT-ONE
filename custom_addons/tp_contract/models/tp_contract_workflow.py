import hashlib
import hmac
import json
import re
import secrets
import uuid
from decimal import Decimal

from psycopg2 import errors as pg_errors

from odoo import fields, models
from odoo.exceptions import ConcurrencyError
from odoo.fields import Domain
from odoo.tools import SQL, float_repr

from .tp_contract import CONTRACT_TYPES, WORKFLOW_CONTEXT
from .tp_contract_line import TAX_BASES
from odoo.addons.tp_contract.exceptions import ContractWorkflowError
from odoo.addons.tp_project.models.tp_project_grant import CAPABILITIES

KEY_PATTERN = re.compile(r'[A-Za-z0-9_.:-]{8,128}')
DECIMAL_PATTERN = re.compile(r'-?\d{1,20}(\.\d{1,10})?')
OPEN_STATES = ('draft', 'in_review', 'returned')
MAX_LINES = 500
MAX_ISSUES = 100
# Amounts pass through Odoo float columns; more significant digits would lose precision.
MAX_AMOUNT_DIGITS = 15
CONTRACT_TYPE_KEYS = frozenset(key for key, _label in CONTRACT_TYPES)
TAX_BASIS_KEYS = frozenset(key for key, _label in TAX_BASES)
CAPABILITY_KEYS = tuple(key for key, _label in CAPABILITIES)

# Capabilities each action needs; changing or removing amounts adds FINANCIAL_EDIT.
ACTION_CAPABILITIES = {
    'create_contract': ('contract_draft_edit',),
    'create_amendment': ('contract_draft_edit',),
    'edit_draft': ('contract_draft_edit',),
    'submit_review': ('contract_submit', 'financial_read'),
    'return_review': ('contract_review_commercial', 'financial_read'),
    'begin_rework': ('contract_draft_edit',),
}
FINANCIAL_EDIT = ('financial_read', 'financial_draft_edit')
REVIEWER_CAPABILITIES = frozenset({'contract_review_commercial', 'financial_read'})


def _error(status, code, message, **details):
    return ContractWorkflowError(status, code, message, details or None)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


# Payload parsers check shape and types only (400). Business rules such as
# required text, currency or amount checks run after the capability guard (422).

def _object(value, where, *, required=(), optional=()):
    if not isinstance(value, dict):
        raise _error(400, 'invalid_request', f'{where} must be a JSON object.', field=where)
    unknown = sorted(set(value) - set(required) - set(optional))
    if unknown:
        raise _error(400, 'invalid_request', 'The request contains unsupported fields.', fields=[f'{where}.{key}' for key in unknown])
    missing = [key for key in required if key not in value]
    if missing:
        raise _error(400, 'invalid_request', 'Required fields are missing.', fields=[f'{where}.{key}' for key in missing])
    return value


def _int(value, field, *, allow_none=False):
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise _error(400, 'invalid_request', f'{field} must be a positive integer.', field=field)
    return value


def _text(value, field, *, max_length, allow_none=True):
    if value is None and allow_none:
        return None
    if not isinstance(value, str):
        raise _error(400, 'invalid_request', f'{field} must be a string.', field=field)
    value = value.strip()
    if len(value) > max_length:
        raise _error(400, 'invalid_request', f'{field} is longer than {max_length} characters.', field=field)
    return value or None


def _choice(value, field, choices):
    if value not in choices:
        raise _error(400, 'invalid_request', f'{field} has an unsupported value.', field=field)
    return value


def _parse_amount(value, where):
    if value is None:
        return None
    _object(value, where, required=('state', 'value', 'tax_basis'))
    raw = value['value']
    if raw is not None and (not isinstance(raw, str) or not DECIMAL_PATTERN.fullmatch(raw)):
        raise _error(400, 'invalid_request', f'{where}.value must be a decimal string or null.', field=f'{where}.value')
    return {
        'state': _choice(value['state'], f'{where}.state', ('unconfirmed', 'confirmed')),
        'value': None if raw is None else Decimal(raw),
        'tax_basis': _choice(value['tax_basis'], f'{where}.tax_basis', TAX_BASIS_KEYS),
    }


def _parse_lines(value):
    if not isinstance(value, list) or len(value) > MAX_LINES:
        raise _error(400, 'invalid_request', f'lines must be a list of at most {MAX_LINES} items.', field='lines')
    lines, seen = [], set()
    for index, item in enumerate(value):
        where = f'lines[{index}]'
        _object(item, where, required=('scope_key', 'name'), optional=('amount',))
        key = _text(item['scope_key'], f'{where}.scope_key', max_length=64, allow_none=False)
        if key in seen:
            raise _error(400, 'invalid_request', 'Each scope key may appear once.', field=f'{where}.scope_key')
        seen.add(key)
        line = {'scope_key': key, 'name': _text(item['name'], f'{where}.name', max_length=255, allow_none=False)}
        if 'amount' in item:
            line['amount'] = _parse_amount(item['amount'], f'{where}.amount')
        lines.append(line)
    return lines


def _parse_revision_fields(value, where='revision'):
    _object(value, where, optional=('name', 'reference'))
    result = {}
    if 'name' in value:
        result['name'] = _text(value['name'], f'{where}.name', max_length=255, allow_none=False)
    if 'reference' in value:
        result['reference'] = _text(value['reference'], f'{where}.reference', max_length=128)
    return result


def _parse_header(value, where):
    _object(value, where, optional=('code', 'name', 'contract_type', 'partner_id', 'currency'))
    result = {}
    for key, max_length in (('code', 64), ('name', 255), ('currency', 3)):
        if key in value:
            result[key] = _text(value[key], f'{where}.{key}', max_length=max_length, allow_none=False)
    if 'contract_type' in value:
        result['contract_type'] = _choice(value['contract_type'], f'{where}.contract_type', CONTRACT_TYPE_KEYS)
    if 'partner_id' in value:
        result['partner_id'] = _int(value['partner_id'], f'{where}.partner_id', allow_none=True)
    return result


def _parse_create_contract(payload):
    _object(payload, 'body', required=('project_id', 'code', 'name', 'contract_type', 'currency'),
            optional=('partner_id', 'revision', 'lines'))
    data = _parse_header({key: payload[key] for key in ('code', 'name', 'contract_type', 'currency', 'partner_id') if key in payload}, 'body')
    data['project_id'] = _int(payload['project_id'], 'body.project_id')
    data['revision'] = _parse_revision_fields(payload.get('revision') or {})
    data['lines'] = _parse_lines(payload['lines']) if 'lines' in payload else []
    return data


def _parse_version(payload):
    return _int(payload['expected_version'], 'body.expected_version')


def _parse_create_amendment(payload):
    _object(payload, 'body', required=('expected_version', 'name'), optional=('reference',))
    return {'expected_version': _parse_version(payload)} | _parse_revision_fields(
        {key: payload[key] for key in ('name', 'reference') if key in payload}, 'body',
    )


def _parse_edit_draft(payload):
    _object(payload, 'body', required=('expected_version',), optional=('contract', 'revision', 'lines'))
    if len(payload) == 1:
        raise _error(400, 'invalid_request', 'Nothing to change: send contract, revision or lines.')
    data = {'expected_version': _parse_version(payload)}
    if 'contract' in payload:
        data['contract'] = _parse_header(payload['contract'], 'contract')
    if 'revision' in payload:
        data['revision'] = _parse_revision_fields(payload['revision'])
    if 'lines' in payload:
        data['lines'] = _parse_lines(payload['lines'])
    return data


def _parse_submit_review(payload):
    _object(payload, 'body', required=('expected_version', 'reviewer_id'), optional=('fix_summary',))
    return {
        'expected_version': _parse_version(payload),
        'reviewer_id': _int(payload['reviewer_id'], 'body.reviewer_id'),
        'fix_summary': _text(payload.get('fix_summary'), 'body.fix_summary', max_length=2000),
    }


def _parse_return_review(payload):
    _object(payload, 'body', required=('expected_version', 'reason'), optional=('issues',))
    issues = payload.get('issues') or []
    if not isinstance(issues, list) or len(issues) > MAX_ISSUES:
        raise _error(400, 'invalid_request', f'issues must be a list of at most {MAX_ISSUES} items.', field='body.issues')
    parsed = []
    for index, issue in enumerate(issues):
        where = f'body.issues[{index}]'
        _object(issue, where, required=('note',), optional=('scope_key',))
        parsed.append({
            'scope_key': _text(issue.get('scope_key'), f'{where}.scope_key', max_length=64),
            'note': _text(issue['note'], f'{where}.note', max_length=1000),
        })
    return {
        'expected_version': _parse_version(payload),
        'reason': _text(payload['reason'], 'body.reason', max_length=2000),
        'issues': parsed,
    }


def _parse_begin_rework(payload):
    _object(payload, 'body', required=('expected_version', 'reason'))
    return {
        'expected_version': _parse_version(payload),
        'reason': _text(payload['reason'], 'body.reason', max_length=2000),
    }


PARSERS = {
    'create_contract': _parse_create_contract,
    'create_amendment': _parse_create_amendment,
    'edit_draft': _parse_edit_draft,
    'submit_review': _parse_submit_review,
    'return_review': _parse_return_review,
    'begin_rework': _parse_begin_rework,
}


def _require_text(value, field, code):
    if not value:
        raise _error(422, code, f'{field} is required.', field=field)
    return value


def _money_text(value, currency):
    return float_repr(currency.round(value), currency.decimal_places)


def _amount_key(amount, currency):
    if not amount:
        return None
    value = _money_text(amount.amount, currency) if amount.amount_state == 'confirmed' else None
    return amount.amount_state, value, amount.tax_basis


class TpContractWorkflow(models.AbstractModel):
    """Service for the CTR-002a draft, submit, return and rework actions.

    Every action runs in the caller's transaction: it resolves the scope with
    the caller's rights (404), checks idempotency before anything else, locks
    the contract row, rechecks assignment and capability grants (403), compares
    the aggregate version (409) and only then writes with superuser rights under
    the workflow context, together with audit, outbox and idempotency records.
    Any exception rolls the whole action back. Methods are private, so none of
    them is callable over RPC.
    """

    _name = 'tp.contract.workflow'
    _description = 'Tan Phat Contract Workflow Service'

    def _tp_run(self, action, payload, *, key, contract_id=None, revision_id=None, request_id=None):
        """Execute ``action`` for the current user and return the affected records.

        :returns: dict with ``contract``, ``revision``, ``submission`` (records
            in the caller's environment) and ``replayed``.
        :raises ContractWorkflowError: mapped by callers to API errors.
        """
        if action not in PARSERS:
            raise ValueError(f'Unknown contract workflow action {action!r}')
        if not isinstance(key, str) or not KEY_PATTERN.fullmatch(key):
            raise _error(400, 'invalid_request', 'An Idempotency-Key of 8-128 letters, digits or ._:- is required.')
        if not self.env.user.has_group('tp_core.group_user'):
            raise _error(403, 'forbidden', 'Tan Phat platform membership is required.')
        if not isinstance(payload, dict):
            raise _error(400, 'invalid_request', 'The request body must be a JSON object.')
        if action == 'create_contract':
            data = PARSERS[action](payload)
            project = self.env['project.project'].search([('id', '=', data['project_id']), ('tp_managed', '=', True)], limit=1)
            if not project:
                raise _error(404, 'not_found', 'The requested project was not found.')
            contract = revision = None
            object_ref = f'project:{project.id}'
        else:
            contract = self._tp_find_contract(contract_id)
            revision = None
            object_ref = f'contract:{contract.id}'
            if action != 'create_amendment':
                revision = self.env['tp.contract.revision'].search([
                    ('id', '=', revision_id), ('contract_id', '=', contract.id),
                ], limit=1)
                if not revision:
                    raise _error(404, 'not_found', 'The requested revision was not found.')
                object_ref += f'/revision:{revision.id}'
            data = PARSERS[action](payload)
            project = contract.project_id

        fingerprint = self._tp_fingerprint(action, object_ref, payload)
        replay = self._tp_replay(action, key, object_ref, fingerprint)
        if replay is not None:
            return replay
        claim = self._tp_claim(action, key, object_ref, fingerprint, project)
        context = {'action': action, 'request_id': request_id}
        if action == 'create_contract':
            result = self._tp_create_contract(project, data, context)
        elif action == 'create_amendment':
            result = self._tp_create_amendment(contract, data, context)
        else:
            result = getattr(self, f'_tp_{action}')(contract, revision, data, context)
        claim.with_context(**{WORKFLOW_CONTEXT: True}).write({
            'required_capabilities': ','.join(result['capabilities']),
            'result_contract_id': result['contract'].id,
            'result_revision_id': result['revision'].id,
            'result_submission_id': result['submission'].id if result.get('submission') else False,
        })
        return self._tp_result(result['contract'], result['revision'], result.get('submission'), replayed=False)

    # Scope, capability, version and idempotency

    def _tp_find_contract(self, contract_id):
        # Records outside the caller's scope are indistinguishable from missing ones.
        contract = self.env['tp.contract'].search([('id', '=', contract_id)], limit=1) if contract_id else None
        if not contract:
            raise _error(404, 'not_found', 'The requested contract was not found.')
        return contract

    def _tp_capabilities(self, project, department, user=None):
        """Capabilities ``user`` holds in the project/department scope.

        Without an active project assignment the user holds none, whatever the
        grants or the platform groups say.
        """
        user = user or self.env.user
        assigned = self.env['tp.project.assignment'].sudo().search_count([
            ('project_id', '=', project.id), ('user_id', '=', user.id), ('active', '=', True),
        ], limit=1)
        if not assigned:
            return set()
        Grant = self.env['tp.project.grant']
        return {capability for capability in CAPABILITY_KEYS if Grant._tp_has_capability(project, capability, department, user)}

    def _tp_require(self, contract_or_project, capabilities, department=None):
        if contract_or_project._name == 'tp.contract':
            record = contract_or_project.sudo()
            project, department = record.project_id, record.department_id
        else:
            project = contract_or_project.sudo()
        held = self._tp_capabilities(project, department)
        missing = [capability for capability in capabilities if capability not in held]
        if missing:
            raise _error(403, 'forbidden', 'You do not hold the capability for this action in the contract scope.',
                         missing_capabilities=missing)

    def _tp_lock(self, contract):
        """Lock the contract row and return its current aggregate version.

        A concurrent writer that committed first makes this statement fail with
        a serialization error, which Odoo retries; the retry then sees the new
        version and answers 409 stale_version.
        """
        self.env.flush_all()
        self.env.cr.execute(SQL('SELECT aggregate_version FROM tp_contract WHERE id = %s FOR UPDATE', contract.id))
        version = self.env.cr.fetchone()[0]
        self.env.invalidate_all()
        return version

    def _tp_guard(self, contract, version, expected_version, capabilities):
        self._tp_require(contract, capabilities)
        if expected_version != version:
            raise _error(409, 'stale_version', 'The contract changed since it was read. Reload and try again.',
                         current_version=version)

    def _tp_bump(self, contract, version):
        contract.sudo().with_context(**{WORKFLOW_CONTEXT: True}).write({'aggregate_version': version + 1})
        return version + 1

    def _tp_fingerprint(self, action, object_ref, payload):
        secret = self.env['ir.config_parameter'].sudo().get_str('database.secret')
        message = _canonical({'action': action, 'object': object_ref, 'payload': payload})
        return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()

    def _tp_replay(self, action, key, object_ref, fingerprint):
        # Runs before the version check: a retry of a request that already
        # succeeded must get its result, not a false stale_version.
        record = self.env['tp.contract.idempotency'].sudo().search([
            ('user_id', '=', self.env.uid), ('action', '=', action), ('key', '=', key),
        ], limit=1)
        if not record:
            return None
        if record.object_ref != object_ref or not hmac.compare_digest(record.fingerprint, fingerprint):
            raise _error(409, 'idempotency_conflict', 'This Idempotency-Key was already used for a different request.')
        contract = self._tp_find_contract(record.result_contract_id.id)
        self._tp_require(contract, [capability for capability in (record.required_capabilities or '').split(',') if capability])
        return self._tp_result(contract, record.result_revision_id, record.result_submission_id, replayed=True)

    def _tp_claim(self, action, key, object_ref, fingerprint, project):
        try:
            with self.env.cr.savepoint():
                return self.env['tp.contract.idempotency'].sudo().create({
                    'user_id': self.env.uid, 'action': action, 'key': key, 'object_ref': object_ref,
                    'fingerprint': fingerprint, 'project_id': project.id, 'company_id': project.sudo().company_id.id,
                })
        except pg_errors.UniqueViolation as error:
            # Another transaction holds the same key; retrying the request replays its result.
            message = 'A concurrent request uses the same Idempotency-Key.'
            raise ConcurrencyError(message) from error

    def _tp_result(self, contract, revision, submission, *, replayed):
        Submission = self.env['tp.contract.submission']
        return {
            'contract': contract.with_env(self.env),
            'revision': revision.with_env(self.env),
            'submission': submission.with_env(self.env) if submission else Submission,
            'replayed': replayed,
        }

    # History

    def _tp_audit(self, context, contract, revision, *, state_before, state_after, version_before, version_after,
                  action=None, submission=None, reason=None):
        return self.env['tp.contract.audit'].sudo().create({
            'event_id': str(uuid.uuid4()),
            'action': action or context['action'],
            'actor_id': self.env.uid,
            'acted_at': fields.Datetime.now(),
            'request_id': context.get('request_id'),
            'contract_id': contract.id,
            'revision_id': revision.id,
            'submission_id': submission.id if submission else False,
            'department_id': contract.sudo().department_id.id,
            'state_before': state_before,
            'state_after': state_after,
            'version_before': version_before,
            'version_after': version_after,
            'payload_sha256': submission.payload_sha256 if submission else False,
            'reason': reason,
        })

    def _tp_notify(self, audit, recipients):
        self.env['tp.contract.outbox'].sudo().create([{
            'event_id': audit.event_id, 'audit_id': audit.id, 'event_type': audit.action, 'recipient_id': user.id,
            'contract_id': audit.contract_id.id, 'revision_id': audit.revision_id.id,
        } for user in recipients])

    # Validation helpers

    def _tp_currency(self, code):
        currency = self.env['res.currency'].search([('name', '=', code.upper())], limit=1)
        if not currency:
            raise _error(422, 'unknown_currency', 'The currency is unknown or inactive.', field='currency')
        return currency

    def _tp_partner(self, partner_id, project):
        if not partner_id:
            return self.env['res.partner']
        partner = self.env['res.partner'].search([('id', '=', partner_id)], limit=1)
        if not partner or partner.company_id not in (project.sudo().company_id, self.env['res.company']):
            raise _error(422, 'unknown_partner', 'The counterparty is unknown or belongs to another company.', field='partner_id')
        return partner

    def _tp_check_code(self, company, code, contract=None):
        domain = Domain('company_id', '=', company.id) & Domain('code', '=', code.upper())
        if contract:
            domain &= Domain('id', '!=', contract.id)
        if self.env['tp.contract'].sudo().with_context(active_test=False).search_count(domain, limit=1):
            raise _error(409, 'duplicate_code', 'Another contract of the company already uses this code.', field='code')

    def _tp_touches_money(self, revision, lines):
        if any('amount' in line for line in lines):
            return True
        kept = [line['scope_key'] for line in lines]
        return bool(self.env['tp.contract.line.amount'].sudo().search_count([
            ('revision_id', '=', revision.id), ('line_id.scope_key', 'not in', kept),
        ], limit=1))

    # Line and amount writes

    def _tp_apply_lines(self, revision, lines):
        revision = revision.sudo()
        Line = self.env['tp.contract.line'].sudo().with_context(**{WORKFLOW_CONTEXT: True})
        currency = revision.contract_id.currency_id
        wanted = {line['scope_key'] for line in lines}
        revision.line_ids.filtered(lambda line: line.scope_key not in wanted).unlink()
        existing = {line.scope_key: line for line in revision.line_ids}
        previous = {line.scope_key: line for line in revision.previous_revision_id.line_ids}
        for index, item in enumerate(lines):
            name = _require_text(item['name'], f'lines[{index}].name', 'name_required')
            vals = {'name': name, 'sequence': (index + 1) * 10}
            line = existing.get(item['scope_key'])
            if line:
                line.write(vals)
            else:
                prior = previous.get(item['scope_key'])
                kind = 'original' if revision.revision_kind == 'original' else ('amended' if prior else 'added')
                line = Line.create(vals | {
                    'revision_id': revision.id, 'scope_key': item['scope_key'], 'change_kind': kind,
                    'previous_line_id': prior.id if prior else False,
                })
            if 'amount' in item:
                self._tp_set_amount(line, item['amount'], currency, f'lines[{index}].amount')
        if revision.revision_kind != 'original':
            self._tp_refresh_change_kinds(revision)

    def _tp_set_amount(self, line, amount, currency, field):
        Amount = self.env['tp.contract.line.amount'].sudo().with_context(**{WORKFLOW_CONTEXT: True})
        record = Amount.search([('line_id', '=', line.id)], limit=1)
        if amount is None:
            record.unlink()
            return
        value = amount['value']
        if amount['state'] == 'confirmed' and value is None:
            raise _error(422, 'amount_value_required', 'A confirmed amount needs a value.', field=field)
        if amount['state'] == 'unconfirmed' and value is not None:
            raise _error(422, 'amount_value_not_allowed', 'An unconfirmed amount carries no value; send null.', field=field)
        if value is not None:
            if value < 0:
                raise _error(422, 'amount_negative', 'Snapshot line amounts cannot be negative.', field=field)
            if value.adjusted() + 1 + currency.decimal_places > MAX_AMOUNT_DIGITS:
                raise _error(422, 'amount_too_large', 'The amount has too many digits.', field=field)
            if value != value.quantize(Decimal(1).scaleb(-currency.decimal_places)):
                raise _error(422, 'amount_precision', f'{currency.name} amounts allow {currency.decimal_places} decimal places.', field=field)
        vals = {
            'amount_state': amount['state'],
            'amount': float(value) if value is not None else 0,
            'tax_basis': amount['tax_basis'],
        }
        if record:
            record.write(vals)
        else:
            Amount.create(vals | {'line_id': line.id})

    def _tp_refresh_change_kinds(self, revision):
        # Carried-over lines are compared with the previous revision on the server
        # so a client cannot label an amended line as unchanged.
        currency = revision.contract_id.currency_id
        previous = {line.scope_key: line for line in revision.previous_revision_id.line_ids}
        amounts = {
            amount.line_id.id: amount
            for amount in self.env['tp.contract.line.amount'].sudo().search([
                ('revision_id', 'in', (revision | revision.previous_revision_id).ids),
            ])
        }
        for line in revision.line_ids:
            prior = previous.get(line.scope_key)
            if not prior:
                kind, prior_id = 'added', False
            else:
                same = line.name == prior.name and _amount_key(amounts.get(line.id), currency) == _amount_key(amounts.get(prior.id), currency)
                kind, prior_id = ('unchanged' if same else 'amended'), prior.id
            if (line.change_kind, line.previous_line_id.id) != (kind, prior_id):
                line.write({'change_kind': kind, 'previous_line_id': prior_id})

    # Snapshot

    def _tp_snapshot(self, revision):
        revision = revision.sudo()
        contract = revision.contract_id
        currency = contract.currency_id
        amounts = {
            amount.line_id.id: amount
            for amount in self.env['tp.contract.line.amount'].sudo().search([('revision_id', '=', revision.id)])
        }
        documents = self.env['tp.contract.document'].sudo().search([('revision_id', '=', revision.id)])
        checksums = {
            attachment.res_id: attachment.checksum
            for attachment in self.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'tp.contract.document'), ('res_field', '=', 'file'), ('res_id', 'in', documents.ids),
            ])
        }

        def document_entry(document):
            return {
                'id': document.id, 'name': document.name, 'kind': document.document_kind,
                'file_name': document.file_name or None, 'sha1': checksums.get(document.id),
            }

        metadata = {
            'contract': {
                'id': contract.id, 'code': contract.code, 'name': contract.name, 'contract_type': contract.contract_type,
                'partner_id': contract.partner_id.id or None, 'partner_name': contract.partner_id.display_name or None,
                'currency': currency.name, 'project_id': contract.project_id.id, 'department_id': contract.department_id.id,
            },
            'revision': {
                'id': revision.id, 'sequence': revision.sequence, 'kind': revision.revision_kind, 'name': revision.name,
                'reference': revision.reference or None, 'previous_revision_id': revision.previous_revision_id.id or None,
            },
            'lines': [{
                'scope_key': line.scope_key, 'name': line.name, 'sequence': line.sequence, 'change_kind': line.change_kind,
                'previous_line_id': line.previous_line_id.id or None, 'work_item_id': line.work_item_id.id or None,
            } for line in revision.line_ids],
            'documents': [document_entry(document) for document in documents if document.confidentiality == 'general'],
        }
        summary = revision._amount_summary()
        financial = {
            'currency': currency.name,
            'lines': {
                line.scope_key: dict(zip(('state', 'value', 'tax_basis'), _amount_key(amounts.get(line.id), currency) or (None, None, None)))
                for line in revision.line_ids
            },
            'total': {
                'value': None if summary['value'] is None else format(summary['value'], f'.{currency.decimal_places}f'),
                'status': summary['status'], 'tax_basis': summary['tax_basis'],
            },
            'documents': [document_entry(document) for document in documents if document.confidentiality == 'financial'],
        }
        return metadata, financial

    def _tp_submission_problems(self, revision):
        revision = revision.sudo()
        if not revision.line_ids:
            return ['no_lines']
        status = revision._amount_summary()['status']
        if status == 'incomplete':
            return ['amounts_not_confirmed']
        if status == 'mixed_basis':
            return ['tax_basis_mixed']
        return []

    def _tp_eligible_reviewers(self, contract):
        """Users who may receive a review: active assignment, review and financial.read grants."""
        contract = contract.sudo()
        if not contract.department_id:
            return self.env['res.users']
        grants = self.env['tp.project.grant'].sudo().search([
            ('project_id', '=', contract.project_id.id), ('department_id', '=', contract.department_id.id),
            ('capability', '=', 'contract_review_commercial'),
        ])
        # _tp_capabilities rechecks assignment, validity dates and financial.read.
        return grants.user_id.filtered(
            lambda user: user.active and self._tp_capabilities(contract.project_id, contract.department_id, user) >= REVIEWER_CAPABILITIES,
        )

    def _tp_available_actions(self, contract, revision=None):
        """Actions the current user may try now. UI hints only; each action rechecks on the server."""
        record = contract.sudo()
        held = self._tp_capabilities(record.project_id, record.department_id)
        actions = []
        if revision is None:
            open_revision = record.revision_ids.filtered(lambda rev: rev.review_state in OPEN_STATES)
            if 'contract_draft_edit' in held and record.revision_ids and not open_revision:
                actions.append('create_amendment')
            return actions, held
        state = revision.sudo().review_state
        if state == 'draft':
            if 'contract_draft_edit' in held:
                actions.append('edit_draft')
            if {'contract_submit', 'financial_read'} <= held:
                actions.append('submit_review')
        elif state == 'in_review':
            pending = revision.sudo().submission_ids.filtered(lambda submission: submission.outcome == 'pending')
            if held >= REVIEWER_CAPABILITIES and pending.reviewer_id == self.env.user:
                actions.append('return_review')
        elif state == 'returned' and 'contract_draft_edit' in held:
            actions.append('begin_rework')
        return actions, held

    # Actions

    def _tp_create_contract(self, project, data, context):
        lines = data['lines']
        capabilities = ACTION_CAPABILITIES['create_contract'] + (FINANCIAL_EDIT if any('amount' in line for line in lines) else ())
        department = project.sudo().tp_department_id
        if not department:
            raise _error(422, 'scope_incomplete', 'The project has no lead department to scope its contracts.')
        self._tp_require(project, capabilities, department)
        code = _require_text(data.get('code'), 'code', 'code_required')
        name = _require_text(data.get('name'), 'name', 'name_required')
        currency = self._tp_currency(data['currency'])
        partner = self._tp_partner(data.get('partner_id'), project)
        company = project.sudo().company_id
        self._tp_check_code(company, code)
        workflow = {WORKFLOW_CONTEXT: True}
        contract = self.env['tp.contract'].sudo().with_context(**workflow).create({
            'code': code, 'name': name, 'project_id': project.id, 'department_id': department.id,
            'partner_id': partner.id, 'contract_type': data['contract_type'], 'currency_id': currency.id,
        })
        revision = self.env['tp.contract.revision'].sudo().with_context(**workflow).create({
            'contract_id': contract.id, 'sequence': 0, 'revision_kind': 'original',
            'name': data['revision'].get('name') or name, 'reference': data['revision'].get('reference'),
        })
        self._tp_apply_lines(revision, lines)
        self._tp_audit(context, contract, revision, state_before=None, state_after='draft',
                       version_before=None, version_after=contract.aggregate_version)
        return {'contract': contract, 'revision': revision, 'capabilities': capabilities}

    def _tp_create_amendment(self, contract, data, context):
        version = self._tp_lock(contract)
        capabilities = ACTION_CAPABILITIES['create_amendment']
        self._tp_guard(contract, version, data['expected_version'], capabilities)
        record = contract.sudo()
        if record.revision_ids.filtered(lambda revision: revision.review_state in OPEN_STATES):
            raise _error(409, 'invalid_state', 'The contract already has a revision in progress.')
        previous = record.revision_ids.filtered(lambda revision: revision.review_state != 'cancelled').sorted('sequence')[-1:]
        if not previous:
            raise _error(409, 'invalid_state', 'There is no revision to amend.')
        name = _require_text(data.get('name'), 'name', 'name_required')
        workflow = {WORKFLOW_CONTEXT: True}
        revision = self.env['tp.contract.revision'].sudo().with_context(**workflow).create({
            'contract_id': record.id, 'sequence': max(record.revision_ids.mapped('sequence')) + 1,
            'revision_kind': 'amendment', 'name': name, 'reference': data.get('reference'),
            'previous_revision_id': previous.id,
        })
        # Carry the previous scope over unchanged; amounts are copied by the
        # system and stay behind the financial.read domain.
        Line = self.env['tp.contract.line'].sudo().with_context(**workflow)
        Amount = self.env['tp.contract.line.amount'].sudo().with_context(**workflow)
        amounts = {amount.line_id.id: amount for amount in Amount.search([('revision_id', '=', previous.id)])}
        for line in previous.line_ids:
            copy = Line.create({
                'revision_id': revision.id, 'scope_key': line.scope_key, 'name': line.name, 'sequence': line.sequence,
                'work_item_id': line.work_item_id.id, 'change_kind': 'unchanged', 'previous_line_id': line.id,
            })
            if amount := amounts.get(line.id):
                Amount.create({
                    'line_id': copy.id, 'amount_state': amount.amount_state, 'amount': amount.amount,
                    'tax_basis': amount.tax_basis,
                })
        new_version = self._tp_bump(record, version)
        self._tp_audit(context, record, revision, state_before=None, state_after='draft',
                       version_before=version, version_after=new_version)
        return {'contract': record, 'revision': revision, 'capabilities': capabilities}

    def _tp_edit_draft(self, contract, revision, data, context):
        version = self._tp_lock(contract)
        record, rev = contract.sudo(), revision.sudo()
        lines = data.get('lines')
        capabilities = ACTION_CAPABILITIES['edit_draft']
        # A currency change re-denominates every amount, so it counts as a money edit.
        if 'currency' in data.get('contract', {}) or (lines is not None and self._tp_touches_money(rev, lines)):
            capabilities += FINANCIAL_EDIT
        self._tp_guard(contract, version, data['expected_version'], capabilities)
        if rev.review_state != 'draft':
            raise _error(409, 'invalid_state', 'Only a draft revision can be edited.', review_state=rev.review_state)
        workflow = {WORKFLOW_CONTEXT: True}
        header = data.get('contract')
        if header:
            if rev.revision_kind != 'original':
                raise _error(422, 'header_locked', 'The contract header changes only with the original draft.', field='contract')
            vals = {}
            if 'code' in header:
                vals['code'] = _require_text(header['code'], 'contract.code', 'code_required')
                self._tp_check_code(record.company_id, vals['code'], record)
            if 'name' in header:
                vals['name'] = _require_text(header['name'], 'contract.name', 'name_required')
            if 'contract_type' in header:
                vals['contract_type'] = header['contract_type']
            if 'partner_id' in header:
                vals['partner_id'] = self._tp_partner(header['partner_id'], record.project_id).id
            if 'currency' in header:
                vals['currency_id'] = self._tp_currency(header['currency']).id
            record.with_context(**workflow).write(vals)
        if data.get('revision'):
            vals = dict(data['revision'])
            if 'name' in vals:
                vals['name'] = _require_text(vals['name'], 'revision.name', 'name_required')
            rev.with_context(**workflow).write(vals)
        if lines is not None:
            self._tp_apply_lines(rev, lines)
        new_version = self._tp_bump(record, version)
        self._tp_audit(context, record, rev, state_before='draft', state_after='draft',
                       version_before=version, version_after=new_version)
        return {'contract': record, 'revision': rev, 'capabilities': capabilities}

    def _tp_submit_review(self, contract, revision, data, context):
        version = self._tp_lock(contract)
        capabilities = ACTION_CAPABILITIES['submit_review']
        self._tp_guard(contract, version, data['expected_version'], capabilities)
        record, rev = contract.sudo(), revision.sudo()
        if rev.review_state != 'draft':
            raise _error(409, 'invalid_state', 'Only a draft revision can be submitted.', review_state=rev.review_state)
        previous = rev.submission_ids.sorted('sequence')[-1:]
        if previous and not data['fix_summary']:
            raise _error(422, 'fix_summary_required', 'Describe what was fixed since the returned submission.', field='fix_summary')
        reviewer = self.env['res.users'].sudo().browse(data['reviewer_id']).exists()
        if not reviewer or reviewer not in self._tp_eligible_reviewers(record):
            raise _error(422, 'reviewer_ineligible', 'The selected reviewer cannot review this contract.', field='reviewer_id')
        problems = self._tp_submission_problems(rev)
        if problems:
            raise _error(422, 'submission_incomplete', 'The draft is not complete enough to submit.', problems=problems)

        metadata, financial = self._tp_snapshot(rev)
        metadata_sha256 = _sha256(_canonical(metadata))
        salt = secrets.token_hex(16)
        financial_sha256 = _sha256(salt.encode() + _canonical(financial))
        workflow = {WORKFLOW_CONTEXT: True}
        submission = self.env['tp.contract.submission'].sudo().with_context(**workflow).create({
            'revision_id': rev.id, 'sequence': (previous.sequence or 0) + 1,
            'previous_submission_id': previous.id, 'submitted_by_id': self.env.uid,
            'submitted_at': fields.Datetime.now(), 'reviewer_id': reviewer.id, 'contract_version': version,
            'fix_summary': data['fix_summary'], 'metadata_snapshot': metadata, 'metadata_sha256': metadata_sha256,
            'payload_sha256': _sha256(f'{metadata_sha256}:{financial_sha256}'.encode()),
        })
        self.env['tp.contract.submission.amount'].sudo().create({
            'submission_id': submission.id, 'financial_snapshot': financial, 'salt': salt,
            'financial_sha256': financial_sha256,
        })
        rev.with_context(**workflow).write({'review_state': 'in_review'})
        new_version = self._tp_bump(record, version)
        audit = self._tp_audit(
            context, record, rev, action='resubmit_review' if previous else 'submit_review',
            state_before='draft', state_after='in_review', version_before=version, version_after=new_version,
            submission=submission, reason=data['fix_summary'],
        )
        self._tp_notify(audit, reviewer)
        return {'contract': record, 'revision': rev, 'submission': submission, 'capabilities': capabilities}

    def _tp_return_review(self, contract, revision, data, context):
        version = self._tp_lock(contract)
        capabilities = ACTION_CAPABILITIES['return_review']
        self._tp_guard(contract, version, data['expected_version'], capabilities)
        record, rev = contract.sudo(), revision.sudo()
        if rev.review_state != 'in_review':
            raise _error(409, 'invalid_state', 'Only a revision under review can be returned.', review_state=rev.review_state)
        pending = rev.submission_ids.filtered(lambda submission: submission.outcome == 'pending')
        if pending.reviewer_id != self.env.user:
            raise _error(403, 'not_assigned_reviewer', 'Only the reviewer assigned to the submission can return it.')
        reason = _require_text(data['reason'], 'reason', 'reason_required')
        scope_keys = {line['scope_key'] for line in pending.metadata_snapshot['lines']}
        for index, issue in enumerate(data['issues']):
            _require_text(issue['note'], f'issues[{index}].note', 'issue_note_required')
            if issue['scope_key'] and issue['scope_key'] not in scope_keys:
                raise _error(422, 'unknown_scope_key', 'The issue refers to a scope key outside the submission.',
                             field=f'issues[{index}].scope_key')
        workflow = {WORKFLOW_CONTEXT: True}
        pending.with_context(**workflow).write({
            'outcome': 'returned', 'returned_by_id': self.env.uid, 'returned_at': fields.Datetime.now(),
            'return_reason': reason, 'return_issues': data['issues'],
        })
        rev.with_context(**workflow).write({'review_state': 'returned'})
        new_version = self._tp_bump(record, version)
        audit = self._tp_audit(context, record, rev, state_before='in_review', state_after='returned',
                               version_before=version, version_after=new_version, submission=pending, reason=reason)
        self._tp_notify(audit, pending.submitted_by_id)
        return {'contract': record, 'revision': rev, 'submission': pending, 'capabilities': capabilities}

    def _tp_begin_rework(self, contract, revision, data, context):
        version = self._tp_lock(contract)
        capabilities = ACTION_CAPABILITIES['begin_rework']
        self._tp_guard(contract, version, data['expected_version'], capabilities)
        record, rev = contract.sudo(), revision.sudo()
        if rev.review_state != 'returned':
            raise _error(409, 'invalid_state', 'Rework starts only from a returned revision.', review_state=rev.review_state)
        reason = _require_text(data['reason'], 'reason', 'reason_required')
        returned = rev.submission_ids.sorted('sequence')[-1:]
        workflow = {WORKFLOW_CONTEXT: True}
        returned.with_context(**workflow).write({
            'rework_started_by_id': self.env.uid, 'rework_started_at': fields.Datetime.now(), 'rework_reason': reason,
        })
        rev.with_context(**workflow).write({'review_state': 'draft'})
        new_version = self._tp_bump(record, version)
        self._tp_audit(context, record, rev, state_before='returned', state_after='draft',
                       version_before=version, version_after=new_version, submission=returned, reason=reason)
        return {'contract': record, 'revision': rev, 'submission': returned, 'capabilities': capabilities}
