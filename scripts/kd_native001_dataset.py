"""KD synthetic dataset: ORM seed, durable provenance, guarded cleanup.

No cleanup apply on dev. Private credentials/manifests are never printed.
"""

# ruff: noqa: T201, PLC0415, EM101
import argparse
import calendar
import hashlib
import json
import secrets
from collections import Counter
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import kd_native001 as kd

ROOT = Path(__file__).resolve().parents[1]
DATASET = "KD_NATIVE_001_REALISTIC_V1"
NS = "tp_kd_native001_realistic_v1"
TARGETS = {
    "partners": 12,
    "opportunities": 12,
    "projects": 8,
    "contracts": 10,
    "amendments": 0,
    "tasks": 100,
    "allocations": 16,
    "productions": 24,
    "acceptances": 16,
    "payments": 20,
    "plans": 16,
    "credentials": 12,
    "obligations": 8,
}
MODELS = {
    "partners": "res.partner",
    "opportunities": "crm.lead",
    "projects": "project.project",
    "contracts": "tp.contract",
    "tasks": "project.task",
    "allocations": "tp.allocation",
    "productions": "tp.production",
    "acceptances": "tp.acceptance",
    "payments": "tp.payment.request",
    "plans": "tp.periodic.plan",
    "credentials": "tp.credential",
    "obligations": "tp.obligation",
}
PROJECTS = [
    ("ANP", "Tư vấn khảo sát và lập thiết kế tuyến kết nối Khu công nghiệp An Phú"),
    ("HLM", "Khảo sát địa hình, địa chất cầu Hòa Lâm"),
    ("NTH", "Thiết kế cải tạo tuyến đường ven sông Nam Thành"),
    ("DVT", "Khảo sát và thiết kế hạ tầng thoát nước Đông Việt"),
    ("BSN", "Thiết kế bảo đảm an toàn tuyến tỉnh lộ Bình Sơn"),
    ("PLC", "Tư vấn giám sát cầu Phú Lộc"),
    ("THA", "Chuẩn bị thiết kế nút giao Tân Hải"),
    ("HPT", "Nghiên cứu phương án hạ tầng khu dân cư Hòa Phát"),
]
PARTNERS = [
    "Ban quản lý hạ tầng An Phú",
    "Ban chuẩn bị dự án Hòa Lâm",
    "Trung tâm hạ tầng Nam Thành",
    "Đơn vị phát triển đô thị Đông Việt",
    "Ban điều phối giao thông Bình Sơn",
    "Ban xây dựng Phú Lộc",
    "Đơn vị đầu tư hạ tầng Tân Hải",
    "Nhóm phát triển khu dân cư Hòa Phát",
    "Tư vấn khảo sát Minh Lộ",
    "Tư vấn thiết kế Hợp Tuyến",
    "Khảo sát địa chất Sơn Hải",
    "Tư vấn kiểm tra Cầu Đường Việt",
]
TASK_NAMES = [
    "Chuẩn bị và kiểm kê tài liệu đầu vào",
    "Tổ chức khảo sát hiện trường",
    "Lập thiết kế và phối hợp kỹ thuật",
    "Kiểm tra và chuẩn bị bàn giao",
    "Thu thập bình đồ và mốc tọa độ",
    "Lập phương án khảo sát chi tiết",
    "Đo địa hình dọc tuyến",
    "Kiểm tra mặt cắt ngang",
    "Khảo sát vị trí công trình trên tuyến",
    "Tổng hợp kết quả địa chất",
    "Xử lý số liệu và kiểm tra mốc",
    "Lập bản vẽ phương án tuyến",
    "Phối hợp cao độ và thoát nước",
    "Kiểm tra khối lượng dự kiến",
    "Rà soát danh mục bản vẽ",
    "Chuẩn bị danh mục hồ sơ bàn giao",
    "Tổng hợp báo cáo KH-KD tháng",
    "Chuẩn bị nội dung truyền thông được giao",
]


def digest(record):
    """Stored business values, including relation IDs; never serialize credentials."""
    if not record.exists():
        return None
    if record._name == "res.users":
        names = ["name", "login", "active", "company_id", "company_ids", "group_ids"]
    else:
        excluded = {
            "id",
            "create_date",
            "write_date",
            "create_uid",
            "write_uid",
            "password",
            "totp_secret",
        }
        names = [
            name
            for name, field in record._fields.items()
            if field.store
            and name not in excluded
            and not name.startswith(("message_", "activity_", "website_"))
            and field.type not in ("binary", "properties", "properties_definition")
        ]
    values = record.with_context(active_test=False).read(names, load=None)[0]
    for name, value in values.items():
        if isinstance(value, list) and record._fields[name].type in (
            "many2many",
            "one2many",
        ):
            values[name] = sorted(value)
    return hashlib.sha256(
        json.dumps(values, sort_keys=True, default=str, ensure_ascii=False).encode(),
    ).hexdigest()


