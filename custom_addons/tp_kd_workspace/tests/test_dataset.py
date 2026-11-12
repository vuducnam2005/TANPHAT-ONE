from odoo.exceptions import AccessError
from odoo.tests import tagged

from .test_workspace import TestKdWorkspace


@tagged("post_install", "-at_install")
class TestDataset(TestKdWorkspace):
    def test_dataset_registry_operator_only(self):
        dataset = self.env["tp.kd.dataset"].create(
            {
                "name": "KD_UNIT",
                "namespace": "tp_kd_unit",
                "database": self.env.cr.dbname,
                "anchor_date": "2026-11-06",
            },
        )
        entry = self.env["tp.kd.dataset.entry"].create(
            {
                "dataset_id": dataset.id,
                "key": "referenced",
                "model": "project.project",
                "res_id": self.project.id,
                "external_id": "tp_kd_unit.referenced",
                "owned": False,
            },
        )
        for record in (dataset, entry):
            with self.assertRaises(AccessError):
                record.with_user(self.reader).read(["id"])
            with self.assertRaises(AccessError):
                record.unlink()
        with self.assertRaises(AccessError):
            entry.write({"owned": True})
        with self.assertRaises(AccessError):
            dataset.with_user(self.reader).create(
                {
                    "name": "FORGE",
                    "namespace": "forged",
                    "database": self.env.cr.dbname,
                    "anchor_date": "2026-11-06",
                },
            )
