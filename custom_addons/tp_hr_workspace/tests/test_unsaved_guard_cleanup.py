# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
from odoo.tests import tagged

from .test_hr_workspace import BaseHrWorkspace


@tagged("post_install", "-at_install")
class TestUnsavedGuardCleanup(BaseHrWorkspace):
    """T-0001 (F-0002): Verify idempotent cleanup only deletes empty AUDIT_UNSAVED_TEST orphans."""

    def test_cleanup_removes_only_empty_audit_orphans(self):
        Employee = self.env["hr.employee"].sudo()
        orphan_1 = Employee.create({"name": "AUDIT_UNSAVED_TEST", "company_id": self.company.id})
        orphan_2 = Employee.create({"name": "AUDIT_UNSAVED_TEST_2", "company_id": self.company.id})
        real_emp = Employee.create({
            "name": "AUDIT_UNSAVED_TEST",
            "company_id": self.company.id,
            "department_id": self.department.id,
        })
        normal_emp = Employee.create({"name": "Nguyễn Văn Thật", "company_id": self.company.id})

        removed = Employee._tp_cleanup_audit_unsaved_orphans()
        self.assertEqual(len(removed), 2)
        self.assertFalse(orphan_1.exists())
        self.assertFalse(orphan_2.exists())
        self.assertTrue(real_emp.exists(), "Employee with department must never be deleted")
        self.assertTrue(normal_emp.exists(), "Normal employee must never be deleted")

        # Idempotent second run
        self.assertEqual(Employee._tp_cleanup_audit_unsaved_orphans(), [])