class Seed:
    def __init__(self, env, target):
        self.env, self.target = env, target
        self.dataset = env["tp.kd.dataset"].search([("name", "=", DATASET)])
        if not self.dataset:
            from odoo import fields

            self.dataset = env["tp.kd.dataset"].create(
                {
                    "name": DATASET,
                    "namespace": NS,
                    "database": env.cr.dbname,
                    "anchor_date": fields.Date.context_today(env["tp.kd.dataset"]),
                },
            )
        if self.dataset.database != env.cr.dbname or self.dataset.namespace != NS:
            raise ValueError("Dataset environment/provenance mismatch")
        self.today = self.dataset.anchor_date
        self.created, self.reused = 0, 0
        self.new_records = set()
        self.folder = kd.BASE / "dataset" / target
        self.folder.mkdir(parents=True, exist_ok=True)
        self.credential_path = self.folder / "credentials.json"
        self.credentials = (
            kd.stabilize.native.read(self.credential_path)
            if self.credential_path.exists()
            else {}
        )

    def entry(self, key):
        return self.env["tp.kd.dataset.entry"].search(
            [("dataset_id", "=", self.dataset.id), ("key", "=", key)],
        )

    def bind(self, key, record, category=None, owned=True):
        existing = self.entry(key)
        if existing:
            if (
                existing.model != record._name
                or existing.res_id != record.id
                or existing.owned != owned
            ):
                raise ValueError("Registry identity changed: " + key)
            return record
        external = self.env.ref(NS + "." + key, raise_if_not_found=False)
        if external and external != record:
            raise ValueError("External ID collision: " + key)
        if not external:
            self.env["ir.model.data"].create(
                {
                    "module": NS,
                    "name": key,
                    "model": record._name,
                    "res_id": record.id,
                    "noupdate": True,
                },
            )
        self.env["tp.kd.dataset.entry"].create(
            {
                "dataset_id": self.dataset.id,
                "key": key,
                "model": record._name,
                "res_id": record.id,
                "external_id": NS + "." + key,
                "owned": owned,
                "category": category or "support",
            },
        )
        return record

    def get(self, key, model, values=None, category=None, factory=None):
        entry = self.entry(key)
        if entry:
            rec = self.env[entry.model].browse(entry.res_id).exists()
            if entry.status != "present" or not rec or entry.model != model:
                raise ValueError(
                    "Missing/tombstoned record: " + key + "; investigate before reseed",
                )
            external = self.env.ref(entry.external_id, raise_if_not_found=False)
            if external != rec:
                raise ValueError("External ID does not match registry: " + key)
            self.reused += 1
            return rec, False
        if self.env.ref(NS + "." + key, raise_if_not_found=False):
            raise ValueError(
                "Unregistered external ID; refusing ownership adoption: " + key,
            )
        record = factory() if factory else self.env[model].create(values)
        self.new_records.add((record._name, record.id))
        self.created += 1
        return self.bind(key, record, category), True

    def grant(self, key, model, values):
        return self.get(key, model, values)[0]

    def transition(self, record, action, actor, **values):
        item = record.with_user(actor)
        result = getattr(item, "action_" + action)()
        wizard = self.env["tp.kd.transition"].with_user(actor).browse(result["res_id"])
        if values:
            wizard.write(values)
        wizard.action_confirm()

    def review_scenario(self, rec, index, editor, reviewer):
        # This method is called ONLY for newly created dossiers, never on rerun.
        if index % 4 == 0:
            return
        self.transition(rec, "submit", editor)
        if index % 4 in (2, 3):
            self.transition(
                rec,
                "return",
                reviewer,
                reason="Bổ sung căn cứ và danh mục đầu ra — tình huống tổng hợp",
            )
        if index % 4 == 3:
            self.transition(
                rec,
                "rework",
                editor,
                reason="Tiếp nhận ý kiến để chuẩn bị lại",
            )
            self.transition(
                rec,
                "submit",
                editor,
                fix_summary="Đã bổ sung kiểm kê nội bộ; chưa xác minh bên ngoài",
            )

    def typed(
        self,
        category,
        key,
        project,
        contract,
        index,
        extra,
        editor,
        reviewer,
        money=None,
    ):
        model = MODELS[category]
        values = {
            "code": key.upper().replace("_", "-"),
            "name": extra.pop("name"),
            "project_id": project.id,
            "contract_id": contract.id if contract else False,
            "owner_id": editor.id,
            "reviewer_id": reviewer.id,
            "date": self.today - timedelta(days=30),
            "date_due": self.today
            + timedelta(days=(-7 if index % 5 == 0 else 3 if index % 5 == 1 else 21)),
            "scope": "Phạm vi quản trị hồ sơ tổng hợp: " + project.name,
            **extra,
        }

        if values.get("date_due") and values["date_due"] < values["date"]:
            values["date_due"] = values["date"] + timedelta(days=3)

        def factory():
            item = self.env[model].with_user(editor).create(values)
            if money is not None:
                payload = money if isinstance(money, list) else [money]
                item.write(
                    {
                        "amount_ids": [(0, 0, line) for line in payload],
                        "version": item.version,
                    },
                )
            self.review_scenario(item, index, editor, reviewer)
            return item.with_env(self.env)

        return self.get(key, model, category=category, factory=factory)[0]

    def run(self):
        from odoo import Command

        env = self.env
        company = self.bind("ref_company", env.company, owned=False)
        currency = self.bind("ref_currency", env.ref("base.VND"), owned=False)
        if not currency.active:
            raise ValueError(
                "VND must already be active; do not change shared currency configuration",
            )
        departments = env["hr.department"].search(
            [("company_id", "=", company.id), ("name", "=", "Kế hoạch Kinh doanh")],
        )
        if len(departments) != 1:
            raise ValueError(
                "Expected one existing KH-KD department; do not guess or duplicate it",
            )
        department = self.bind("ref_department", departments, owned=False)
        partners = [
            self.get(
                f"partner_{i + 1:02}",
                "res.partner",
                {
                    "name": name,
                    "is_company": True,
                    "comment": "Tình huống tổng hợp KD-NATIVE-001; không là thông tin pháp nhân thực tế.",
                },
                "partners",
            )[0]
            for i, name in enumerate(PARTNERS)
        ]
        users = {}
        roles = {
            "editor": "tp_core.group_user,sales_team.group_sale_salesman_all_leads",
            "reviewer": "tp_core.group_user,sales_team.group_sale_salesman_all_leads",
            "metadata": "tp_core.group_user,sales_team.group_sale_salesman_all_leads",
            "planner": "tp_core.group_manager",
        }
        for role, groups in roles.items():
            key = "user_" + role
            entry = self.entry(key)
            if not entry and role not in self.credentials:
                self.credentials[role] = {
                    "login": "kd_native001_" + role,
                    "password": secrets.token_urlsafe(24),
                }
                kd.stabilize.native.write(self.credential_path, self.credentials)
            if role not in self.credentials:
                raise ValueError(
                    "Existing actor credential file is missing; no password reset",
                )
            credential = self.credentials[role]
            if not entry and env["res.users"].with_context(
                active_test=False,
            ).search_count([("login", "=", credential["login"])]):
                raise ValueError(
                    "Login already exists outside dataset; refusing ownership adoption",
                )
            user, _ = self.get(
                key,
                "res.users",
                {
                    "name": {
                        "editor": "KH-KD — lập hồ sơ tổng hợp",
                        "reviewer": "KH-KD — rà soát tổng hợp",
                        "metadata": "KH-KD — hỗ trợ hồ sơ tổng hợp",
                        "planner": "KH-KD — điều phối tổng hợp",
                    }[role],
                    **credential,
                    "company_id": company.id,
                    "company_ids": [Command.set(company.ids)],
                    "group_ids": [
                        Command.set([env.ref(g).id for g in groups.split(",")]),
                    ],
                    "lang": "vi_VN",
                    "tz": "Asia/Ho_Chi_Minh",
                },
            )
            users[role] = user
            self.bind(key + "_partner", user.partner_id)
        projects = []
        for i, (short, name) in enumerate(PROJECTS):
            project, _ = self.get(
                f"project_{i + 1:02}",
                "project.project",
                {
                    "name": name,
                    "tp_code": "KD26-" + short,
                    "tp_managed": True,
                    "company_id": company.id,
                    "partner_id": partners[i].id,
                    "tp_department_id": department.id,
                    "user_id": users["planner"].id,
                    "privacy_visibility": "employees",
                    "kd_scope": "Tình huống tổng hợp khảo sát/thiết kế; hồ sơ đang chuẩn bị, chưa xác nhận ký hoặc hiệu lực.",
                    "kd_deadline": self.today + timedelta(days=45 + i * 7),
                },
                "projects",
            )
            projects.append(project)
            for role, user in users.items():
                self.grant(
                    f"assignment_{i}_{role}",
                    "tp.project.assignment",
                    {
                        "project_id": project.id,
                        "user_id": user.id,
                        "role": "coordinator" if role == "planner" else "reader",
                    },
                )
                domains = [
                    "opportunity",
                    "allocation",
                    "production",
                    "acceptance",
                    "payment",
                    "plan",
                    "credential",
                    "obligation",
                ]
                caps = (
                    ["review"]
                    if role == "reviewer"
                    else ["prepare", "submit"]
                    if role in ("editor", "metadata")
                    else []
                )
                for domain in domains:
                    for cap in caps:
                        self.grant(
                            f"kdgrant_{i}_{role}_{domain}_{cap}",
                            "tp.kd.grant",
                            {
                                "project_id": project.id,
                                "department_id": department.id,
                                "user_id": user.id,
                                "domain": domain,
                                "capability": cap,
                                "reason": "Fixture tổng hợp KD-NATIVE-001; không cấp quyền người thật",
                            },
                        )
                financial = {
                    "editor": [
                        "financial_read",
                        "financial_draft_edit",
                        "contract_draft_edit",
                        "contract_submit",
                    ],
                    "reviewer": ["financial_read", "contract_review_commercial"],
                    "metadata": ["contract_draft_edit"],
                    "planner": [],
                }[role]
                for cap in financial:
                    self.grant(
                        f"grant_{i}_{role}_{cap}",
                        "tp.project.grant",
                        {
                            "project_id": project.id,
                            "user_id": user.id,
                            "department_id": department.id
                            if cap != "financial_read"
                            else False,
                            "capability": cap,
                            "reason": "Fixture tổng hợp; không quyết định Q2/người thật",
                        },
                    )
        contracts, originals = [], []
        for i in range(10):
            p = projects[i if i < 8 else i - 8]
            key = f"contract_{i + 1:02}"
            result = {}

            def factory(i=i, p=p, key=key):
                result.update(
                    env["tp.contract.workflow"]
                    .with_user(users["editor"])
                    ._tp_run(
                        "create_contract",
                        {
                            "project_id": p.id,
                            "code": f"KD26-HD-{i + 1:02}",
                            "name": "Dự thảo " + p.name,
                            "contract_type": "owner",
                            "currency": "VND",
                            "partner_id": p.partner_id.id,
                            "revision": {"name": "Phương án ban đầu — chưa ký"},
                            "lines": [
                                {
                                    "scope_key": "KS-TK",
                                    "name": "Khảo sát và hồ sơ thiết kế",
                                    "amount": {
                                        "state": "unconfirmed"
                                        if i == 7
                                        else "confirmed",
                                        "value": None
                                        if i == 7
                                        else str(
                                            [
                                                350000000,
                                                1200000000,
                                                3200000000,
                                                8500000000,
                                                740000000,
                                                1800000000,
                                                560000000,
                                                0,
                                                960000000,
                                                2100000000,
                                            ][i],
                                        ),
                                        "tax_basis": "unknown"
                                        if i == 7
                                        else "excluding_tax",
                                    },
                                },
                            ],
                        },
                        key=DATASET + ":" + key,
                    ),
                )
                return result["contract"].with_env(env)

            contract, new = self.get(
                key,
                "tp.contract",
                category="contracts",
                factory=factory,
            )
            revision = result.get("revision") or contract.revision_ids.filtered(
                lambda r: r.revision_kind == "original",
            )
            self.bind(key + "_original", revision)
            if new and i in (1, 2, 3, 4, 8):

                def action(name, actor, values):
                    return (
                        env["tp.contract.workflow"]
                        .with_user(actor)
                        ._tp_run(
                            name,
                            {"expected_version": contract.aggregate_version, **values},
                            contract_id=contract.id,
                            revision_id=revision.id,
                            key=DATASET + ":" + key + ":" + name,
                        )
                    )

                action(
                    "submit_review",
                    users["editor"],
                    {"reviewer_id": users["reviewer"].id},
                )
                if i in (2, 3):
                    action(
                        "return_review",
                        users["reviewer"],
                        {"reason": "Bổ sung danh mục phạm vi — tổng hợp", "issues": []},
                    )
                if i == 3:
                    action(
                        "begin_rework",
                        users["editor"],
                        {"reason": "Chuẩn bị bản sửa"},
                    )
            contracts.append(contract)
            originals.append(revision)
        # Twelve opportunities share partners/projects. No legal award is asserted.
        for i in range(12):
            p = projects[i % 8]
            route = "direct" if i % 3 == 0 else "bid"
            key = f"opportunity_{i + 1:02}"

            def factory(i=i, p=p, route=route):
                lead = (
                    env["crm.lead"]
                    .with_user(users["editor"])
                    .create(
                        {
                            "name": (
                                "Chuẩn bị gói "
                                if route == "bid"
                                else "Đề xuất giao trực tiếp "
                            )
                            + p.name,
                            "type": "opportunity",
                            "company_id": company.id,
                            "partner_id": p.partner_id.id,
                            "tp_project_id": p.id,
                            "user_id": users["editor"].id,
                            "kd_route": route,
                            "kd_source": "Tình huống tổng hợp phòng KH-KD",
                            "kd_scope": "Khảo sát/thiết kế và chuẩn bị hồ sơ",
                            "kd_checklist": "Phạm vi; nhân lực; danh mục năng lực; tiến độ dự kiến",
                            "kd_deadline": self.today
                            + timedelta(
                                days=(-7 if i % 4 == 0 else 3 if i % 4 == 1 else 21),
                            ),
                        },
                    )
                )
                if i % 4 != 0:
                    lead.action_kd_prepare()
                if route == "bid" and i % 4 in (2, 3):
                    lead.write(
                        {"kd_receipt": "Khai báo nộp nội bộ tổng hợp, chưa xác minh"},
                    )
                    lead.action_kd_record_submission()
                return lead.with_env(env)

            self.get(key, "crm.lead", category="opportunities", factory=factory)
        tasks = []
        for pi, count in enumerate([18, 18, 18, 14, 12, 8, 6, 6]):
            local = []
            for j in range(count):
                key = f"task_{pi + 1:02}_{j + 1:02}"
                name = TASK_NAMES[j]
                values = {
                    "name": name,
                    "project_id": projects[pi].id,
                    "parent_id": local[j % 4].id if j >= 4 else False,
                    "kd_contract_id": contracts[pi].id,
                    "kd_responsible_id": users["planner"].id,
                    "user_ids": [
                        Command.set([users["planner"].id, users["editor"].id]),
                    ],
                    "date_deadline": self.today
                    + timedelta(
                        days=(-7 if j % 7 == 0 else 3 if j % 7 == 1 else 14 + j),
                    ),
                    "kd_deliverable": "Bộ kết quả: "
                    + name.lower()
                    + " — tình huống tổng hợp",
                    "description": "Nội dung tổng hợp phục vụ quản trị quy trình; không gửi hoặc xuất bản ra ngoài.",
                }
                task = self.get(
                    key,
                    "project.task",
                    category="tasks",
                    factory=lambda values=values: (
                        env["project.task"]
                        .with_user(users["planner"])
                        .create(values)
                        .with_env(env)
                    ),
                )[0]
                local.append(task)
            tasks.append(local)

        def money(index, value):
            return {
                "currency_id": currency.id,
                "amount_state": "unconfirmed" if index % 7 == 0 else "confirmed",
                "value": 0 if index % 7 == 0 else value,
                "tax_basis": "unknown" if index % 7 == 0 else "excluding_tax",
            }

        allocations = [[] for _ in projects]
        index = 0
        for pi, count in enumerate([4, 4, 4, 2, 1, 1, 0, 0]):
            for j in range(count):
                index += 1
                rec = self.typed(
                    "allocations",
                    f"kd26_gk_{index:02}",
                    projects[pi],
                    contracts[pi],
                    index,
                    {
                        "name": ("Khoán nội bộ " if j % 2 == 0 else "Phạm vi thầu phụ ")
                        + PROJECTS[pi][0]
                        + f" đợt{j + 1}",
                        "task_id": tasks[pi][min(j + 4, len(tasks[pi]) - 1)].id,
                        "allocation_kind": "internal" if j % 2 == 0 else "subcontract",
                        "recipient_department_id": department.id
                        if j % 2 == 0
                        else False,
                        "partner_id": partners[8 + (j % 4)].id if j % 2 else False,
                        "parent_id": allocations[pi][0].id if j in (2, 3) else False,
                        "period_from": self.today.replace(day=1) - timedelta(days=31),
                        "period_to": self.today + timedelta(days=30),
                    },
                    users["editor"],
                    users["reviewer"],
                    money(index, [1200000000, 580000000, 350000000, 470000000][j % 4]),
                )
                allocations[pi].append(rec)
        productions = [[] for _ in projects]
        index = 0
        for pi, count in enumerate([6, 6, 6, 4, 2, 0, 0, 0]):
            for j in range(count):
                index += 1
                start = (
                    self.today.replace(day=1) - timedelta(days=31)
                    if j < 2
                    else self.today.replace(day=1)
                )
                start = start.replace(day=1)
                end = start.replace(day=calendar.monthrange(start.year, start.month)[1])
                rec = self.typed(
                    "productions",
                    f"kd26_sl_{index:02}",
                    projects[pi],
                    contracts[pi],
                    index,
                    {
                        "name": f"Kết quả {PROJECTS[pi][0]} kỳ{start.month} đợt{j + 1}",
                        "allocation_id": allocations[pi][j % len(allocations[pi])].id,
                        "task_id": tasks[pi][min(j + 4, len(tasks[pi]) - 1)].id,
                        "date": start,
                        "period_from": start,
                        "period_to": end,
                        "quantity": 2.5 + j,
                        "unit": "km",
                        "completion_percent": min(100, 25 + j * 12),
                        "reconciliation_state": "needs_evidence"
                        if j % 3 == 1
                        else "unreconciled",
                    },
                    users["editor"],
                    users["reviewer"],
                    money(index, 85000000 + j * 35000000),
                )
                productions[pi].append(rec)
        acceptances = [[] for _ in projects]
        index = 0
        for pi, count in enumerate([4, 4, 4, 3, 1, 0, 0, 0]):
            for j in range(count):
                index += 1
                source = productions[pi][j]
                rec = self.typed(
                    "acceptances",
                    f"kd26_nt_{index:02}",
                    projects[pi],
                    contracts[pi],
                    index,
                    {
                        "name": f"Hồ sơ nghiệm thu {PROJECTS[pi][0]} đợt{j + 1}",
                        "date": source.date + timedelta(days=2),
                        "production_id": source.id,
                        "round_code": f"Đợt{j + 1}",
                        "counterparty_id": projects[pi].partner_id.id,
                        "quantity": source.quantity / 2,
                        "unit": source.unit,
                        "period_from": source.period_from,
                        "period_to": source.period_to,
                        "evidence_checklist": "Danh mục khối lượng và bản vẽ; còn thiếu biên bản ngoài — chưa xác minh",
                    },
                    users["editor"],
                    users["reviewer"],
                    money(index, 42500000 + j * 17500000),
                )
                acceptances[pi].append(rec)
        index = 0
        for pi, count in enumerate([5, 5, 5, 3, 1, 1, 0, 0]):
            for j in range(count):
                index += 1
                advance = j == 0
                self.typed(
                    "payments",
                    f"kd26_tt_{index:02}",
                    projects[pi],
                    contracts[pi],
                    index,
                    {
                        "name": ("Đề nghị tạm ứng " if advance else "Đề nghị theo đợt ")
                        + PROJECTS[pi][0]
                        + f" lần{j + 1}",
                        "direction": "receipt" if j % 3 else "disbursement",
                        "date": self.today - timedelta(days=30)
                        if advance
                        else acceptances[pi][(j - 1) % len(acceptances[pi])].date,
                        "payment_basis": "advance" if advance else "acceptance",
                        "acceptance_id": False
                        if advance
                        else acceptances[pi][(j - 1) % len(acceptances[pi])].id,
                        "partner_id": projects[pi].partner_id.id,
                        "advance_basis": "Điều khoản tạm ứng dự kiến trong dự thảo, chưa hiệu lực"
                        if advance
                        else False,
                        "document_checklist": "Kiểm kê hồ sơ đề nghị, chưa phải hóa đơn ghi sổ hoặc tiền đã trả",
                        "reconciliation_state": "missing_documents"
                        if j % 2
                        else "pending",
                    },
                    users["editor"],
                    users["reviewer"],
                    money(index, 135000000 + j * 45000000),
                )
        year = self.today.year
        periods = (
            [("month", m, m) for m in range(1, 13)]
            + [("quarter", m, m + 2) for m in (1, 4, 10)]
            + [("year", 1, 12)]
        )
        for i, (kind, first, last) in enumerate(periods):
            self.typed(
                "plans",
                f"kd26_kh_{i + 1:02}",
                projects[0],
                False,
                i,
                {
                    "name": f"Kế hoạch {kind} {first:02}-{last:02}/{year} — An Phú",
                    "period_kind": kind,
                    "period_from": self.today.replace(month=first, day=1),
                    "period_to": self.today.replace(
                        month=last,
                        day=calendar.monthrange(year, last)[1],
                    ),
                },
                users["editor"],
                users["reviewer"],
                [
                    dict(
                        money(i, 350000000 + (i % 4) * 150000000),
                        measure="production",
                    ),
                    dict(
                        money(i + 1, 450000000 + (i % 4) * 180000000),
                        measure="revenue",
                    ),
                ],
            )
        for i in range(12):
            pi = i % 8
            new_credential = not self.entry(f"kd26_nl_{i + 1:02}")
            rec = self.typed(
                "credentials",
                f"kd26_nl_{i + 1:02}",
                projects[pi],
                False,
                i,
                {
                    "name": [
                        "Năng lực khảo sát địa hình",
                        "Danh mục năng lực thiết kế cầu",
                        "Hồ sơ năng lực giám sát",
                        "Năng lực khảo sát địa chất",
                    ][i % 4]
                    + " — "
                    + PROJECTS[pi][0],
                    "subject_kind": "organization",
                    "subject_id": partners[8 + i % 4].id,
                    "credential_kind": ["Khảo sát", "Thiết kế", "Giám sát", "Địa chất"][
                        i % 4
                    ],
                    "valid_from": self.today - timedelta(days=400),
                    "valid_to": self.today
                    + timedelta(days=(-7 if i % 4 == 0 else 30 if i % 4 == 1 else 180)),
                    "source_note": "Danh mục tổng hợp để quản trị thời hạn; không phát hành hoặc xác minh chứng chỉ pháp lý",
                },
                users["editor"],
                users["reviewer"],
            )
            lead = env.ref(NS + f".opportunity_{pi + 1:02}")
            # New linkage only; never rebuild/overwrite existing user edits on rerun.
            if new_credential:
                lead.with_user(users["editor"]).write(
                    {"kd_credential_ids": [Command.link(rec.id)]},
                )
        for i, p in enumerate(projects):
            self.typed(
                "obligations",
                f"kd26_nv_{i + 1:02}",
                p,
                contracts[i],
                i,
                {
                    "name": "Theo dõi danh mục hồ sơ còn thiếu — " + PROJECTS[i][0],
                    "obligation_kind": [
                        "contract_docs",
                        "retention",
                        "warranty",
                        "reconciliation",
                    ][i % 4],
                    "document_checklist": "Còn thiếu: căn cứ đối chiếu; danh mục bản vẽ; biên bản ngoài nếu áp dụng. Chưa xác nhận hết nghĩa vụ.",
                    "checklist_update_reason": "Khởi tạo checklist tổng hợp",
                    "checklist_status": "collecting" if i % 2 else "missing",
                },
                users["editor"],
                users["reviewer"],
            )
        self.register_support(projects, contracts, users)
        env.flush_all()
        for entry in self.dataset.entry_ids.filtered(
            lambda e: e.owned and not e.checksum,
        ):
            entry.checksum = digest(env[entry.model].browse(entry.res_id))
        return {
            "created": self.created,
            "reused": self.reused,
            "users": {k: v.id for k, v in users.items()},
        }

    def register_support(self, projects, contracts, users):
        env = self.env
        new_contracts = [c.id for c in contracts if (c._name, c.id) in self.new_records]
        for rec in env["tp.contract.idempotency"].search(
            [
                ("result_contract_id", "in", new_contracts),
                ("key", "=like", DATASET + ":%"),
            ],
        ):
            self.bind("support_idempotency_" + str(rec.id), rec)
        new_tasks = [rid for model, rid in self.new_records if model == "project.task"]
        for rec in env["project.task.stage.personal"].search(
            [("task_id", "in", new_tasks)],
        ):
            self.bind("support_task_personal_" + str(rec.id), rec)
        for rec in env["mail.followers"].search(
            [("res_model", "=", "project.task"), ("res_id", "in", new_tasks)],
        ):
            self.bind("support_task_follower_" + str(rec.id), rec)
        for model in (
            "tp.contract.revision",
            "tp.contract.line",
            "tp.contract.line.amount",
            "tp.contract.submission",
            "tp.contract.submission.amount",
            "tp.contract.audit",
            "tp.contract.outbox",
        ):
            if model not in env:
                continue
            fields = env[model]._fields
            if "contract_id" not in fields:
                continue
            for rec in env[model].search(
                [
                    (
                        "contract_id",
                        "in",
                        [
                            c.id
                            for c in contracts
                            if (c._name, c.id) in self.new_records
                        ],
                    ),
                ],
            ):
                if not env["tp.kd.dataset.entry"].search_count(
                    [
                        ("dataset_id", "=", self.dataset.id),
                        ("model", "=", model),
                        ("res_id", "=", rec.id),
                    ],
                ):
                    self.bind(
                        "support_" + model.replace(".", "_") + "_" + str(rec.id),
                        rec,
                    )
        for category in (
            "allocations",
            "productions",
            "acceptances",
            "payments",
            "plans",
            "credentials",
            "obligations",
        ):
            model = MODELS[category]
            ids = self.dataset.entry_ids.filtered(
                lambda e: (
                    e.category == category and (e.model, e.res_id) in self.new_records
                ),
            ).mapped("res_id")
            for suffix, field in (("amount", "record_id"), ("event", "record_id")):
                child = model + "." + suffix
                if child not in env:
                    continue
                records = env[child].search([(field, "in", ids)])
                for rec in records:
                    self.bind(
                        "support_" + child.replace(".", "_") + "_" + str(rec.id),
                        rec,
                    )
                    if suffix == "event" and "amount_ids" in rec._fields:
                        for amount in rec.amount_ids:
                            self.bind(
                                "support_"
                                + amount._name.replace(".", "_")
                                + "_"
                                + str(amount.id),
                                amount,
                            )


