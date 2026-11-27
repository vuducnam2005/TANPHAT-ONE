# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Fill missing Vietnamese translation for standard calendar_alarm 'Email - 1 day' (T-0016 / F-0025)."""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        UPDATE calendar_alarm
           SET name = jsonb_set(name, '{vi_VN}', to_jsonb(%s::text), true)
         WHERE name IS NOT NULL
           AND name->>'en_US' = 'Email - 1 day'
           AND (name->>'vi_VN' IS NULL OR name->>'vi_VN' = 'Email - 1 day')
        """,
        ("Email - Trước 1 ngày",),
    )
