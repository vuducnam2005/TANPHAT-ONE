from datetime import date

from werkzeug.exceptions import NotFound

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.fields import Domain
from odoo.http import Controller, request, route
from odoo.tools import float_repr

from .projects import _require_reader
from odoo.addons.tp_api.services.response import api_response


def _invalid(message):
    raise ValidationError(message)


def _page_params(params):
    try:
        limit = int(params.get('limit', 20))
        offset = int(params.get('offset', 0))
    except (ValueError, TypeError) as error:
        raise ValidationError(request.env._('Limit and offset must be integers.')) from error
    if not 1 <= limit <= 100 or not 0 <= offset <= 10000:
        _invalid(request.env._('Limit must be 1-100 and offset must be 0-10000.'))
    return limit, offset


def _parse_as_of(value):
    if value is None:
        return fields.Date.context_today(request.env.user)
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(request.env._('as_of must be a date in YYYY-MM-DD format.')) from error


def _iso_datetime(value):
    return value.isoformat(timespec='seconds') + 'Z' if value else None


def _iso_date(value):
    return value.isoformat() if value else None


def _ref(record):
    return {'id': record.id, 'name': record.display_name} if record else None


def _money(value, status, tax_basis, currency):
    """Serialize money as a decimal string; ``None`` means not confirmed, never zero."""
    return {
        'value': None if value is None else format(value, f'.{currency.decimal_places}f'),
        'currency': currency.name,
        'status': status,
        'tax_basis': tax_basis,
    }


def _amount_money(amount, currency):
    if not amount:
        return _money(None, 'unconfirmed', 'unknown', currency)
    if amount.amount_state != 'confirmed':
        return _money(None, 'unconfirmed', amount.tax_basis, currency)
    return {
        'value': float_repr(currency.round(amount.amount), currency.decimal_places),
        'currency': currency.name,
        'status': 'confirmed',
        'tax_basis': amount.tax_basis,
    }


def _summary_money(summary):
    return _money(summary['value'], summary['status'], summary['tax_basis'], summary['currency'])


def _find_contract(contract_id):
    # Records outside the caller's scope are indistinguishable from missing ones.
    contract = request.env['tp.contract'].search([('id', '=', contract_id)], limit=1)
    if not contract:
        raise NotFound(request.env._('The requested contract was not found.'))
    return contract


def _revision_status(revision):
    return {
        'id': revision.id,
        'sequence': revision.sequence,
        'kind': revision.revision_kind,
        'name': revision.name,
        'review_state': revision.review_state,
        'signature_status': revision.signature_status,
        'effectivity_status': revision.effectivity_status,
    }


def _contract_summary(contract):
    revisions = contract.revision_ids
    return {
        'id': contract.id,
        'code': contract.code,
        'name': contract.name,
        'contract_type': contract.contract_type,
        'lifecycle_state': contract.lifecycle_state,
        'legacy_unverified': contract.legacy_unverified,
        'active': contract.active,
        'project': {'id': contract.project_id.id, 'code': contract.project_id.tp_code, 'name': contract.project_id.name},
        'company': {'id': contract.company_id.id, 'name': contract.company_id.name},
        'counterparty': _ref(contract.partner_id),
        'currency': contract.currency_id.name,
        'revision_count': len(revisions),
        'latest_revision': _revision_status(revisions[-1]) if revisions else None,
        'updated_at': _iso_datetime(contract.write_date),
    }


def _approval_dto(reference, financial_read):
    data = {
        'id': reference.id,
        'purpose': reference.purpose,
        'reference_kind': reference.reference_kind,
        'base_reference': reference.base_reference or None,
        'source_url': reference.source_url or None,
        'provenance': reference.provenance or None,
        'decision': reference.decision,
        'decided_by_name': reference.decided_by_name or None,
        'decided_at': _iso_datetime(reference.decided_at),
        'decision_reason': reference.decision_reason or None,
        'verification_state': reference.verification_state,
        'verified_by': _ref(reference.verified_by_id),
        'verified_at': _iso_datetime(reference.verified_at),
        'authority_status': reference.authority_status,
        'authority_source': reference.authority_source or None,
        'recorded_by': _ref(reference.recorded_by_id),
        'recorded_at': _iso_datetime(reference.recorded_at),
        'previous_reference_id': reference.previous_reference_id.id or None,
        'evidence_sha256': reference.evidence_sha256 or None,
        'submitted_document_sha256': reference.submitted_document_sha256 or None,
        'verified_result': reference._is_verified_result(),
    }
    if financial_read:
        amount = request.env['tp.approval.reference.amount'].search([('reference_id', '=', reference.id)], limit=1)
        data['approved_amount'] = _amount_money(amount, reference.contract_id.currency_id) if amount else None
    return data


def _revision_dto(revision, financial_read):
    return _revision_status(revision) | {
        'reference': revision.reference or None,
        'previous_revision_id': revision.previous_revision_id.id or None,
        'signed_date': _iso_date(revision.signed_date),
        'effective_date': _iso_date(revision.effective_date),
        'recorded_at': _iso_datetime(revision.recorded_at),
        'signature_authority_status': revision.signature_authority_status,
        'legacy_unverified': revision.legacy_unverified,
        'line_count': len(revision.line_ids),
        'base_references': [_approval_dto(reference, financial_read) for reference in revision.approval_reference_ids],
    }


