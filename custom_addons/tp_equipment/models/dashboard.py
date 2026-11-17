"""Admin-only current equipment snapshot; every drill-down reuses its source domain."""
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .common import ASSET_CLASS, TECH_STATE, check_admin
from .proposal import APPROVAL_STATES, PROGRESS, REVIEW_STATES


# EQUIP-UI-002: one definition per bucket, reused by KPI, donut, department chart and drill-down.
PHYS_ACTIVE = [("tp_asset_class", "in", ["device", "component"]), ("tp_parent_id", "=", False),
               ("tp_lifecycle", "=", "active")]
USER_HELD = [("tp_custody", "in", ["employee", "loan"]), ("tp_employee_id", "!=", False)]
SHARED_HELD = [("tp_custody", "in", ["department", "location"])]
IN_USE = ["|", "&", ("tp_custody", "in", ["employee", "loan"]), ("tp_employee_id", "!=", False),
          ("tp_custody", "in", ["department", "location"])]
IN_STOCK = [("tp_custody", "=", "stock")]
OTHER_HELD = ["!", "|", "|", "&", ("tp_custody", "in", ["employee", "loan"]), ("tp_employee_id", "!=", False),
              ("tp_custody", "in", ["department", "location"]), ("tp_custody", "=", "stock")]
TYPE_TOP_N = 7
FAULTY = [("tp_technical_state", "in", ["limited", "broken"])]
REPLACE = [("tp_replacement_needed", "=", True)]
ACTION_CONTEXT = {
    # Keep in sync with each action's XML context: drill-down replaces it, so `create: False`
    # must be repeated here or the HR-scoped lists would show "Mới" when opened from here.
    "tp_equipment.action_equipment": {"tp_filter_profile": "equipment_users",
                                      "tp_eq_leaf": "tp_equipment.menu_equipment_all", "create": False},
    "tp_equipment.action_equipment_stock": {"tp_filter_profile": "equipment_stock",
                                            "tp_eq_leaf": "tp_equipment.menu_equipment_stock"},
    "tp_equipment.action_equipment_shared": {"tp_filter_profile": "equipment_shared",
                                             "tp_eq_leaf": "tp_equipment.menu_equipment_shared", "create": False},
    "tp_equipment.action_equipment_all_records": {"tp_filter_profile": "equipment",
                                                  "tp_eq_leaf": "tp_equipment.menu_equipment_records"},
}
DEPT_COLORS = {"department": "#1E3A8A", "shared": "#14B8A6", "stock": "#2563EB", "unknown": "#D97706"}


