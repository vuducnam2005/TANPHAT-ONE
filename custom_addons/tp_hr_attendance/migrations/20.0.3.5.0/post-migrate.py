"""CHG-20261119-029 (20.0.3.5.0): ENTI-ATTENDANCE-002.

The ENTI cron now keeps polling "today" for about a minute per run and re-arms itself; give it a lower
priority than the default (5) so other scheduled jobs on the single cron thread always run first.
No attendance data is rewritten here; the first sync only stores the change fingerprint of unchanged days.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        UPDATE ir_cron SET priority = 10
         WHERE id = (SELECT res_id FROM ir_model_data
                      WHERE module = 'tp_hr_attendance' AND name = 'ir_cron_enti_attendance_sync' AND model = 'ir.cron')
           AND priority = 5
    """)
