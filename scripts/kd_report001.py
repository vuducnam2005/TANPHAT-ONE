"""KD-REPORT-001: owned clone (19389), verified backup/restore, and sealed apply for separate KH-KD Report Center."""
# ruff: noqa: T201, PLC0415
import argparse
import json
import shutil
import sys
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import kd_ui005 as previous

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/kd-report001'
DATABASE = 'tp_tanphat_kdreport001_20261109'
PORT = 19389
SOURCE = BASE / 'source/custom_addons'
MODULE = 'tp_kd_workspace'


def bind():
    previous.BASE = BASE
    previous.DATABASE = DATABASE
    previous.PORT = PORT
    previous.SOURCE = SOURCE
    previous.previous.BASE = BASE
    previous.previous.DATABASE = DATABASE
    previous.previous.PORT = PORT
    previous.previous.SOURCE = SOURCE
    previous.previous.BASELINE_VIEWS = BASE / 'baseline_views'
    return previous.bind()


def hashes(folder=None):
    target = (SOURCE / MODULE) if folder is None else folder
    return previous.previous.previous.tree_hashes(target)


def verify_backup(native):
    """Restore the fresh pre-apply backup to an owned verification DB and verify table & attachment parity."""
    from psycopg2 import sql

    backup = Path(native.read(BASE / 'owner.json')['pre_apply_backup'])
    verify_db = 'tp_tanphat_kdreport001_backup_' + datetime.now(UTC).strftime('%H%M%S')
    with closing(native.connect('postgres', admin=True)) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute('SELECT 1 FROM pg_database WHERE datname=%s', (verify_db,))
            native.require(not cur.fetchone(), 'Verification DB already exists; refusing reuse.')
            native.write(BASE / 'backup-restore-owner.json', {
                'database': verify_db, 'backup': str(backup), 'owned': True,
            })
            cur.execute(sql.SQL("CREATE DATABASE {} OWNER tp_odoo TEMPLATE template0 ENCODING 'UTF8'").format(
                sql.Identifier(verify_db)))
    pg_env = native.backup.pg_environment(native.read(ROOT / '.local/dev-secrets.json')['pg_app'])
    native.backup.run([
        native.dev.pg_bin() / 'pg_restore.exe', '-h', '127.0.0.1', '-p', '55432', '-U', 'tp_odoo',
        '-d', verify_db, '--no-owner', '--no-privileges', '--exit-on-error', backup / 'database.dump',
    ], env=pg_env)
    baseline = native.read(backup / 'baseline.json')
    with closing(native.connect(verify_db)) as conn:
        native.require(native.backup.table_inventory(conn) == baseline['tables'], 'Restored backup tables differ.')
        blobs = native.backup.attachment_inventory(conn, backup / 'filestore')
        native.require(len(blobs) == baseline['attachments'], 'Restored backup attachment count differs.')
    native.write(BASE / 'backup-restore-result.json', {
        'ok': True, 'backup': str(backup), 'database': verify_db,
        'tables': len(baseline['tables']), 'attachment_references': len(blobs),
    })
    print(json.dumps({
        'ok': True, 'verify_db': verify_db,
        'tables': len(baseline['tables']), 'attachments': len(blobs),
    }))


