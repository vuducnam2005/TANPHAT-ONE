"""Hash-only preservation evidence. Capture before each dev batch and compare afterward."""
# ruff: noqa: T201, EM101
import argparse
import hashlib
import json
from pathlib import Path

import ai_workflow
import native_data003 as task
from psycopg2 import sql


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def capture():
    task.preflight()
    output = {'tables': {}, 'files': {}, 'cluster': {}}
    with task.connect('tp_tanphat_dev') as connection, connection.cursor() as cursor:
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        tables = [r[0] for r in cursor.fetchall()]
        for table in tables:
            cursor.execute(sql.SQL('SELECT row_to_json(t) FROM public.{} t').format(sql.Identifier(table)))
            rows = [r[0] for r in cursor.fetchall()]
            if all('id' in row for row in rows):
                output['tables'][table] = {str(row['id']): {key: digest(value) for key, value in row.items()} for row in rows}
            else:
                output['tables'][table] = sorted(digest(row) for row in rows)
        for name, query in {
            'databases': 'SELECT oid,datname,datdba,encoding,datcollate,datctype FROM pg_database ORDER BY oid',
            'roles': 'SELECT oid,rolname,rolsuper,rolinherit,rolcreaterole,rolcreatedb,rolcanlogin,rolconfig FROM pg_roles ORDER BY oid',
        }.items():
            cursor.execute(query)
            output['cluster'][name] = [list(row) for row in cursor.fetchall()]
    for name in ('.local/odoo.conf', '.local/dev-secrets.json', '.local/runtime-owner.json',
                 '.local/postgres/data/postgresql.conf', '.local/postgres/data/pg_hba.conf'):
        output['files'][name] = task.backup.digest(task.ROOT / name)
    return output


def compare(before, after):
    task.require(before['files'] == after['files'], 'Shared config/credentials changed.')
    task.require(before['cluster'] == after['cluster'], 'Shared database catalog/roles changed.')
    result = {}
    for name in before['tables'].keys() | after['tables'].keys():
        old, new = before['tables'].get(name, {}), after['tables'].get(name, {})
        if old == new:
            continue
        if isinstance(old, list) or isinstance(new, list):
            result[name] = {'relation_changed': True, 'before': len(old), 'after': len(new),
                            'removed_hashes': sorted(set(old) - set(new)), 'added_hashes': sorted(set(new) - set(old))}
        else:
            result[name] = {
                'created': sorted(new.keys() - old.keys(), key=int), 'deleted': sorted(old.keys() - new.keys(), key=int),
                'updated': {key: sorted(field for field in old[key].keys() | new[key].keys() if old[key].get(field) != new[key].get(field))
                            for key in old.keys() & new.keys() if old[key] != new[key]},
            }
    return {'changed_tables': result, 'unchanged_tables': len(before['tables']) - len(result),
            'config_credentials_cluster_roles_unchanged': True}