class EquipmentDashboard(models.AbstractModel):
    _name = "tp.equipment.dashboard"
    _description = "Kho thiết bị — tổng quan quản trị"

    def _scope_domain(self, filters=None):
        check_admin(self.env, self)
        filters = filters or {}
        domain = [("tp_code", "!=", False), ("company_id", "in", self.env.companies.ids)]
        for key, field in (("department_id", "tp_current_department_id"), ("location_id", "tp_location_id")):
            value = filters.get(key)
            if value:
                try:
                    value = int(value)
                except (ValueError, TypeError) as exc:
                    raise ValidationError(_("Phạm vi lọc không hợp lệ.")) from exc
                domain.append((field, "=", value))
        start, end = filters.get("date_from"), filters.get("date_to")
        try:
            start = fields.Date.to_date(start) if start else None
            end = fields.Date.to_date(end) if end else None
        except (ValueError, TypeError) as exc:
            raise ValidationError(_("Ngày lọc không hợp lệ.")) from exc
        if start and end and start > end:
            raise ValidationError(_("Từ ngày phải trước hoặc bằng Đến ngày."))
        if start:
            domain.append(("tp_purchase_date", ">=", fields.Date.to_string(start)))
        if end:
            domain.append(("tp_purchase_date", "<=", fields.Date.to_string(end)))
        return domain

    def _facets(self):
        today = fields.Date.context_today(self)
        return {
            "all": [],
            "physical": [("tp_asset_class", "in", ["device", "component"]), ("tp_parent_id", "=", False)],
            "available": [("tp_asset_class", "in", ["device", "component"]), ("tp_parent_id", "=", False),
                          ("tp_availability", "=", "available")],
            "in_use": [("tp_asset_class", "in", ["device", "component"]), ("tp_parent_id", "=", False),
                       ("tp_availability", "=", "in_use")],
            "repair": [("tp_availability", "=", "repair")],
            "draft": [("tp_lifecycle", "=", "draft")],
            "unverified": [("tp_verification", "=", "source"), ("tp_lifecycle", "!=", "retired")],
            "broken": [("tp_technical_state", "=", "broken"), ("tp_lifecycle", "=", "active")],
            "offboard": [("tp_employee_archived", "=", True), ("tp_lifecycle", "=", "active")],
            "warranty": [("tp_warranty_end", ">=", fields.Date.to_string(today)),
                         ("tp_warranty_end", "<=", fields.Date.to_string(today + timedelta(days=30))),
                         ("tp_lifecycle", "=", "active")],
            "unknown_date": [("tp_purchase_date", "=", False)],
        }

    def _workload_source(self, filters, key):
        equipment_domain = self._scope_domain(filters)
        filters = filters or {}
        company_domain = [("company_id", "in", self.env.companies.ids)]
        if key == "open_requests":
            equipment_ids = self.env["maintenance.equipment"].with_context(active_test=False).search(equipment_domain).ids
            return ("maintenance.request", "repairs", "repair", company_domain + [
                ("equipment_id", "in", equipment_ids), ("tp_state", "in", ["new", "in_progress", "vendor"])])
        if key == "review_proposals":
            domain = company_domain + [("review_state", "=", "review")]
            if filters.get("department_id"):
                domain.append(("requester_department_id", "=", int(filters["department_id"])))
            for key, operator in (("date_from", ">="), ("date_to", "<=")):
                if filters.get(key):
                    domain.append(("date", operator, fields.Date.to_string(fields.Date.to_date(filters[key]))))
            return "tp.equipment.proposal", "proposals", "proposal", domain
        raise ValidationError(_("Nhóm công việc không hợp lệ."))

    @api.model
    def get_dashboard(self, filters=None):
        domain = self._scope_domain(filters)
        equipment = self.env["maintenance.equipment"].with_context(active_test=False)

        def count(extra):
            return equipment.search_count(domain + extra)

        def grouped(field, labels=None):
            rows = equipment._read_group(domain, [field], ["__count"])
            result = []
            for value, amount in rows:
                key = value.id if hasattr(value, "id") else value
                label = value.display_name if hasattr(value, "display_name") and value else (labels or {}).get(key, key)
                result.append({"key": key or False, "label": label or _("Chưa khai báo"), "count": amount})
            return sorted(result, key=lambda row: (-row["count"], row["label"]))

        facets = self._facets()
        kpi_meta = [
            ("all", "Tổng hồ sơ", "Mọi hồ sơ có mã, kể cả nháp và ngừng quản lý; gồm dịch vụ."),
            ("physical", "Thiết bị vật lý", "Thiết bị và linh kiện độc lập; loại dịch vụ và linh kiện đã gắn trong bộ máy."),
            ("available", "Sẵn sàng cấp", "Thiết bị vật lý có trạng thái khả dụng Sẵn sàng cấp phát."),
            ("in_use", "Đang sử dụng", "Thiết bị vật lý có trạng thái khả dụng Đang sử dụng."),
        ]
        needs_meta = [
            ("draft", "Hồ sơ chưa đăng ký", "Kiểm tra dữ liệu trước khi đăng ký vào kho."),
            ("unverified", "Chưa kiểm tra thực tế", "Hồ sơ chưa xác minh, chưa ngừng quản lý."),
            ("broken", "Thiết bị đang hỏng", "Thiết bị đang quản lý có kết luận kỹ thuật Hỏng."),
            ("repair", "Đang sửa chữa", "Hồ sơ có trạng thái khả dụng Đang sửa chữa."),
            ("offboard", "Người giữ đã lưu trữ", "Kiểm tra thu hồi; lưu trữ HR không có nghĩa đã trả máy."),
            ("warranty", "Bảo hành đến hạn trong 30 ngày", "Theo ngày hết hạn đã khai báo; không kết luận về giới hạn số đếm."),
        ]
        departments = self.env["hr.department"].search(["|", ("company_id", "=", False),
                                                        ("company_id", "in", self.env.companies.ids)])
        dept_rows = self._tp_department_rows(domain, departments, equipment)
        workload = []
        for key, label, definition in [
            ("open_requests", "Yêu cầu sửa chữa đang mở",
             "Phiếu mới / đang xử lý / tại NCC của thiết bị trong bộ lọc hiện tại. Kỳ theo ngày mua/nhận thiết bị, không theo ngày báo lỗi."),
            ("review_proposals", "Đề xuất chờ rà soát",
             "Hồ sơ đang rà soát trong company được phép. Kỳ theo ngày đề xuất; phòng theo bộ phận cần. Không áp bộ lọc vị trí."),
        ]:
            model, _action, _view, workload_domain = self._workload_source(filters, key)
            workload.append({"key": key, "label": label, "definition": definition,
                             "count": self.env[model].with_context(active_test=False).search_count(workload_domain)})
        ui_extra = self._tp_ui_dashboard_extra(domain, filters, equipment)
        return {
            "workload": workload,
            "domain": domain,
            "kpis": [{"key": key, "label": label, "definition": definition, "count": count(facets[key])}
                     for key, label, definition in kpi_meta],
            "needs": [{"key": key, "label": label, "definition": definition, "count": count(facets[key])}
                      for key, label, definition in needs_meta],
            "types": grouped("category_id"),
            "technical": grouped("tp_technical_state", dict(TECH_STATE)),
            "classes": grouped("tp_asset_class", dict(ASSET_CLASS)),
            "locations": grouped("tp_location_id"),
            "departments": dept_rows,
            "options": {
                "departments": [{"id": row.id, "name": row.display_name} for row in departments],
                "locations": self.env["tp.equipment.location"].search_read(
                    [("company_id", "in", self.env.companies.ids)], ["name"], order="name"),
            },
            "unknown_date": count(facets["unknown_date"]),
            **ui_extra,
        }

    def _tp_department_rows(self, domain, departments, equipment):
        """Physical managed devices: one row per HR department, then shared / stock / unknown (never merged)."""
        phys = domain + PHYS_ACTIVE
        rows = []
        for department in departments:
            dept_dom = phys + [("tp_current_department_id", "=", department.id)]
            personal = equipment.search_count(dept_dom + USER_HELD)
            shared = equipment.search_count(dept_dom + SHARED_HELD)
            other = equipment.search_count(dept_dom) - personal - shared
            total = personal + shared + max(other, 0)
            if total:
                rows.append({"key": department.id, "kind": "department", "label": department.display_name,
                             "count": total, "personal": personal, "shared": shared + max(other, 0),
                             "tone": "department", "color": DEPT_COLORS["department"],
                             "hint": f"{personal} giao nhân viên · {shared + max(other, 0)} dùng chung"})
        rows.sort(key=lambda row: (-row["count"], row["label"]))
        no_dept = phys + [("tp_current_department_id", "=", False)]
        extra_rows = [
            ("dept_shared", "Dùng chung", "shared", no_dept + SHARED_HELD,
             "Thiết bị dùng chung / đặt tại vị trí chưa gắn phòng ban HR"),
            ("in_stock", "Trong kho", "stock", phys + IN_STOCK, "Thiết bị đang ở kho, chưa giao"),
            ("dept_unknown", "Chưa xác định phòng ban", "unknown",
             no_dept + [("tp_custody", "!=", "stock"), ("tp_custody", "not in", ["department", "location"])],
             "Người giữ chưa có phòng ban HR, gửi sửa ngoài hoặc chưa rõ nơi giữ"),
        ]
        for kind, label, tone, row_domain, hint in extra_rows:
            amount = equipment.search_count(row_domain)
            if amount:
                rows.append({"key": kind, "kind": kind, "label": label, "count": amount,
                             "personal": 0, "shared": 0, "tone": tone, "color": DEPT_COLORS[tone], "hint": hint})
        return rows

    def _tp_proposal_scope_domain(self, filters):
        filters = filters or {}
        dom = [
            ("company_id", "in", self.env.companies.ids),
            ("review_state", "!=", "cancel"),
            ("approval_state", "!=", "rejected"),
            ("progress", "not in", ["done", "cancel"]),
        ]
        if filters.get("department_id"):
            dom.append(("requester_department_id", "=", int(filters["department_id"])))
        if filters.get("date_from"):
            dom.append(("date", ">=", filters["date_from"]))
        if filters.get("date_to"):
            dom.append(("date", "<=", filters["date_to"]))
        return dom

    def _tp_ui_dashboard_extra(self, domain, filters, equipment):
        phys_dom = domain + PHYS_ACTIVE
        physical_total = equipment.search_count(phys_dom)
        employee_count = equipment.search_count(phys_dom + USER_HELD)
        shared_count = equipment.search_count(phys_dom + SHARED_HELD)
        in_use_count = employee_count + shared_count
        in_stock_count = equipment.search_count(phys_dom + IN_STOCK)
        other_count = equipment.search_count(phys_dom + OTHER_HELD)
        available_ready = equipment.search_count(phys_dom + [("tp_availability", "=", "available")])
        stock_need_check = max(in_stock_count - available_ready, 0)

        all_records = equipment.search_count(domain)
        service_count = equipment.search_count(domain + [("tp_asset_class", "=", "service"), ("tp_lifecycle", "=", "active")])
        draft_count = equipment.search_count(domain + [("tp_lifecycle", "=", "draft")])
        retired_count = equipment.search_count(domain + [("tp_lifecycle", "=", "retired")])
        unverified_count = equipment.search_count(domain + [("tp_lifecycle", "=", "active"), ("tp_verification", "!=", "verified")])

        Proposal = self.env["tp.equipment.proposal"]
        prop_dom = self._tp_proposal_scope_domain(filters)
        open_proposals = Proposal.search(prop_dom, order="date desc, id desc")
        prop_draft = len(open_proposals.filtered(lambda p: p.review_state in ("draft", "returned")))
        prop_reviewing = len(open_proposals.filtered(lambda p: p.review_state == "review"))
        prop_approved_wait = max(len(open_proposals) - prop_draft - prop_reviewing, 0)

        rev_map = dict(REVIEW_STATES)
        app_map = dict(APPROVAL_STATES)
        prog_map = dict(PROGRESS)
        recent_proposals = []
        for p in open_proposals[:5]:
            amt_txt = "Chưa có"
            if p.amount_total_known:
                sym = p.currency_id.symbol or p.currency_id.name or "₫"
                amt_txt = f"{round(p.amount_total or 0):,}".replace(",", ".") + f" {sym}"
            req = p.requester_employee_id.name or p.requester_department_id.name or p.requester_text or "Chưa ghi nhận"
            recent_proposals.append({
                "id": p.id,
                "name": p.name,
                "title": p.title,
                "requester": req,
                "date": p.date.strftime("%d/%m/%Y") if (p.date_known and p.date) else "Chưa rõ ngày",
                "amount": amt_txt,
                "review_state": p.review_state,
                "review_label": rev_map.get(p.review_state, p.review_state),
                "approval_state": p.approval_state,
                "approval_label": app_map.get(p.approval_state, p.approval_state),
                "progress_label": prog_map.get(p.progress, p.progress),
            })

        def pct(val, denom):
            return round((val * 100.0 / denom), 1) if denom else 0.0

        ui_kpis = [
            {
                "key": "physical",
                "label": "Tổng thiết bị",
                "value": physical_total,
                "subnote": f"{all_records} hồ sơ · {service_count} dịch vụ" if all_records != physical_total else "Đang quản lý vật lý",
                "tooltip": "Thiết bị và linh kiện độc lập đang quản lý (không tính nháp, ngừng quản lý, dịch vụ).",
                "tone": "navy",
                "icon": "devices",
            },
            {
                "key": "in_use",
                "label": "Đang sử dụng",
                "value": in_use_count,
                "subnote": f"{employee_count} giao nhân viên · {shared_count} dùng chung",
                "tooltip": "Gồm thiết bị giao nhân viên và dùng chung (phòng ban / vị trí cố định).",
                "tone": "teal",
                "icon": "person_pin",
            },
            {
                "key": "in_stock",
                "label": "Trong kho",
                "value": in_stock_count,
                "subnote": f"{available_ready} sẵn sàng · {stock_need_check} chờ kiểm tra",
                "tooltip": "Tất cả thiết bị vật lý hiện ở kho, bao gồm máy chờ kiểm tra thực tế hoặc hạn chế/hỏng.",
                "tone": "blue",
                "icon": "inventory_2",
            },
            {
                "key": "open_proposals",
                "label": "Đề xuất đang mở",
                "value": len(open_proposals),
                "subnote": f"{prop_draft} nháp · {prop_reviewing + prop_approved_wait} đang xử lý",
                "tooltip": "Đề xuất mua sắm / sửa chữa / nâng cấp chưa hủy và chưa hoàn tất (gồm hồ sơ nháp).",
                "tone": "purple",
                "icon": "assignment",
            },
        ]

        allocation = {
            "denominator": physical_total,
            "items": [
                {"key": "employee", "label": "Giao nhân viên", "count": employee_count,
                 "percent": pct(employee_count, physical_total), "color": "#0F766E", "drill_kind": "employee"},
                {"key": "shared", "label": "Dùng chung", "count": shared_count,
                 "percent": pct(shared_count, physical_total), "color": "#2DD4BF", "drill_kind": "shared"},
                {"key": "in_stock", "label": "Trong kho", "count": in_stock_count,
                 "percent": pct(in_stock_count, physical_total), "color": "#2563EB", "drill_kind": "in_stock"},
                {"key": "other", "label": "Khác / sửa ngoài", "count": other_count,
                 "percent": pct(other_count, physical_total), "color": "#D97706", "drill_kind": "other"},
            ],
        }

        # Same physical scope as "Tổng thiết bị": top N + "Khác" always sum to physical_total.
        cat_groups = equipment._read_group(phys_dom, ["category_id"], ["__count"])
        palette = ["#2563EB", "#0F766E", "#7C3AED", "#D97706", "#0284C7", "#059669", "#DC2626", "#4F46E5"]
        active_total = sum(cnt for _cat, cnt in cat_groups) or 1
        ordered = sorted(cat_groups, key=lambda x: (-x[1], (x[0].name if x[0] else "zzz")))
        top, rest = (ordered, []) if len(ordered) <= TYPE_TOP_N + 1 else (ordered[:TYPE_TOP_N], ordered[TYPE_TOP_N:])
        ui_types = []
        for cat, cnt in top:
            cid = cat.id if cat else 0
            ui_types.append({
                "id": cid,
                "key": str(cid),
                "kind": "category",
                "label": cat.name if cat else "Chưa phân loại",
                "count": cnt,
                "percent": round(cnt * 100.0 / active_total, 1),
                "color": palette[cid % len(palette)] if cid else "#64748B",
            })
        if rest:
            rest_count = sum(cnt for _cat, cnt in rest)
            ui_types.append({
                "id": -1,
                "key": ",".join(str(cat.id if cat else 0) for cat, _cnt in rest),
                "kind": "category_other",
                "label": f"Khác ({len(rest)} loại)",
                "count": rest_count,
                "percent": round(rest_count * 100.0 / active_total, 1),
                "color": "#94A3B8",
                "members": ", ".join((cat.name if cat else "Chưa phân loại") for cat, _cnt in rest),
            })

        # Source import is main-admin work; a scoped caller gets no row instead of a false zero.
        batches = self.env["tp.equipment.import.batch"]
        pending_import = sum(
            batches.search([("company_id", "in", self.env.companies.ids), ("state", "!=", "applied")])
            .mapped("pending_count"),
        ) if batches.has_access("read") else None

        open_repairs = self.env["maintenance.request"].search_count([
            ("company_id", "in", self.env.companies.ids), ("equipment_id", "in", equipment.search(domain).ids),
            ("tp_state", "in", ["new", "in_progress", "vendor"])])
        facets = self._facets()
        attention = [
            {"key": "faulty", "kind": "faulty", "label": "Hỏng / hạn chế",
             "count": equipment.search_count(phys_dom + FAULTY),
             "hint": "Tình trạng kỹ thuật hạn chế hoặc hỏng", "tone": "red"},
            {"key": "open_repairs", "kind": "open_repairs", "label": "Yêu cầu sửa chữa đang mở", "count": open_repairs,
             "hint": "Mới / đang xử lý / tại đơn vị sửa", "tone": "orange"},
            {"key": "offboard", "kind": "offboard", "label": "Người giữ đã lưu trữ HR",
             "count": equipment.search_count(domain + facets["offboard"]),
             "hint": "Cần lập phiếu thu hồi", "tone": "red"},
            {"key": "warranty", "kind": "warranty", "label": "Bảo hành hết trong 30 ngày",
             "count": equipment.search_count(domain + facets["warranty"]),
             "hint": "Kiểm tra gia hạn hoặc kế hoạch thay thế", "tone": "orange"},
            {"key": "replace", "kind": "replace", "label": "Cần thay thế",
             "count": equipment.search_count(phys_dom + REPLACE),
             "hint": "Đã đánh dấu cần thay thế", "tone": "purple"},
        ]
        quality = [
            {"key": "unverified", "kind": "unverified", "label": "Chưa kiểm tra thực tế", "count": unverified_count,
             "hint": "Hồ sơ theo nguồn, chưa đối chiếu máy thật", "tone": "orange"},
            {"key": "unknown_date", "kind": "unknown_date", "label": "Thiếu ngày mua / nhận",
             "count": equipment.search_count(domain + facets["unknown_date"]),
             "hint": "Không lọc được theo kỳ mua / nhận", "tone": "neutral"},
            {"key": "pending_import", "kind": "pending_import", "label": "Dòng nguồn chờ bổ sung",
             "count": pending_import, "hint": "Dòng Excel chưa đủ thông tin để tạo hồ sơ", "tone": "purple"},
            {"key": "draft", "kind": "draft", "label": "Hồ sơ nháp", "count": draft_count,
             "hint": "Chưa đăng ký vào kho", "tone": "neutral"},
        ]
        quality = [row for row in quality if row["count"] is not None]
        return {
            "ui_kpis": ui_kpis,
            "allocation": allocation,
            "ui_types": ui_types,
            "recent_proposals": recent_proposals,
            "attention": attention,
            "quality": quality,
            "scope_meta": {
                "employee_count": employee_count,
                "shared_count": shared_count,
                "in_stock_count": in_stock_count,
                "other_count": other_count,
                "all_records": all_records,
                "physical_total": physical_total,
                "service_count": service_count,
                "draft_count": draft_count,
                "retired_count": retired_count,
                "unverified_count": unverified_count,
                "available_ready": available_ready,
                "stock_need_check": stock_need_check,
                "pending_import": pending_import,
            },
        }

    def _tp_category_ids(self, key):
        try:
            return [int(part) for part in str(key or "").split(",") if part.strip() != ""]
        except (TypeError, ValueError) as exc:
            raise ValidationError(_("Phân loại không hợp lệ.")) from exc

    def _tp_equipment_action(self, xmlid, domain, name=None):
        # Counts above use active_test=False, so the drill-down list must too, or totals would differ.
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["domain"] = domain
        action["context"] = {**ACTION_CONTEXT[xmlid], "active_test": False}
        if name:
            action["name"] = name
        return action

    @api.model
    def open_ui_detail(self, kind, key=None, filters=None):
        """Every drill-down opens exactly the set counted on the dashboard (scope filters + bucket domain)."""
        check_admin(self.env, self)
        domain = self._scope_domain(filters)
        phys = domain + PHYS_ACTIVE
        if kind == "pending_import":
            return self.env["ir.actions.act_window"]._for_xml_id("tp_equipment.action_import_pending")
        if kind == "open_repairs":
            # Same scope as the count: open requests of the equipment matching the dashboard filters.
            _model, _key, _view, repair_domain = self._workload_source(filters, "open_requests")
            action = self.env["ir.actions.act_window"]._for_xml_id("tp_equipment.action_repairs")
            action["domain"] = repair_domain
            return action
        if kind == "attention":
            return self.env["ir.actions.act_window"]._for_xml_id("tp_equipment.action_equipment_attention")
        if kind == "open_proposals":
            return {
                "type": "ir.actions.act_window",
                "name": "Đề xuất mua thiết bị",
                "res_model": "tp.equipment.proposal",
                "view_mode": "list,form",
                "views": [(self.env.ref("tp_equipment.proposal_list").id, "list"),
                          (self.env.ref("tp_equipment.proposal_form").id, "form")],
                "domain": self._tp_proposal_scope_domain(filters),
                "context": {"tp_filter_profile": "proposal", "tp_eq_leaf": "tp_equipment.menu_proposals"},
            }
        if kind == "in_stock":
            return self._tp_equipment_action("tp_equipment.action_equipment_stock", phys + IN_STOCK)
        if kind == "employee":
            return self._tp_equipment_action("tp_equipment.action_equipment", phys + USER_HELD)
        if kind in ("shared", "dept_shared"):
            extra = SHARED_HELD if kind == "shared" else [("tp_current_department_id", "=", False)] + SHARED_HELD
            return self._tp_equipment_action(
                "tp_equipment.action_equipment_shared", phys + extra,
                name="Thiết bị dùng chung" if kind == "shared" else "Dùng chung — chưa gắn phòng ban")
        buckets = {
            "physical": (PHYS_ACTIVE, "Tổng thiết bị vật lý"),
            "in_use": (PHYS_ACTIVE + IN_USE, "Đang sử dụng (giao nhân viên và dùng chung)"),
            "other": (PHYS_ACTIVE + OTHER_HELD, "Thiết bị khác / sửa ngoài / chưa rõ người giữ"),
            "unverified": ([("tp_lifecycle", "=", "active"), ("tp_verification", "!=", "verified")],
                           "Thiết bị chưa xác minh thực tế"),
            "offboard": (self._facets()["offboard"], "Người giữ đã lưu trữ hồ sơ HR"),
            "faulty": (PHYS_ACTIVE + FAULTY, "Thiết bị hỏng / hạn chế"),
            "warranty": (self._facets()["warranty"], "Bảo hành hết trong 30 ngày"),
            "replace": (PHYS_ACTIVE + REPLACE, "Thiết bị cần thay thế"),
            "draft": (self._facets()["draft"], "Hồ sơ nháp"),
            "unknown_date": (self._facets()["unknown_date"], "Thiếu ngày mua / nhận"),
            "dept_unknown": (PHYS_ACTIVE + [("tp_current_department_id", "=", False), ("tp_custody", "!=", "stock"),
                                            ("tp_custody", "not in", ["department", "location"])],
                             "Chưa xác định phòng ban"),
        }
        if kind in buckets:
            extra, name = buckets[kind]
        elif kind == "category":
            try:
                cid = int(key or 0)
            except (TypeError, ValueError) as exc:
                raise ValidationError(_("Phân loại không hợp lệ.")) from exc
            extra = PHYS_ACTIVE + [("category_id", "=", cid or False)]
            name = "Thiết bị theo phân loại"
        elif kind == "category_other":
            ids = self._tp_category_ids(key)
            if not ids:
                raise ValidationError(_("Phân loại không hợp lệ."))
            real = [cid for cid in ids if cid]
            cat = [("category_id", "in", real)] if real else []
            if 0 in ids:
                cat = ["|", ("category_id", "=", False)] + cat if cat else [("category_id", "=", False)]
            extra = PHYS_ACTIVE + cat
            name = "Thiết bị — nhóm loại khác"
        elif kind == "department":
            try:
                did = int(key)
            except (TypeError, ValueError) as exc:
                raise ValidationError(_("Phòng ban không hợp lệ.")) from exc
            extra = PHYS_ACTIVE + [("tp_current_department_id", "=", did)]
            name = "Thiết bị theo phòng ban"
        else:
            raise ValidationError(_("Tiêu chí xem chi tiết không hợp lệ."))
        return self._tp_equipment_action("tp_equipment.action_equipment_all_records", domain + extra, name=name)

    @api.model
    def open_detail(self, filters=None, facet="all", value=None):
        domain = self._scope_domain(filters)
        if facet in ("open_requests", "review_proposals"):
            _model, action_key, view_key, workload_domain = self._workload_source(filters, facet)
            action = self.env["ir.actions.actions"]._for_xml_id("tp_equipment.action_" + action_key)
            action.update({"domain": workload_domain, "context": {"active_test": False},
                           "views": [(self.env.ref("tp_equipment." + view_key + "_list").id, "list"),
                                     (self.env.ref("tp_equipment." + view_key + "_form").id, "form")]})
            return action
        grouped_fields = {"types": "category_id", "technical": "tp_technical_state",
                          "departments": "tp_current_department_id", "locations": "tp_location_id",
                          "classes": "tp_asset_class"}
        if facet in grouped_fields:
            domain.append((grouped_fields[facet], "=", value or False))
        elif facet in self._facets():
            domain += self._facets()[facet]
        else:
            raise ValidationError(_("Tiêu chí xem chi tiết không hợp lệ."))
        action = self.env["ir.actions.actions"]._for_xml_id("tp_equipment.action_equipment_all_records")
        action.update({"domain": domain, "context": {"active_test": False, "tp_filter_profile": "equipment",
                                                     "tp_eq_leaf": "tp_equipment.menu_equipment_records"},
                       "views": [(self.env.ref("tp_equipment.equipment_list").id, "list"),
                                 (self.env.ref("tp_equipment.equipment_form").id, "form")]})
        return action
