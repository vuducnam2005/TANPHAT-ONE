# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Idempotent Vietnamese translation & en_US source restoration (F-A02-0004, F-A07-0010, F-A07-0011).

1. Restores original upstream `en_US` labels while keeping `vi_VN` glossary labels on the 7
   menus/actions previously mutated in XML (`mail`, `project_todo`, `calendar`).
2. Preserves `calendar_alarm` Vietnamese translation ('Email - Trước 1 ngày').
3. Safely translates `hr_recruitment` default stages and XML view labels in `vi_VN` JSONB
   when `hr_recruitment` tables exist, without creating any `ir.model.data` owned by `tp_i18n_vi`.
"""

_GLOSSARY_RESTORATIONS = (
    # (module, xmlid_name, expected_model, table_name, en_us, vi_vn)
    ("mail", "menu_root_discuss", "ir.ui.menu", "ir_ui_menu", "Discuss", "Trao đổi"),
    ("mail", "action_discuss", "ir.actions.client", "ir_act_client", "Discuss", "Trao đổi"),
    ("project_todo", "menu_todo_todos", "ir.ui.menu", "ir_ui_menu", "To-do", "Việc cá nhân"),
    (
        "project_todo",
        "project_task_action_todo",
        "ir.actions.act_window",
        "ir_act_window",
        "To-dos",
        "Việc cá nhân",
    ),
    ("calendar", "mail_menu_calendar", "ir.ui.menu", "ir_ui_menu", "Calendar", "Lịch làm việc"),
    (
        "calendar",
        "calendar_event_menu",
        "ir.ui.menu",
        "ir_ui_menu",
        "Calendar",
        "Lịch làm việc",
    ),
    (
        "calendar",
        "action_calendar_event",
        "ir.actions.act_window",
        "ir_act_window",
        "Meetings",
        "Lịch làm việc",
    ),
)

_RECRUITMENT_STAGE_TRANSLATIONS = (
    ("New", "Mới ứng tuyển"),
    ("Initial Qualification", "Sơ loại hồ sơ"),
    ("Qualification", "Sơ loại hồ sơ"),
    ("First Interview", "Phỏng vấn vòng 1"),
    ("Second Interview", "Phỏng vấn vòng 2"),
    ("Contract Proposal", "Đề nghị nhận việc"),
    ("Contract Signed", "Đã ký hợp đồng"),
)

_RECRUITMENT_ARCH_REPLACEMENTS = (
    ('string="Salary Range"', 'string="Khung lương"'),
    ('string="Open Applications"', 'string="Hồ sơ đang mở"'),
    ('string="Expected Degree"', 'string="Trình độ yêu cầu"'),
    ("> new applications<", "> hồ sơ ứng tuyển mới<"),
    (
        'new<br/><span class="text-nowrap">applications</span>',
        'hồ sơ<br/><span class="text-nowrap">ứng tuyển mới</span>',
    ),
    (
        'in<br/><span class="text-nowrap">progress</span>',
        'đang<br/><span class="text-nowrap">xử lý</span>',
    ),
    (
        'to<br/><span class="text-nowrap">recruit</span>',
        'chỉ tiêu<br/><span class="text-nowrap">cần tuyển</span>',
    ),
)

_ALLOWED_TABLES = frozenset({"ir_ui_menu", "ir_act_client", "ir_act_window"})


def _table_exists(cr, table_name):
    cr.execute(
        """
        SELECT 1
          FROM information_schema.tables
         WHERE table_schema = 'public'
           AND table_name = %s
        """,
        (table_name,),
    )
    return cr.fetchone() is not None


def migrate(cr, version):
    if not version:
        return

    # 1. Restore canonical en_US & vi_VN JSONB values on the 7 upstream menus/actions
    for mod, name, expected_model, table_name, en_val, vi_val in _GLOSSARY_RESTORATIONS:
        if table_name not in _ALLOWED_TABLES or not _table_exists(cr, table_name):
            continue
        cr.execute(
            """
            SELECT res_id
              FROM ir_model_data
             WHERE module = %s
               AND name = %s
               AND model = %s
            """,
            (mod, name, expected_model),
        )
        row = cr.fetchone()
        if not row:
            continue
        res_id = row[0]
        cr.execute(
            f"""
            UPDATE {table_name}
               SET name = jsonb_set(
                   jsonb_set(COALESCE(name, '{{}}'::jsonb), '{{en_US}}', to_jsonb(%s::text), true),
                   '{{vi_VN}}',
                   to_jsonb(%s::text),
                   true
               )
             WHERE id = %s
            """,
            (en_val, vi_val, res_id),
        )

    # 2. Keep calendar_alarm 'Email - 1 day' Vietnamese label intact
    if _table_exists(cr, "calendar_alarm"):
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

    # 3. Translate hr_recruitment default stages & XML view strings in vi_VN JSONB (keeping en_US untouched)
    if _table_exists(cr, "hr_recruitment_stage"):
        for en_stage, vi_stage in _RECRUITMENT_STAGE_TRANSLATIONS:
            cr.execute(
                """
                UPDATE hr_recruitment_stage
                   SET name = jsonb_set(name, '{vi_VN}', to_jsonb(%s::text), true)
                 WHERE name IS NOT NULL
                   AND name->>'en_US' = %s
                   AND (name->>'vi_VN' IS NULL OR name->>'vi_VN' = %s)
                """,
                (vi_stage, en_stage, en_stage),
            )

    if _table_exists(cr, "ir_act_window"):
        cr.execute(
            """
            UPDATE ir_act_window a
               SET name = jsonb_set(a.name, '{vi_VN}', to_jsonb(%s::text), true)
              FROM ir_model_data d
             WHERE d.module = 'hr_recruitment'
               AND d.name = 'action_hr_job_new_application'
               AND d.model = 'ir.actions.act_window'
               AND d.res_id = a.id
               AND a.name IS NOT NULL
               AND (a.name->>'vi_VN' IS NULL OR a.name->>'vi_VN' = 'New Application')
            """,
            ("Hồ sơ ứng tuyển mới",),
        )

    if _table_exists(cr, "ir_ui_view"):
        cr.execute(
            """
            SELECT v.id, v.arch_db->>'en_US', v.arch_db->>'vi_VN'
              FROM ir_ui_view v
              JOIN ir_model_data d
                ON d.model = 'ir.ui.view'
               AND d.res_id = v.id
             WHERE d.module = 'hr_recruitment'
               AND v.arch_db IS NOT NULL
            """,
        )
        for view_id, arch_en, arch_vi in cr.fetchall():
            base_vi = arch_vi or arch_en
            if not base_vi:
                continue
            updated_vi = base_vi
            for src_term, dst_term in _RECRUITMENT_ARCH_REPLACEMENTS:
                if src_term in updated_vi:
                    updated_vi = updated_vi.replace(src_term, dst_term)
            if updated_vi != arch_vi and any(src in (arch_en or "") for src, _ in _RECRUITMENT_ARCH_REPLACEMENTS):
                cr.execute(
                    """
                    UPDATE ir_ui_view
                       SET arch_db = jsonb_set(arch_db, '{vi_VN}', to_jsonb(%s::text), true)
                     WHERE id = %s
                    """,
                    (updated_vi, view_id),
                )