def inventory(env):
    dataset = env["tp.kd.dataset"].search([("name", "=", DATASET)])
    if not dataset or dataset.database != env.cr.dbname:
        raise ValueError("Dataset missing or wrong database")
    rows = []
    for entry in dataset.entry_ids.sorted("key"):
        rec = (
            env[entry.model]
            .with_context(active_test=False)
            .browse(entry.res_id)
            .exists()
        )
        external = env.ref(entry.external_id, raise_if_not_found=False)
        current = digest(rec) if rec and entry.owned else None
        dependencies = []
        if rec:
            for name, field in rec._fields.items():
                if (
                    field.store
                    and field.type == "many2one"
                    and name not in ("create_uid", "write_uid")
                    and rec[name]
                ):
                    dependencies.append(
                        {"field": name, "model": field.comodel_name, "id": rec[name].id},
                    )
        rows.append(
            {
                "key": entry.key,
                "model": entry.model,
                "id": entry.res_id,
                "external_id": entry.external_id,
                "owned": entry.owned,
                "category": entry.category,
                "status": entry.status,
                "exists": bool(rec),
                "external_match": bool(rec and external == rec),
                "checksum": entry.checksum,
                "current_checksum": current,
                "drift": bool(entry.owned and rec and entry.checksum != current),
                "dependencies": dependencies,
                "code": rec["code"]
                if rec and "code" in rec._fields
                else rec.tp_code
                if rec and entry.model == "project.project"
                else None,
            },
        )
    counts = Counter(
        r["category"]
        for r in rows
        if r["owned"]
        and r["exists"]
        and r["status"] == "present"
        and r["category"] != "support"
    )
    return {
        "dataset": DATASET,
        "database": env.cr.dbname,
        "anchor_date": str(dataset.anchor_date),
        "counts": dict(counts),
        "total": sum(counts.values()),
        "missing_amendments": 6,
        "amendment_gate": "User chose254 on workflow create_amendment open-revision guard; no legal state fabricated",
        "rows": rows,
    }


