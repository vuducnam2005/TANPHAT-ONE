import hashlib

from odoo import Command, fields
from odoo.tests.common import new_test_user
from odoo.tools import BinaryBytes

from odoo.addons.base.tests.common import BaseCommon


class TpContractCommon(BaseCommon):
    """Synthetic contracts (amounts in million VND) for read and access tests."""

    # Run test methods as the superuser; every access check names its user.
    _test_user_groups = ()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.currency = cls.env.ref('base.VND')
        cls.currency.active = True
        cls.reader = new_test_user(cls.env, login='tp_ctr_reader', groups='tp_core.group_user', company_id=cls.company.id)
        cls.finance_a = new_test_user(cls.env, login='tp_ctr_finance_a', groups='tp_core.group_user', company_id=cls.company.id)
        cls.finance_b = new_test_user(cls.env, login='tp_ctr_finance_b', groups='tp_core.group_user', company_id=cls.company.id)
        cls.outsider = new_test_user(cls.env, login='tp_ctr_outsider', groups='tp_core.group_user', company_id=cls.company.id)
        cls.manager = new_test_user(cls.env, login='tp_ctr_manager', groups='tp_core.group_manager', company_id=cls.company.id)
        cls.project_a = cls._project('CTR-TEST-A')
        cls.project_b = cls._project('CTR-TEST-B')
        for project, users in ((cls.project_a, cls.reader | cls.finance_a | cls.finance_b), (cls.project_b, cls.finance_b)):
            cls.env['tp.project.assignment'].create([{'project_id': project.id, 'user_id': user.id} for user in users])
        cls.grant_a = cls._grant(cls.project_a, cls.finance_a)
        cls.grant_b = cls._grant(cls.project_b, cls.finance_b)

        cls.contract_a = cls._contract(cls.project_a, 'HD-A')
        cls.original = cls._revision(cls.contract_a, 0, signed='2026-01-05', effective='2026-01-10')
        cls.line_x = cls._line(cls.original, 'X', 'Survey package', change_kind='original', amount=60)
        cls.line_y = cls._line(cls.original, 'Y', 'Design package', change_kind='original', amount=40)
        cls.amendment = cls._revision(
            cls.contract_a, 1, previous=cls.original, signed='2026-10-10', effective='2026-11-01', kind='amendment',
        )
        cls.line_x2 = cls._line(cls.amendment, 'X', 'Survey package', change_kind='amended', previous=cls.line_x, amount=70)
        cls.line_y2 = cls._line(cls.amendment, 'Y', 'Design package', change_kind='unchanged', previous=cls.line_y, amount=40)
        cls.approval = cls.env['tp.approval.reference'].create({
            'revision_id': cls.amendment.id, 'reference_kind': 'manual', 'provenance': 'Synthetic test screenshot',
            'decision': 'approved', 'decided_by_name': 'BASE approver (synthetic)',
            'decided_at': fields.Datetime.to_datetime('2026-10-09 03:00:00'),
            'evidence_sha256': hashlib.sha256(b'synthetic evidence').hexdigest(),
        })
        cls.approval_amount = cls.env['tp.approval.reference.amount'].create({
            'reference_id': cls.approval.id, 'amount_state': 'confirmed', 'amount': 110,
        })
        cls.financial_doc = cls.env['tp.contract.document'].create({
            'contract_id': cls.contract_a.id, 'revision_id': cls.amendment.id, 'name': 'Signed amendment',
            'document_kind': 'amendment', 'file': BinaryBytes(b'synthetic signed amendment'),
            'file_name': 'amendment.pdf',
        })
        cls.general_doc = cls.env['tp.contract.document'].create({
            'contract_id': cls.contract_a.id, 'name': 'Technical scope', 'document_kind': 'technical_scope',
            'confidentiality': 'general', 'file': BinaryBytes(b'synthetic scope'), 'file_name': 'scope.txt',
        })

        cls.contract_b = cls._contract(cls.project_b, 'HD-B')
        cls.revision_b = cls._revision(cls.contract_b, 0, signed='2026-02-01', effective='2026-02-01')
        cls.line_b = cls._line(cls.revision_b, 'B1', 'Supervision', change_kind='original', amount=25)

    @classmethod
    def _project(cls, code):
        return cls.env['project.project'].create({
            'name': f'Project {code}', 'company_id': cls.company.id, 'tp_managed': True, 'tp_code': code,
            'privacy_visibility': 'employees',
        })

    @classmethod
    def _grant(cls, project, user):
        return cls.env['tp.project.grant'].create({
            'project_id': project.id, 'user_id': user.id, 'capability': 'financial_read', 'reason': 'Synthetic test grant',
        })

    @classmethod
    def _contract(cls, project, code):
        return cls.env['tp.contract'].create({
            'code': code, 'name': f'Contract {code}', 'project_id': project.id, 'contract_type': 'owner',
            'currency_id': cls.currency.id,
        })

    @classmethod
    def _revision(cls, contract, sequence, *, previous=None, signed=None, effective=None, kind='original'):
        vals = {
            'contract_id': contract.id, 'sequence': sequence, 'revision_kind': kind,
            'name': 'Original' if kind == 'original' else f'Revision {sequence}',
            'previous_revision_id': previous.id if previous else False, 'review_state': 'review_complete',
        }
        if signed:
            vals.update(signature_status='signed_recorded', signed_date=signed)
        if effective:
            vals.update(effectivity_status='effective_recorded', effective_date=effective)
        return cls.env['tp.contract.revision'].create(vals)

    @classmethod
    def _line(cls, revision, key, name, *, change_kind, previous=None, amount=None, state='confirmed'):
        line = cls.env['tp.contract.line'].create({
            'revision_id': revision.id, 'scope_key': key, 'name': name, 'change_kind': change_kind,
            'previous_line_id': previous.id if previous else False,
        })
        cls.env['tp.contract.line.amount'].create({
            'line_id': line.id, 'amount_state': state, 'amount': amount if state == 'confirmed' else 0,
        })
        return line

    @staticmethod
    def _assign(project, user):
        project.env['tp.project.assignment'].create({'project_id': project.id, 'user_id': user.id})

    @staticmethod
    def _link_group(user, xmlid):
        user.sudo().group_ids = [Command.link(user.env.ref(xmlid).id)]