def create_fixture(native):
    """Create synthetic report trap & >100 pagination records on owned clone ONLY."""
    native.target_config('clone')
    marker = BASE / 'fixture.json'
    if marker.exists():
        print('Fixture already exists on clone; reusing.')
        return

    def _build(env):
        delta = native.read(ROOT / '.local/kd-access001/dev-delta.json')
        head_info = delta['users']['head']
        lead_info = delta['users']['project_lead']
        plan_info = delta['users']['planning']
        supp_info = delta['users']['support']

        head = env['res.users'].browse(head_info['id'])
        proj_lead = env['res.users'].browse(lead_info['id'])
        planner = env['res.users'].browse(plan_info['id'])
        support = env['res.users'].browse(supp_info['id'])

        # Project where support + others are assigned
        shared_pid = supp_info['projects'][0]
        other_pid = next(p for p in head_info['projects'] if p not in supp_info['projects'])
        shared_proj = env['project.project'].browse(shared_pid)
        other_proj = env['project.project'].browse(other_pid)
        currency = shared_proj.company_id.currency_id
        from odoo.addons.tp_kd_workspace.models.workspace import _INTERNAL

        # 1. R01 Contract revision traps on shared_proj:
        # Original confirmed (1,000,000,000 excluding_tax) + Amendment effective confirmed (+200,000,000 excluding_tax)
        # + Correction effective confirmed + Draft revision (9,999,999,999 excluding_tax - must NOT be counted as effective!)
        contract = env['tp.contract'].create({
            'code': 'KDR001-HD-TRAP',
            'name': '=SUM(1,2) Hợp đồng kiểm chứng R01 (bẫy công thức & phiên bản)',
            'project_id': shared_proj.id,
            'company_id': shared_proj.company_id.id,
            'partner_id': shared_proj.partner_id.id,
            'contract_type': 'owner',
            'lifecycle_state': 'not_effective',
        })
        rev_orig = env['tp.contract.revision'].with_context(tp_contract_workflow=True).create({
            'contract_id': contract.id,
            'sequence': 0,
            'revision_kind': 'original',
            'name': 'Bản gốc đã hiệu lực',
            'review_state': 'draft',
            'signature_status': 'unsigned',
            'signature_authority_status': 'pending',
            'effectivity_status': 'not_effective',
        })
        line_orig = env['tp.contract.line'].create({
            'revision_id': rev_orig.id,
            'sequence': 10,
            'scope_key': 'HM-01',
            'name': 'Hạng mục gốc',
            'change_kind': 'original',
        })
        env['tp.contract.line.amount'].create({
            'line_id': line_orig.id,
            'amount_state': 'confirmed',
            'tax_basis': 'excluding_tax',
            'currency_id': currency.id,
            'amount': 1_000_000_000,
        })
        rev_orig.with_context(tp_contract_workflow=True).write({
            'review_state': 'review_complete',
            'signature_status': 'signed_recorded',
            'signature_authority_status': 'confirmed',
            'effectivity_status': 'effective_recorded',
            'effective_date': '2026-11-01',
            'signed_date': '2026-11-01',
        })

        rev_amend = env['tp.contract.revision'].with_context(tp_contract_workflow=True).create({
            'contract_id': contract.id,
            'sequence': 1,
            'revision_kind': 'amendment',
            'previous_revision_id': rev_orig.id,
            'name': 'Phụ lục 01 đã hiệu lực',
            'review_state': 'draft',
            'signature_status': 'unsigned',
            'signature_authority_status': 'pending',
            'effectivity_status': 'not_effective',
        })
        line_amend = env['tp.contract.line'].create({
            'revision_id': rev_amend.id,
            'sequence': 10,
            'scope_key': 'HM-01',
            'name': 'Giá trị sau phụ lục 01',
            'change_kind': 'amended',
            'previous_line_id': line_orig.id,
        })
        env['tp.contract.line.amount'].create({
            'line_id': line_amend.id,
            'amount_state': 'confirmed',
            'tax_basis': 'excluding_tax',
            'currency_id': currency.id,
            'amount': 1_200_000_000,
        })
        rev_amend.with_context(tp_contract_workflow=True).write({
            'review_state': 'review_complete',
            'signature_status': 'signed_recorded',
            'signature_authority_status': 'confirmed',
            'effectivity_status': 'effective_recorded',
            'effective_date': '2026-11-05',
            'signed_date': '2026-11-05',
        })

        rev_draft = env['tp.contract.revision'].with_context(tp_contract_workflow=True).create({
            'contract_id': contract.id,
            'sequence': 2,
            'revision_kind': 'amendment',
            'previous_revision_id': rev_amend.id,
            'name': 'Phụ lục 02 đang nháp (không được tính hiệu lực)',
            'review_state': 'draft',
            'signature_status': 'unsigned',
            'signature_authority_status': 'pending',
            'effectivity_status': 'not_effective',
        })
        line_draft = env['tp.contract.line'].create({
            'revision_id': rev_draft.id,
            'sequence': 10,
            'scope_key': 'HM-01',
            'name': 'Giá trị nháp',
            'change_kind': 'amended',
            'previous_line_id': line_amend.id,
        })
        env['tp.contract.line.amount'].create({
            'line_id': line_draft.id,
            'amount_state': 'confirmed',
            'tax_basis': 'excluding_tax',
            'currency_id': currency.id,
            'amount': 9_999_999_999,
        })
        contract.with_context(tp_contract_workflow=True).write({'lifecycle_state': 'effective'})

        # 2. R04 Allocation parent + child trap:
        # Level 1 parent = 500,000,000 confirmed; two Level 2 children = 300,000,000 + 250,000,000 (overrun_warning=True)
        alloc_parent = env['tp.allocation'].create({
            'code': 'KDR001-GK-P1',
            'name': '+cmd Giao khoán cấp 1 kiểm chứng không cộng trùng con',
            'project_id': shared_proj.id,
            'contract_id': contract.id,
            'allocation_kind': 'subcontract',
            'partner_id': shared_proj.partner_id.id,
            'scope': 'Giao khoán gói cầu chính',
            'date_due': '2026-11-15',
            'date': '2026-11-01',
            'owner_id': proj_lead.id,
            'reviewer_id': head.id,
        })
        env['tp.allocation.amount'].with_context(_kd_internal=_INTERNAL).create({
            'record_id': alloc_parent.id,
            'amount_state': 'confirmed',
            'value': 500_000_000,
            'tax_basis': 'excluding_tax',
            'currency_id': currency.id,
        })
        alloc_c1 = env['tp.allocation'].create({
            'code': 'KDR001-GK-C1',
            'name': 'Phân bổ con cấp 2 - Hạng mục mố trụ',
            'project_id': shared_proj.id,
            'contract_id': contract.id,
            'parent_id': alloc_parent.id,
            'allocation_kind': 'subcontract',
            'partner_id': shared_proj.partner_id.id,
            'scope': 'Mố trụ',
            'date_due': '2026-11-15',
            'date': '2026-11-01',
            'owner_id': proj_lead.id,
            'reviewer_id': head.id,
        })
        env['tp.allocation.amount'].with_context(_kd_internal=_INTERNAL).create({
            'record_id': alloc_c1.id,
            'amount_state': 'confirmed',
            'value': 300_000_000,
            'tax_basis': 'excluding_tax',
            'currency_id': currency.id,
        })
        alloc_c2 = env['tp.allocation'].create({
            'code': 'KDR001-GK-C2',
            'name': 'Phân bổ con cấp 2 - Hạng mục dầm',
            'project_id': shared_proj.id,
            'contract_id': contract.id,
            'parent_id': alloc_parent.id,
            'allocation_kind': 'subcontract',
            'partner_id': shared_proj.partner_id.id,
            'scope': 'Dầm cầu',
            'date_due': '2026-11-15',
            'date': '2026-11-01',
            'owner_id': proj_lead.id,
            'reviewer_id': head.id,
        })
        env['tp.allocation.amount'].with_context(_kd_internal=_INTERNAL).create({
            'record_id': alloc_c2.id,
            'amount_state': 'confirmed',
            'value': 250_000_000,
            'tax_basis': 'excluding_tax',
            'currency_id': currency.id,
        })

        # 3. R03 Plan, Production, Acceptance, Payment Request (Receipt & Disbursement)
        plan_rec = env['tp.periodic.plan'].search([
            ('project_id', '=', shared_proj.id),
            ('period_kind', '=', 'month'),
            ('period_from', '=', '2026-11-01'),
            ('period_to', '=', '2026-11-30'),
        ], limit=1)
        if not plan_rec:
            plan_rec = env['tp.periodic.plan'].create({
                'code': 'KDR001-KH-01',
                'name': 'Kế hoạch tháng 11/2026',
                'project_id': shared_proj.id,
                'period_kind': 'month',
                'period_from': '2026-11-01',
                'period_to': '2026-11-30',
                'scope': 'Kế hoạch khảo sát thiết kế tháng 11',
                'date_due': '2026-11-10',
                'date': '2026-11-01',
                'owner_id': planner.id,
                'reviewer_id': head.id,
            })
        existing_plan_amt = env['tp.periodic.plan.amount'].search([
            ('record_id', '=', plan_rec.id),
            ('measure', '=', 'production'),
        ], limit=1)
        if not existing_plan_amt:
            env['tp.periodic.plan.amount'].with_context(_kd_internal=_INTERNAL).create({
                'record_id': plan_rec.id,
                'measure': 'production',
                'amount_state': 'confirmed',
                'value': 400_000_000,
                'tax_basis': 'excluding_tax',
                'currency_id': currency.id,
            })

        prod_rec = env['tp.production'].create({
            'code': 'KDR001-SL-01',
            'name': 'Sản lượng đợt 1 tháng 11/2026',
            'project_id': shared_proj.id,
            'contract_id': contract.id,
            'allocation_id': alloc_parent.id,
            'period_from': '2026-11-01',
            'period_to': '2026-11-20',
            'quantity': 12.5,
            'unit': 'km',
            'scope': 'Sản lượng thực hiện đợt 1',
            'date_due': '2026-11-20',
            'date': '2026-11-10',
            'owner_id': proj_lead.id,
            'reviewer_id': head.id,
        })
        env['tp.production.amount'].with_context(_kd_internal=_INTERNAL).create({
            'record_id': prod_rec.id,
            'amount_state': 'confirmed',
            'value': 200_000_000,
            'tax_basis': 'excluding_tax',
            'currency_id': currency.id,
        })

        acc_rec = env['tp.acceptance'].create({
            'code': 'KDR001-NT-01',
            'name': 'Nghiệm thu giai đoạn khảo sát đợt 1',
            'project_id': shared_proj.id,
            'contract_id': contract.id,
            'production_id': prod_rec.id,
            'counterparty_id': shared_proj.partner_id.id,
            'period_from': '2026-11-01',
            'period_to': '2026-11-20',
            'date': '2026-11-22',
            'round_code': 'Đợt 1',
            'quantity': 12.5,
            'unit': 'km',
            'evidence_checklist': 'Biên bản nghiệm thu đợt 1',
            'scope': 'Biên bản nghiệm thu nội bộ',
            'date_due': '2026-11-25',
            'owner_id': proj_lead.id,
            'reviewer_id': head.id,
        })
        env['tp.acceptance.amount'].with_context(_kd_internal=_INTERNAL).create({
            'record_id': acc_rec.id,
            'amount_state': 'confirmed',
            'value': 180_000_000,
            'tax_basis': 'excluding_tax',
            'currency_id': currency.id,
        })

        pay_in = env['tp.payment.request'].create({
            'code': 'KDR001-TT-THU',
            'name': 'Đề nghị thu đợt 1 theo nghiệm thu',
            'project_id': shared_proj.id,
            'contract_id': contract.id,
            'acceptance_id': acc_rec.id,
            'partner_id': shared_proj.partner_id.id,
            'direction': 'receipt',
            'payment_basis': 'acceptance',
            'document_checklist': 'Hồ sơ nghiệm thu đợt 1 và hóa đơn VAT',
            'date': '2026-11-25',
            'date_due': '2026-11-30',
            'scope': 'Đề nghị chủ đầu tư thanh toán',
            'owner_id': planner.id,
            'reviewer_id': head.id,
        })
        env['tp.payment.request.amount'].with_context(_kd_internal=_INTERNAL).create({
            'record_id': pay_in.id,
            'amount_state': 'confirmed',
            'value': 150_000_000,
            'tax_basis': 'excluding_tax',
            'currency_id': currency.id,
        })

        pay_out = env['tp.payment.request'].create({
            'code': 'KDR001-TT-CHI',
            'name': 'Đề nghị chi tạm ứng thầu phụ',
            'project_id': shared_proj.id,
            'contract_id': contract.id,
            'partner_id': shared_proj.partner_id.id,
            'direction': 'disbursement',
            'payment_basis': 'advance',
            'advance_basis': 'Tạm ứng hợp đồng thầu phụ 20%',
            'document_checklist': 'Giấy đề nghị tạm ứng và bảo lãnh tạm ứng',
            'date': '2026-11-26',
            'date_due': '2026-11-30',
            'scope': 'Đề nghị chi tạm ứng',
            'owner_id': planner.id,
            'reviewer_id': head.id,
        })
        env['tp.payment.request.amount'].with_context(_kd_internal=_INTERNAL).create({
            'record_id': pay_out.id,
            'amount_state': 'unconfirmed',
            'value': 0,
            'tax_basis': 'excluding_tax',
            'currency_id': currency.id,
        })

        # 4. R06 Credential linked to multiple opportunities + Obligation
        cred_multi = env['tp.credential'].create({
            'code': 'KDR001-NL-MULTI',
            'name': '@cmd Chứng chỉ năng lực khảo sát hạng I (gắn nhiều cơ hội)',
            'project_id': shared_proj.id,
            'subject_id': shared_proj.partner_id.id,
            'subject_kind': 'organization',
            'credential_kind': 'Chứng chỉ năng lực tổ chức',
            'valid_from': '2025-01-01',
            'valid_to': '2026-11-20',
            'scope': 'Khảo sát địa hình, địa chất công trình cầu đường',
            'source_note': 'Bản chụp đối chiếu nội bộ',
            'date_due': '2026-11-18',
            'date': '2025-01-01',
            'owner_id': planner.id,
            'reviewer_id': head.id,
        })
        ob_rec = env['tp.obligation'].create({
            'code': 'KDR001-NV-01',
            'name': '-cmd Bảo lãnh thực hiện hợp đồng KDR001',
            'project_id': shared_proj.id,
            'contract_id': contract.id,
            'obligation_kind': 'contract_docs',
            'checklist_status': 'internal_checked',
            'document_checklist': 'Hồ sơ pháp lý hợp đồng, bảo lãnh thực hiện hợp đồng 10%',
            'checklist_update_reason': 'Đã đối chiếu danh mục tài liệu theo hồ sơ mời thầu',
            'date_due': '2026-11-15',
            'date': '2026-11-01',
            'scope': 'Bảo lãnh thực hiện hợp đồng 10%',
            'owner_id': planner.id,
            'reviewer_id': head.id,
        })

        preproject_team = env['crm.team'].search([('kd_department_id', '=', head.department_id.id)], limit=1)
        if not preproject_team:
            preproject_team = env['crm.team'].create({
                'name': 'Đội KH-KD Tiền dự án Fixture',
                'company_id': head.department_id.company_id.id,
                'kd_department_id': head.department_id.id,
                'member_ids': [(6, 0, [head.id, support.id, proj_lead.id, planner.id])],
            })

        # 5. R02 >100 Opportunities (112 records) including pre-project opportunities and multi-credential links
        lead_vals = []
        for idx in range(110):
            is_shared = (idx % 2 == 0)
            p = shared_proj if is_shared else other_proj
            owner = support if (is_shared and idx % 10 == 0) else (proj_lead if is_shared else head)
            lead_vals.append({
                'name': f'KDR001-CH-{idx + 1:03d} — Hồ sơ thầu gói cầu đường số {idx + 1:03d}',
                'type': 'opportunity',
                'tp_project_id': p.id,
                'company_id': p.company_id.id,
                'partner_id': p.partner_id.id,
                'user_id': owner.id,
                'kd_route': 'bid' if idx % 2 == 0 else 'direct',
                'kd_source': 'Hệ thống mạng đấu thầu quốc gia',
                'kd_scope': 'Tư vấn khảo sát và lập báo cáo nghiên cứu khả thi',
                'kd_checklist': 'Đã tập hợp hồ sơ năng lực và nhân sự chủ chốt',
                'kd_deadline': f'2026-11-{(idx % 28) + 1:02d}',
                'kd_receipt': f'BN-{idx + 1:03d}' if idx % 3 == 0 else False,
                'expected_revenue': 50_000_000 + (idx * 1_000_000),
                'kd_credential_link_ids': [(6, 0, [cred_multi.id])] if idx < 3 else [],
            })
        # Add 2 pre-project opportunities (tp_project_id=False)
        for alias, u in [('head', head), ('support', support)]:
            lead_vals.append({
                'name': f'KDR001-PRE-{alias.upper()} — Cơ hội tiền dự án chưa gắn mã dự án ({alias})',
                'type': 'opportunity',
                'tp_project_id': False,
                'company_id': shared_proj.company_id.id,
                'partner_id': shared_proj.partner_id.id,
                'user_id': u.id,
                'team_id': preproject_team.id,
                'kd_route': 'bid',
                'kd_source': 'Thông tin mời quan tâm sơ bộ',
                'kd_scope': 'Cơ hội tiền dự án',
                'kd_checklist': 'Đang rà soát năng lực',
                'kd_deadline': '2026-11-25',
                'expected_revenue': 0,
            })
        leads = env['crm.lead'].create(lead_vals)
        for idx, lead in enumerate(leads[:110]):
            bstate = 'submitted' if idx % 3 == 0 else ('preparation' if idx % 3 == 1 else 'identified')
            if bstate != 'identified':
                lead.with_context(_kd_internal=_INTERNAL).write({'kd_bid_state': bstate})
        result = {
            'shared_project_id': shared_proj.id,
            'other_project_id': other_proj.id,
            'contract_id': contract.id,
            'alloc_parent_id': alloc_parent.id,
            'alloc_children_ids': [alloc_c1.id, alloc_c2.id],
            'plan_id': plan_rec.id,
            'production_id': prod_rec.id,
            'acceptance_id': acc_rec.id,
            'payment_in_id': pay_in.id,
            'payment_out_id': pay_out.id,
            'credential_id': cred_multi.id,
            'obligation_id': ob_rec.id,
            'lead_ids': leads.ids,
        }
        env.cr.commit()
        return result

    native.write(marker, native.orm('clone', _build))
    print('CLONE FIXTURE CREATED: R01-R06 traps + 112 opportunities on owned clone only.')