def verify(env):
    result = inventory(env)
    expected = {k: v for k, v in TARGETS.items() if v}
    if result["counts"] != expected or result["total"] != 254:
        raise ValueError("Business counts differ from approved254 structure")
    if any(
        not row["external_match"]
        for row in result["rows"]
        if row["status"] == "present"
    ):
        raise ValueError("Registry/externalID mismatch")

    def ids(cat):
        return [r["id"] for r in result["rows"] if r["category"] == cat]

    projects = env["project.project"].browse(ids("projects"))
    for model in [
        "tp.allocation",
        "tp.production",
        "tp.acceptance",
        "tp.payment.request",
        "tp.periodic.plan",
        "tp.credential",
        "tp.obligation",
    ]:
        records = env[model].search([("project_id", "in", projects.ids)])
        records._kd_check_integrity()
        records._kd_validate_sources()
    for project in projects[:3]:
        for model in [
            "crm.lead",
            "tp.contract",
            "project.task",
            "tp.allocation",
            "tp.production",
            "tp.acceptance",
            "tp.payment.request",
            "tp.obligation",
        ]:
            field = "tp_project_id" if model == "crm.lead" else "project_id"
            if not env[model].search_count([(field, "=", project.id)]):
                raise ValueError("Incomplete linked chain: " + model)
    if env["tp.contract.revision"].search_count(
        [
            ("contract_id", "in", ids("contracts")),
            ("effectivity_status", "!=", "not_effective"),
        ],
    ):
        raise ValueError("Unexpected legal effectivity")
    result["verified"] = True
    return result


