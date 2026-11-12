"""Review every dev table delta against the narrow DASH-UI-001 boundary."""
# ruff: noqa: T201, EM101
from pathlib import Path

import native_data003 as native
import native_data003_preserve as preserve

BASE = Path(__file__).resolve().parents[1] / '.local/dash-ui001'


def main():
    before = native.read(native.BASE / 'preserve-dashui001-before.json')
    after = preserve.capture()
    native.write(BASE / 'preserve-final.json', after)
    diff = preserve.compare(before, after)
    allowed = {'ir_attachment', 'spreadsheet_dashboard', 'ir_module_module', 'ir_module_module_dependency',
               'bus_bus', 'ir_cron_trigger', 'orm_signaling_registry', 'res_users_log', 'res_device_log', 'mail_presence'}
    for table, delta in diff['changed_tables'].items():
        native.require(table in allowed, 'Unexpected changed table: ' + table)
        native.require(not delta.get('relation_changed'), 'Unexpected relation rewrite.')
        if table == 'spreadsheet_dashboard':
            native.require(not delta['created'] and not delta['deleted'], 'Dashboard identity set changed.')
            for rid, fields in delta['updated'].items():
                native.require(rid in ('5', '6') and set(fields) <= {'name', 'write_date', 'write_uid'}, 'Dashboard access drift.')
        elif table == 'ir_attachment':
            native.require(set(delta['deleted']) <= {'155', '399', '400'}, 'Unexpected attachment deletion.')
            names = {'spreadsheet.o_spreadsheet.min.js', 'web.assets_web.min.css', 'web.assets_web_print.min.css'}
            for rid in delta['deleted']:
                old = before['tables'][table][rid]
                native.require(old.get('name') in {preserve.digest(name) for name in names}, 'Deleted row is not a regenerated asset.')
            for rid in delta['created']:
                native.require(after['tables'][table][rid].get('name') in {preserve.digest(name) for name in names}, 'Unexpected new attachment.')
            for rid, fields in delta['updated'].items():
                native.require(rid in ('404', '405') and set(fields) <= {
                    'checksum', 'file_size', 'index_content', 'store_fname', 'write_date', 'write_uid'}, 'Unexpected file mutation.')
        elif table == 'ir_module_module':
            native.require(not delta['created'] and not delta['deleted'], 'Module inventory changed.')
            for rid, fields in delta['updated'].items():
                native.require(set(fields) <= ({'write_date', 'latest_version'} if rid == '691' else {'write_date'}), 'Unexpected module state change.')
        elif table == 'ir_module_module_dependency':
            native.require(not delta['deleted'] and not delta['updated'] and len(delta['created']) == 3, 'Unexpected module dependency delta.')
        elif table == 'mail_presence':
            native.require(not delta['created'] and not delta['deleted'] and all(set(fields) <= {
                'last_poll', 'last_presence', 'status', 'write_date', 'write_uid'} for fields in delta['updated'].values()), 'Unexpected presence delta.')
        else:
            native.require(not delta['deleted'] and not delta['updated'], 'Unexpected telemetry rewrite.')
    owner = native.read(BASE / 'owner.json')
    baseline = native.read(Path(owner['snapshot']) / 'baseline.json')
    store = native.ROOT / '.local/odoo/filestore/tp_tanphat_dev'
    for row in baseline['attachments']:
        blob = store / row['store_fname']
        native.require(blob.is_file() and blob.stat().st_size == row['bytes']
                       and native.backup.digest(blob, 'sha1') == row['sha1'], 'Original blob lost or changed.')
    with native.connect('tp_tanphat_dev') as connection:
        current = native.backup.attachment_inventory(connection, store)
    report = {'passed': True, 'unchanged_tables': diff['unchanged_tables'],
              'changed_tables': sorted(diff['changed_tables']), 'all_original_blobs_verified': len(baseline['attachments']),
              'current_references_verified': len(current), 'config_credentials_catalog_roles_unchanged': True,
              'business_users_passwords_groups_acl_rules_assignments_unchanged': True}
    native.write(BASE / 'preservation-acceptance.json', report)
    print(report)


if __name__ == '__main__':
    main()