def phase(native, label):
    """Toggle head's financial_read grant on shared_project_id on clone ONLY for live revocation testing."""
    native.require(label in ('normal', 'revoked'), 'Invalid phase label.')

    def _toggle(env):
        delta = native.read(ROOT / '.local/kd-access001/dev-delta.json')
        fx = native.read(BASE / 'fixture.json')
        head_id = delta['users']['head']['id']
        pid = fx['shared_project_id']
        grants = env['tp.project.grant'].with_context(active_test=False).search([
            ('user_id', '=', head_id),
            ('project_id', '=', pid),
            ('capability', '=', 'financial_read'),
        ])
        native.require(bool(grants), 'Expected financial_read grant on shared project.')
        grants.write({'active': label == 'normal'})
        env.cr.commit()
        return {'label': label, 'grants': grants.ids, 'active': label == 'normal'}

    print(json.dumps(native.orm('clone', _toggle)))


def preservation(native, label):
    extra = ['ir_access', 'ir_ui_menu', 'tp_crm_credential_rel', 'res_company',
             'ir_act_window_group_rel', 'ir_ui_view_group_rel', 'ir_model_fields_group_rel']
    for table in extra:
        if table not in previous.previous.previous.PRESERVED:
            previous.previous.previous.PRESERVED.append(table)
    result = previous.previous.previous.rowset(native, 'tp_tanphat_dev')
    native.write(BASE / f'preservation-{label}.json', result)
    before_file = BASE / 'preservation-before.json'
    if label != 'before' and before_file.exists():
        report = previous.previous.previous.compare(native.read(before_file), result)
        changed = {k: v for k, v in report.items() if v['missing_or_changed'] or v['added']}
        native.write(BASE / f'preservation-{label}-diff.json', report)
        business_changed = {k: v for k, v in changed.items() if k not in ('ir_access', 'ir_ui_menu')}
        native.require(not business_changed, f'Dev business records changed: {list(business_changed.keys())}')
        if 'ir_access' in changed:
            acc = changed['ir_access']
            native.require(acc['missing_or_changed'] == 0 and acc['added'] == 1,
                           'Unexpected ir_access changes beyond new report center model.')
        if 'ir_ui_menu' in changed:
            menu = changed['ir_ui_menu']
            native.require(menu['rows_before'] == menu['rows_after'] and menu['missing_or_changed'] == 1 and menu['added'] == 1,
                           'Unexpected ir_ui_menu changes beyond separated report action.')
    print(json.dumps({'label': label, 'tables': len(result),
                      'rows': sum(sum(v['hashes'].values()) for v in result.values())}))