def export_fixture(env, target):
    users = {
        role: env.ref(NS + ".user_" + role)
        for role in ("editor", "reviewer", "metadata", "planner")
    }
    actions = {
        key: env.ref("tp_kd_workspace.action_" + key).id
        for key in (
            "overview",
            "projects",
            "opportunities",
            "tasks",
            "allocations",
            "productions",
            "acceptances",
            "payments",
            "plans",
            "credentials",
            "obligations",
        )
    }
    projects = [env.ref(NS + f".project_{i:02}") for i in range(1, 9)]
    actions["contracts"] = env.ref("tp_contract.action_tp_contracts").id
    fixture = {
        "database": env.cr.dbname,
        "port": 18069 if target == "dev" else kd.PORT,
        "dataset": DATASET,
        "users": {k: v.id for k, v in users.items()},
        "actor_names": {k: v.name for k, v in users.items()},
        "actions": actions,
        "projects": [{"id": p.id, "name": p.name, "code": p.tp_code} for p in projects],
        "contract": {
            "id": env.ref(NS + ".contract_01").id,
            "name": env.ref(NS + ".contract_01").name,
        },
        "partner_name": projects[0].partner_id.name,
        "department_name": projects[0].tp_department_id.name,
        "company_name": projects[0].company_id.name,
        "production_name": env.ref(NS + ".kd26_sl_01").name,
    }
    kd.stabilize.native.write(kd.BASE / "dataset" / target / "fixture.json", fixture)