def _document_dto(document):
    return {
        'id': document.id,
        'name': document.name,
        'kind': document.document_kind,
        'confidentiality': document.confidentiality,
        'revision_id': document.revision_id.id or None,
        'file_name': document.file_name or None,
        'has_file': bool(document.file),
    }


def _line_dto(line, amounts, currency):
    data = {
        'id': line.id,
        'sequence': line.sequence,
        'scope_key': line.scope_key,
        'name': line.name,
        'work_item': {'id': line.work_item_id.id, 'code': line.work_item_id.code, 'name': line.work_item_id.name}
        if line.work_item_id else None,
        'change_kind': line.change_kind,
        'previous_line_id': line.previous_line_id.id or None,
    }
    if amounts is not None:
        data['amount'] = _amount_money(amounts.get(line.id), currency)
    return data


class TpContracts(Controller):
    @route('/api/v1/contracts', type='http', auth='user', methods=['GET'], readonly=True)
    def contracts(self, **params):
        _require_reader()
        if set(params) - {'limit', 'offset', 'q', 'project_id'}:
            _invalid(request.env._('Unsupported query parameter.'))
        limit, offset = _page_params(params)
        domain = Domain.TRUE
        if 'project_id' in params:
            try:
                project_id = int(params['project_id'])
            except ValueError as error:
                raise ValidationError(request.env._('project_id must be an integer.')) from error
            domain &= Domain('project_id', '=', project_id)
        query = params.get('q', '').strip()
        if len(query) > 100:
            _invalid(request.env._('The search query is too long.'))
        if query:
            domain &= Domain('code', 'ilike', query) | Domain('name', 'ilike', query)
        contracts = request.env['tp.contract'].search(domain, limit=limit + 1, offset=offset, order='code, id')
        return api_response([_contract_summary(contract) for contract in contracts[:limit]], pagination={
            'limit': limit, 'offset': offset, 'has_more': len(contracts) > limit,
        })

    @route('/api/v1/contracts/<int:contract_id>', type='http', auth='user', methods=['GET'], readonly=True)
    def contract(self, contract_id, **params):
        _require_reader()
        if set(params) - {'as_of'}:
            _invalid(request.env._('Unsupported query parameter.'))
        as_of = _parse_as_of(params.get('as_of'))
        contract = _find_contract(contract_id)
        financial_read = contract.project_id.tp_financial_read_granted
        effective, warnings = contract._effective_revision(as_of)
        snapshot = {
            'as_of': as_of.isoformat(),
            'known_at': _iso_datetime(fields.Datetime.now()),
            'basis': 'recorded_effectivity',
            'revision_id': effective.id or None,
            'warnings': warnings,
        }
        if financial_read:
            snapshot['total'] = _summary_money(effective._amount_summary()) if effective else None
        documents = request.env['tp.contract.document'].search([('contract_id', '=', contract.id)])
        return api_response(_contract_summary(contract) | {
            'permissions': {'financial_read': financial_read},
            'effective_snapshot': snapshot,
            'revisions': [_revision_dto(revision, financial_read) for revision in contract.revision_ids],
            'documents': [_document_dto(document) for document in documents],
        })

    @route('/api/v1/contracts/<int:contract_id>/revisions/<int:revision_id>', type='http', auth='user', methods=['GET'], readonly=True)
    def revision(self, contract_id, revision_id, **params):
        _require_reader()
        if params:
            _invalid(request.env._('Unsupported query parameter.'))
        contract = _find_contract(contract_id)
        revision = request.env['tp.contract.revision'].search([
            ('id', '=', revision_id), ('contract_id', '=', contract.id),
        ], limit=1)
        if not revision:
            raise NotFound(request.env._('The requested revision was not found.'))
        financial_read = contract.project_id.tp_financial_read_granted
        amounts = None
        if financial_read:
            amounts = {
                amount.line_id.id: amount
                for amount in request.env['tp.contract.line.amount'].search([('revision_id', '=', revision.id)])
            }
        data = _revision_dto(revision, financial_read) | {
            'contract_id': contract.id,
            'permissions': {'financial_read': financial_read},
            'lines': [_line_dto(line, amounts, contract.currency_id) for line in revision.line_ids],
        }
        if financial_read:
            data['total'] = _summary_money(revision._amount_summary())
        return api_response(data)

    @route('/api/v1/contracts/<int:contract_id>/documents/<int:document_id>/content', type='http', auth='user', methods=['GET'], readonly=True)
    def document_content(self, contract_id, document_id, **params):
        _require_reader()
        if params:
            _invalid(request.env._('Unsupported query parameter.'))
        contract = _find_contract(contract_id)
        document = request.env['tp.contract.document'].search([
            ('id', '=', document_id), ('contract_id', '=', contract.id),
        ], limit=1)
        if not document or not document.file:
            raise NotFound(request.env._('The requested document was not found.'))
        # The field is read with the caller's rights; no sudo bypass.
        stream = request.env['ir.binary']._get_stream_from(
            document, 'file', filename=document.file_name or f'contract-document-{document.id}',
        )
        response = stream.get_response(as_attachment=True)
        response.headers['Cache-Control'] = 'no-store'
        return response