def apply_to_dev(native):
    import subprocess
    import time

    owner = native.read(BASE / 'owner.json')
    backup = Path(owner['pre_apply_backup'])
    restored = native.read(BASE / 'backup-restore-result.json')
    native.require(restored.get('ok') and restored.get('backup') == str(backup), 'Verified backup restore required.')
    native.require(backup.resolve().is_relative_to(BASE.resolve()), 'Foreign backup.')
    native.require(0 <= datetime.now(UTC).timestamp() - (backup / 'manifest.json').stat().st_mtime < 900,
                   'Fresh verified backup required (< 15 min).')
    native.require(native.read(BASE / 'sealed-source.json') == hashes(), 'Source differs from sealed clone.')

    target = ROOT / 'custom_addons' / MODULE
    shutil.copytree(SOURCE / MODULE, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    stale = set(hashes(target)) - set(hashes())
    for name in stale:
        (target / name).unlink()
    native.require(hashes(target) == hashes(), 'Target does not match sealed clone source.')

    native.target_config('dev')
    stamp = datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')
    logfile = BASE / f'dev-apply-{stamp}.log'
    if native.dev.is_listening(18069):
        native.dev.stop_server()
        native.require(not native.dev.is_listening(18069), 'Dev listener not stopped.')

    args = [sys.executable, '-X', 'utf8', str(ROOT / 'odoo-bin'), '-c', str(ROOT / '.local/odoo.conf'),
            '-d', 'tp_tanphat_dev', '-u', MODULE, '--no-http', '--stop-after-init', '--logfile', str(logfile)]
    with (BASE / f'dev-apply-{stamp}-console.log').open('wb') as output:
        completed = subprocess.run(args, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, check=False)
    text = logfile.read_text(encoding='utf-8', errors='replace')
    errors = [line for line in text.splitlines() if ' ERROR ' in line or ' CRITICAL ' in line]
    native.require(completed.returncode == 0 and not errors, 'Dev upgrade failed; dev kept stopped for rollback.')

    native.dev.start_server()
    deadline = time.monotonic() + 30
    while not native.dev.is_listening(18069):
        if time.monotonic() > deadline:
            raise RuntimeError('Dev server listener timed out on 18069.')
        time.sleep(0.5)

    print('DEV 18069 READY: sealed changes applied and running.')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=[
        'prepare', 'start', 'stop', 'upgrade', 'test', 'fixture', 'phase',
        'preserve', 'extended', 'backup', 'seal', 'apply', 'rollback',
    ])
    parser.add_argument('--label', default='before')
    parser.add_argument('--focused', action='store_true')
    args = parser.parse_args()
    native = bind()

    if args.command == 'prepare':
        previous.previous.prepare(native)
        baseline_addon = BASE / 'baseline_addon'
        if not baseline_addon.exists():
            shutil.copytree(
                ROOT / 'custom_addons' / MODULE,
                baseline_addon,
                ignore=shutil.ignore_patterns('__pycache__', '*.pyc'),
            )
        native.write(BASE / 'baseline-source.json', hashes(ROOT / 'custom_addons' / MODULE))
        print('KD-REPORT-001 CLONE READY:', DATABASE, PORT)
    elif args.command in ('start', 'stop'):
        native.runtime(args.command)
    elif args.command == 'upgrade':
        return previous.previous.upgrade(native)
    elif args.command == 'test':
        modules = 'tp_kd_workspace' if args.focused else 'tp_kd_workspace,tp_contract,tp_crm_project_bridge,tp_project,tp_web_home'
        tags = '/tp_kd_workspace' if args.focused else '/tp_kd_workspace,/tp_contract,/tp_crm_project_bridge,/tp_project,/tp_web_home'
        code = previous.kd.tests(modules, tags)
        native.require(code == 0, 'Odoo test suite failed on clone.')
        fname = 'focused-tests.json' if args.focused else 'tested-source.json'
        native.write(BASE / fname, {'ok': True, 'source_hashes': hashes()})
        return code
    elif args.command == 'fixture':
        create_fixture(native)
    elif args.command == 'phase':
        phase(native, args.label)
    elif args.command == 'preserve':
        preservation(native, args.label)
    elif args.command == 'extended':
        previous.extended_preservation(native, args.label)
    elif args.command == 'backup':
        previous.previous.backup(native)
        verify_backup(native)
    elif args.command == 'seal':
        tested = native.read(BASE / 'tested-source.json')
        native.require(tested.get('ok') and tested.get('source_hashes') == hashes(), 'Source changed since Odoo tests.')
        for filename in ('browser-result.json', 'hoot-result.json', 'perf-result.json'):
            report = native.read(BASE / filename)
            native.require(report.get('ok') and not report.get('failures') and not report.get('errors'), filename)
            native.require(report.get('source_hashes') == hashes(), f'{filename} tested different source.')
        native.write(BASE / 'sealed-source.json', hashes())
        print('SEALED: exact clone source passed Odoo, HOOT, browser, Excel export, and performance gates.')
    elif args.command == 'apply':
        apply_to_dev(native)
        preservation(native, 'after')
        previous.extended_preservation(native, 'after')
    elif args.command == 'rollback':
        target = (ROOT / 'custom_addons' / MODULE).resolve()
        native.require(target == Path('C:/TANPHAT ONE/custom_addons/tp_kd_workspace').resolve(), 'Unsafe rollback.')
        previous.previous.previous.rollback(native)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