class RollbackProbe(Exception):
    """Intentionally roll back the rehearsal; never clean the retained dataset."""


def rehearsal(env, target):
    if target != "clone" or env.cr.dbname != kd.DATABASE:
        raise ValueError("Rehearsal may only run on the owned clone")
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    for name, attempted_target, confirmation in (
        ("cleanup_refuses_dev", "dev", env.cr.dbname + ":" + DATASET),
        ("cleanup_refuses_wrong_confirmation", "clone", "wrong:dataset"),
    ):
        try:
            cleanup_apply(env, attempted_target, confirmation)
        except ValueError:
            checks.append(name)
        else:
            raise AssertionError(name)

    baseline = kd.stabilize.native.backup.table_inventory(env.cr._cnx)
    plan = cleanup_plan(env)
    check(
        "dry_run_does_not_write",
        baseline == kd.stabilize.native.backup.table_inventory(env.cr._cnx),
    )
    users = [
        env.ref(NS + ".user_" + r).id
        for r in ("editor", "reviewer", "metadata", "planner")
    ]
    env.cr.execute(
        "SELECT id,password FROM res_users WHERE id=ANY(%s) ORDER BY id", (users,),
    )
    passwords = env.cr.fetchall()
    try:
        with env.cr.savepoint():
            task = env.ref(NS + ".task_08_06").with_user(env.ref(NS + ".user_planner"))
            task.write({"kd_deliverable": "Sửa sau seed phải được giữ nguyên"})
            expected = digest(task)
            second = Seed(env, target).run()
            check("reseed_creates_zero", second["created"] == 0)
            check(
                "reseed_preserves_user_edit",
                task.kd_deliverable == "Sửa sau seed phải được giữ nguyên"
                and digest(task) == expected,
            )
            env.cr.execute(
                "SELECT id,password FROM res_users WHERE id=ANY(%s) ORDER BY id",
                (users,),
            )
            check("reseed_preserves_password_hashes", passwords == env.cr.fetchall())
            check(
                "drift_reported",
                any(
                    r["drift"] and r["key"] == "task_08_06"
                    for r in inventory(env)["rows"]
                ),
            )
            # A draft with no ownership record is never adopted by cleanup.
            candidates = [r for r in plan["cleanup"] if r["action"] == "unlink_draft"]
            check("draft_cleanup_candidates_exist", bool(candidates))
            victim = candidates[0]
            attachment = env["ir.attachment"].create(
                {
                    "name": "External reference ownership probe",
                    "res_model": victim["model"],
                    "res_id": victim["id"],
                },
            )
            guarded = cleanup_plan(env)
            guarded_row = next(
                r
                for r in guarded["cleanup"]
                if r["model"] == victim["model"] and r["id"] == victim["id"]
            )
            check(
                "external_reference_blocks_related_cleanup",
                guarded_row["action"] == "retained",
            )
            result = cleanup_apply(env, target, env.cr.dbname + ":" + DATASET)
            check(
                "apply_unlinks_only_owned_drafts",
                bool(result["unlinked"])
                and all(r["action"] == "unlink_draft" for r in result["unlinked"]),
            )
            check(
                "apply_retains_history_and_references",
                bool(result["retained"])
                and attachment.exists()
                and env[victim["model"]].browse(victim["id"]).exists(),
            )
            check(
                "referenced_department_is_preserved",
                env.ref(NS + ".ref_department").exists(),
            )
            counts = {
                k: len(result[k])
                for k in ("unlinked", "archived", "retained", "referenced")
            }
            raise RollbackProbe  # noqa: TRY301 - intentionally roll back the complete rehearsal savepoint.
    except RollbackProbe:
        env.invalidate_all()
    check(
        "rehearsal_rollback_preserves_all_rowsets",
        baseline == kd.stabilize.native.backup.table_inventory(env.cr._cnx),
    )
    result = {
        "database": env.cr.dbname,
        "dataset": DATASET,
        "checks": checks,
        "cleanup_simulation": counts,
        "rolled_back": True,
        "persistent_dataset_total": verify(env)["total"],
    }
    return result


