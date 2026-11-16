"""Map the former fixed priority selection to the shared priority catalog (CORP-REPORT-001 addendum).

Old codes: '0' normal, '1' high, '2' urgent. Rows without a mapping get the default catalog entry.
"""


def migrate(cr, version):
    cr.execute("""
        SELECT res_id, name FROM ir_model_data
         WHERE module = 'tp_reporting' AND model = 'tp.report.priority'
           AND name IN ('priority_normal', 'priority_high', 'priority_urgent')
    """)
    ids = {name: res_id for res_id, name in cr.fetchall()}
    if 'priority_normal' not in ids:
        return
    mapping = {'0': ids['priority_normal'], '1': ids.get('priority_high'), '2': ids.get('priority_urgent')}
    for table in ('tp_report_plan', 'tp_report_line'):
        cr.execute("""
            SELECT 1 FROM information_schema.columns
             WHERE table_name = %s AND column_name = 'priority'
        """, [table])
        if cr.fetchone():
            for code, priority_id in mapping.items():
                if priority_id:
                    cr.execute(f'UPDATE {table} SET priority_id = %s WHERE priority = %s', [priority_id, code])
            # The removed selection column kept NOT NULL; drop it so new rows insert cleanly.
            cr.execute(f'ALTER TABLE {table} DROP COLUMN priority')
        cr.execute(f'UPDATE {table} SET priority_id = %s WHERE priority_id IS NULL', [ids['priority_normal']])
