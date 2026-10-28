def migrate(cr, version):
    """Scope existing contracts to their project lead department (CTR-002a).

    Contracts of projects without a lead department stay unscoped; workflow
    actions on them answer scope_incomplete until the project gets one.
    """
    cr.execute("""
        UPDATE tp_contract AS contract
           SET department_id = project.tp_department_id
          FROM project_project AS project
         WHERE project.id = contract.project_id
           AND contract.department_id IS NULL
           AND project.tp_department_id IS NOT NULL
    """)