def incoming_references(env, owned):
    """Inspect stored ORM relationships, including generic attachment/message links."""
    by_model = {}
    for model, rid in owned:
        by_model.setdefault(model, set()).add(rid)
    incoming = {key: [] for key in owned}
    for model_name in sorted(env.registry.models):
        model = env[model_name].with_context(active_test=False)
        if (
            model._abstract
            or model._transient
            or not model._auto
            or model_name.startswith("tp.kd.dataset")
        ):
            continue
        for name, field in model._fields.items():
            if not field.store or name in ("create_uid", "write_uid"):
                continue
            if (
                field.type not in ("many2one", "many2many")
                or field.comodel_name not in by_model
            ):
                continue
            for source in model.search(
                [(name, "in", sorted(by_model[field.comodel_name]))],
            ):
                for target in source[name]:
                    key = (target._name, target.id)
                    if key in incoming:
                        incoming[key].append(
                            {
                                "model": model_name,
                                "id": source.id,
                                "field": name,
                                "external": (model_name, source.id) not in owned,
                            },
                        )
        # Generic record references have no FK. Ignore only this dataset's own XML IDs.
        pair = (
            ("res_model", "res_id")
            if "res_model" in model._fields and "res_id" in model._fields
            else ("model", "res_id")
            if "model" in model._fields and "res_id" in model._fields
            else None
        )
        if (
            pair
            and model._fields[pair[0]].type == "char"
            and model._fields[pair[1]].type == "integer"
        ):
            for target_model, ids in by_model.items():
                for source in model.search(
                    [(pair[0], "=", target_model), (pair[1], "in", sorted(ids))],
                ):
                    if model_name == "ir.model.data" and source.module == NS:
                        continue
                    key = (target_model, source[pair[1]])
                    incoming[key].append(
                        {
                            "model": model_name,
                            "id": source.id,
                            "field": ",".join(pair),
                            "external": (model_name, source.id) not in owned,
                        },
                    )
        for name, field in model._fields.items():
            if field.store and field.type == "reference":
                refs = [f"{m},{rid}" for m, rid in owned]
                for source in model.search([(name, "in", refs)]):
                    target = source[name]
                    key = (target._name, target.id)
                    if key in incoming:
                        incoming[key].append(
                            {
                                "model": model_name,
                                "id": source.id,
                                "field": name,
                                "external": (model_name, source.id) not in owned,
                            },
                        )
            if field.store and field.type == "many2one_reference":
                model_field = field.model_field
                for target_model, ids in by_model.items():
                    for source in model.search(
                        [(model_field, "=", target_model), (name, "in", sorted(ids))],
                    ):
                        if model_name == "ir.model.data" and source.module == NS:
                            continue
                        key = (target_model, source[name])
                        incoming[key].append(
                            {
                                "model": model_name,
                                "id": source.id,
                                "field": name,
                                "external": (model_name, source.id) not in owned,
                            },
                        )
    return incoming


def cleanup_plan(env):
    result = inventory(env)
    owned = {
        (r["model"], r["id"]): r for r in result["rows"] if r["owned"] and r["exists"]
    }
    incoming = incoming_references(env, owned)
    candidates = set()
    reasons = {}
    for key, row in owned.items():
        record = env[key[0]].browse(key[1])
        if row["drift"]:
            reasons[key] = "changed_since_seed"
        elif row["category"] == "support" or row["category"] in (
            "contracts",
            "projects",
            "partners",
        ):
            reasons[key] = "retain_support_identity_and_audit_or_upstream_master"
        elif "event_ids" in record._fields and record.event_ids:
            reasons[key] = "retain_review_or_checklist_history_no_archive_semantics"
        elif key[0] == "project.task" and record.is_closed:
            reasons[key] = "retain_closed_task"
        elif (
            "state" in record._fields
            and key[0] != "project.task"
            and record.state != "draft"
        ):
            reasons[key] = "retain_non_draft"
        elif key[0] == "crm.lead" and (
            record.kd_bid_state != "identified" or record.sudo().kd_credential_link_ids
        ):
            reasons[key] = "retain_bid_progress_or_credential_links"
        else:
            candidates.add(key)
    changed = True

    def blockers_for(key):
        blockers = []
        for ref in incoming[key]:
            source_key = (ref["model"], ref["id"])
            # Current amount lines are owned children deleted by the parent's
            # existing ORM unlink/ondelete policy; event snapshots are retained.
            if (
                cascade_child(key, ref)
                and source_key in owned
                and not owned[source_key]["drift"]
            ):
                continue
            if source_key not in candidates:
                blockers.append(ref)
        return blockers

    while changed:
        changed = False
        for key in list(candidates):
            blockers = blockers_for(key)
            if blockers:
                candidates.remove(key)
                reasons[key] = "external_or_retained_dependency"
                changed = True
    result["cleanup"] = [
        {
            "model": key[0],
            "id": key[1],
            "key": row["key"],
            "action": "unlink_draft" if key in candidates else "retained",
            "reason": reasons.get(key, "draft_without_history_or_external_dependency"),
            "incoming": incoming[key],
        }
        for key, row in owned.items()
    ]
    result["cleanup_counts"] = dict(Counter(row["action"] for row in result["cleanup"]))
    return result