def audit(before, after):
    """Review every changed table and enforce the observed, documented field boundary."""
    diff = compare(before, after)
    # Row IDs originate in the proven namespace inventory, not names/display labels.
    updates = {
        'account_analytic_line': (range(21, 41), {'manager_id', 'write_date'}),
        'calendar_event': (range(9, 17), {'write_date', 'write_uid'}),
        'crm_lead': (range(11, 21), {'tp_project_id', 'date_open', 'duration_tracking', 'user_id', 'write_date'}),
        'hr_employee': (range(13, 25), {'parent_id', 'coach_id', 'expense_manager_id', 'user_id', 'work_contact_id', 'write_date'}),
        'hr_expense': (range(7, 13), {'manager_id', 'account_move_id', 'approval_date', 'approval_state', 'state',
                                   'last_notification_date', 'write_date', 'write_uid'}),
        'hr_version': ([22], {'last_modified_date', 'tz', 'write_date'}),
        'ir_attachment': ([405], {'checksum', 'file_size', 'index_content', 'store_fname', 'write_date', 'write_uid'}),
        'ir_config_parameter': ([29], {'value', 'write_date'}),  # Cumulative bootstrap journal reconciliation.
        'ir_module_module': (range(1, 690), {'write_date'}),
        'mail_presence': (range(1, 1000000), {'last_presence', 'last_poll', 'status', 'write_date', 'write_uid'}),
        'res_partner': ([54, 55, 56, 57, 58, 59, 60, 63], {'employee', 'lang', 'write_date'}),
        'res_users': ([18, 19, 20, 21, 22, 23, 24], {'notification_type', 'password', 'odoobot_state', 'write_date', 'write_uid'}),
        'resource_resource': ([23], {'tz', 'user_id', 'write_date'}),
        'spreadsheet_dashboard': ([1, 2, 5, 6], {'tp_internal_only', 'write_date', 'write_uid'}),
    }
    categories = {
        'module_metadata': 'ir_access ir_model_constraint ir_model_data ir_model_fields ir_model_fields_group_rel '
                           'ir_module_module ir_module_module_dependency ir_ui_view',
        'fixture_links_and_actors': 'account_analytic_line calendar_attendee calendar_event calendar_event_res_partner_rel '
                                  'crm_lead hr_employee hr_expense hr_version ir_config_parameter res_users '
                                  'res_partner resource_resource res_groups_users_rel res_company_users_rel '
                                  'spreadsheet_dashboard spreadsheet_dashboard_allowed_users_rel tp_project_assignment',
        'native_receipts': 'account_move account_move_line account_move_line_account_tax_rel account_account_tag_account_move_line_rel',
        'native_user_onboarding': 'calendar_calendar calendar_user digest_digest_res_users_rel project_task project_task_type '
                                  'project_task_user_rel res_users_settings ir_attachment',
        'native_history_and_members': 'discuss_channel discuss_channel_member mail_activity mail_followers '
                                     'mail_followers_mail_message_subtype_rel mail_mail mail_message',
        'runtime_telemetry': 'bus_bus mail_presence res_device_log res_users_log orm_signaling_default '
                             'orm_signaling_registry orm_signaling_stable ir_cron_trigger',
    }
    classification = {table: category for category, tables in categories.items() for table in tables.split()}
    for table, delta in diff['changed_tables'].items():
        task.require(table in classification, 'Unreviewed changed table: ' + table)
        task.require(not delta.get('deleted') and not delta.get('removed_hashes'), 'Existing row/relation removed: ' + table)
        for record_id, fields in delta.get('updated', {}).items():
            task.require(table in updates, 'Unreviewed existing update: ' + table)
            ids, allowed = updates[table]
            task.require(int(record_id) in ids and set(fields) <= allowed, 'Unreviewed field change: ' + table + '/' + record_id)
    # Restrict old data more tightly than the coarse field unions above.
    for rid, fields in diff['changed_tables'].get('crm_lead', {}).get('updated', {}).items():
        task.require(int(rid) in (11, 13, 15, 18) or fields == ['tp_project_id'], 'Unlinked lead changed.')
    for rid, fields in diff['changed_tables'].get('spreadsheet_dashboard', {}).get('updated', {}).items():
        task.require(int(rid) in (5, 6) or fields == ['tp_internal_only'], 'Standard dashboard changed.')
    # Every original blob still exists with its old checksum, including the previous dashboard version.
    owner = task.read(task.BASE / 'owner.json')
    baseline = task.read(Path(owner['snapshot']) / 'baseline.json')
    store = task.ROOT / '.local/odoo/filestore/tp_tanphat_dev'
    for row in baseline['attachments']:
        blob = store / row['store_fname']
        task.require(blob.is_file() and blob.stat().st_size == row['bytes']
                     and task.backup.digest(blob, 'sha1') == row['sha1'], 'Original blob changed.')
    with task.connect('tp_tanphat_dev') as connection:
        current_blobs = task.backup.attachment_inventory(connection, store)
        current_by_id = {row['id']: row for row in current_blobs}
        task.require(all(row['id'] == 405 or current_by_id.get(row['id']) == row for row in baseline['attachments']),
                     'Original attachment reference changed outside dashboard405.')
    source_baseline = task.BASE / 'source-baseline.json'
    if not source_baseline.exists():
        task.write(source_baseline, task.read(task.ROOT / '.local/ai-workflow/active.json')['code'])
    checkpoint = task.read(source_baseline)['files']
    current_code = ai_workflow.snapshot(task.ROOT)['files']
    task.require(all(current_code.get(path) == value for path, value in checkpoint.items()), 'Pre-existing maintained code changed.')
    return {**diff, 'classification': classification, 'old_blob_references_verified': len(baseline['attachments']),
            'current_blob_references_verified': len(current_blobs), 'old_code_files_unchanged': len(checkpoint),
            'limits': 'New-row semantics reviewed in runbook; other DB contents not fingerprinted, only catalog/owner/roles/config.',
            'passed': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label')
    parser.add_argument('--compare')
    parser.add_argument('--audit', action='store_true')
    args = parser.parse_args()
    current = capture()
    task.write(task.BASE / f'preserve-{args.label}.json', current)
    if args.compare:
        result = (audit if args.audit else compare)(task.read(task.BASE / f'preserve-{args.compare}.json'), current)
        task.write(task.BASE / f'preserve-diff-{args.compare}-{args.label}.json', result)
        print(json.dumps(result))
    else:
        print('PRESERVATION BASELINE:', args.label, len(current['tables']), 'tables; hash-only private report.')


if __name__ == '__main__':
    main()