def cascade_child(key, ref):
    return (
        (ref["model"] == key[0] + ".amount" and ref["field"] == "record_id")
        or (
            key[0] == "project.task"
            and ref["model"] == "project.task.stage.personal"
            and ref["field"] == "task_id"
        )
        or (
            key[0] == "project.task"
            and ref["model"] == "mail.followers"
            and ref["field"] in ("res_id", "res_model,res_id")
        )
    )


def cleanup_apply(env, target, confirmation):
    if target != "clone" or env.cr.dbname != kd.DATABASE:
        raise ValueError(
            "Cleanup apply is forbidden on dev in KD-NATIVE-001; separate future authorization required",
        )
    if confirmation != env.cr.dbname + ":" + DATASET:
        raise ValueError("Exact database:dataset confirmation is required")
    result = cleanup_plan(env)
    pending = {
        (r["model"], r["id"]): r
        for r in result["cleanup"]
        if r["action"] == "unlink_draft"
    }
    deleted = []
    retained = []
    checksums = {(r["model"], r["id"]): r["checksum"] for r in result["rows"]}
    # Delete leaves first. Recheck current relationships/checksum; never disable constraints.
    while pending:
        progressed = False
        owned = {
            (r["model"], r["id"])
            for r in result["rows"]
            if r["owned"] and env[r["model"]].browse(r["id"]).exists()
        }
        incoming = incoming_references(env, owned)
        for key, row in list(pending.items()):
            record = env[key[0]].browse(key[1]).exists()
            if not record:
                pending.pop(key)
                continue
            refs = [
                ref
                for ref in incoming.get(key, [])
                if env[ref["model"]].browse(ref["id"]).exists()
                and not (
                    cascade_child(key, ref)
                    and (ref["model"], ref["id"]) in owned
                    and digest(env[ref["model"]].browse(ref["id"]))
                    == checksums[ref["model"], ref["id"]]
                )
            ]
            if refs:
                continue
            if digest(record) != checksums[key]:
                retained.append(
                    dict(row, reason="changed_during_cleanup_or_child_removal"),
                )
                pending.pop(key)
                progressed = True
                continue
            try:
                with env.cr.savepoint():
                    actor = (
                        record.owner_id
                        if "owner_id" in record._fields
                        else env.ref(NS + ".user_planner")
                        if record._name == "project.task"
                        else env.user
                    )
                    record.with_user(actor).unlink()
                    entry = env["tp.kd.dataset.entry"].search(
                        [
                            ("dataset_id.name", "=", DATASET),
                            ("model", "=", key[0]),
                            ("res_id", "=", key[1]),
                        ],
                    )
                    entry.write({"status": "unlinked"})
            except Exception as exc:  # noqa: BLE001 - retain on any ORM policy or database race failure.
                # Model policy or an incoming race wins. Do not weaken it to clear the dataset.
                retained.append(
                    dict(
                        row,
                        reason="model_policy_or_new_dependency:" + type(exc).__name__,
                    ),
                )
            else:
                deleted.append(row)
            pending.pop(key)
            progressed = True
        if not progressed:
            retained.extend(
                dict(row, reason="dependency_cycle_or_retained_record")
                for row in pending.values()
            )
            break
    for entry in env["tp.kd.dataset.entry"].search(
        [
            ("dataset_id.name", "=", DATASET),
            ("owned", "=", True),
            ("status", "=", "present"),
        ],
    ):
        if not env[entry.model].browse(entry.res_id).exists():
            entry.status = "unlinked"
    return {
        "dataset": DATASET,
        "database": env.cr.dbname,
        "unlinked": deleted,
        "archived": [],
        "retained": retained
        + [row for row in result["cleanup"] if row["action"] == "retained"],
        "referenced": [row for row in result["rows"] if not row["owned"]],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["seed", "inventory", "verify", "cleanup", "rehearsal"],
    )
    parser.add_argument("--target", choices=["clone", "dev"], required=True)
    parser.add_argument("--dataset", required=True, choices=[DATASET])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    kd.bind()

    def run(env):
        env = env(
            context=dict(
                env.context,
                tracking_disable=True,
                mail_create_nolog=True,
                mail_notrack=True,
                crm_iap_enrich_force=False,
            ),
        )
        folder = kd.BASE / "dataset" / args.target
        folder.mkdir(parents=True, exist_ok=True)
        if args.command == "rehearsal":
            result = rehearsal(env, args.target)
            kd.stabilize.native.write(folder / "rehearsal.json", result)
            print(json.dumps(result, ensure_ascii=False, default=str))
            return
        if args.command == "seed":
            before = env["mail.mail"].search([]).ids
            # A seed must not create queued external mail, even if notifications change upstream.
            with patch(
                "odoo.addons.base.models.ir_mail_server.IrMail_Server.send_email",
                side_effect=RuntimeError("External mail forbidden in dataset seed"),
            ):
                summary = Seed(env, args.target).run()
            if env["mail.mail"].search([("id", "not in", before)]):
                raise ValueError(
                    "Seed created external mail queue; transaction refused",
                )
            result = verify(env)
            env.cr.commit()
            result["seed"] = summary
        elif args.command == "cleanup":
            if args.apply:
                result = cleanup_apply(env, args.target, args.confirm)
                env.cr.commit()
            else:
                result = cleanup_plan(env)
            kd.stabilize.native.write(folder / "cleanup-last.json", result)
            print(
                json.dumps(
                    {
                        "dataset": DATASET,
                        "database": env.cr.dbname,
                        "apply": args.apply,
                        "counts": {
                            k: len(result[k])
                            for k in ("unlinked", "archived", "retained", "referenced")
                        }
                        if args.apply
                        else result["cleanup_counts"],
                    },
                    ensure_ascii=False,
                ),
            )
            return
        else:
            result = verify(env) if args.command == "verify" else inventory(env)
        kd.stabilize.native.write(folder / "manifest.json", result)
        export_fixture(env, args.target)
        print(
            json.dumps(
                {k: v for k, v in result.items() if k != "rows"},
                ensure_ascii=False,
                default=str,
            ),
        )

    kd.stabilize.native.orm(args.target, run)


if __name__ == "__main__":
    main()
