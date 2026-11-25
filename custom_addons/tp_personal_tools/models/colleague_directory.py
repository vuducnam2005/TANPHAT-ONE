# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Safe colleague directory for TANPHAT ONE Personal Tools.

Returns only active internal accounts (`res.users` / `res.partner`) enriched with
public department and job title from linked `hr.employee` (via Odoo 20 `hr.version`)
to disambiguate colleagues with identical names, without ever exposing sensitive HR
fields or OdooBot.
"""

from odoo import api, models
from odoo.exceptions import AccessError
from odoo.fields import Domain


class ResUsersColleagueDirectory(models.Model):
    _inherit = "res.users"

    def _tp_require_internal_caller(self):
        if not self.env.user._is_internal() or not self.env.user.active:
            raise AccessError(self.env._("Tài khoản không có quyền truy cập công cụ nội bộ."))

    @api.model
    def _tp_public_employee_meta_by_user(self, user_ids):
        """Return `{user_id: {'department': str, 'job_title': str}}` with zero private HR fields."""
        if not user_ids:
            return {}
        company_ids = self.env.companies.ids or [self.env.company.id]
        employees = (
            self.env["hr.employee"]
            .sudo()
            .search(
                [
                    ("active", "=", True),
                    ("user_id", "in", list(user_ids)),
                    ("company_id", "in", company_ids),
                ],
                order="id asc",
            )
        )
        meta = {}
        for emp in employees:
            uid = emp.user_id.id
            if uid and uid not in meta:
                dept_name = (emp.department_id.name or "").strip() if emp.department_id else ""
                job_name = (
                    (emp.job_id.name or "").strip()
                    if emp.job_id
                    else (emp.job_title or "").strip()
                )
                meta[uid] = {
                    "department": dept_name,
                    "job_title": job_name,
                }
        return meta

    @api.model
    def _tp_format_colleagues(self, users):
        if not users:
            return []
        emp_meta = self._tp_public_employee_meta_by_user(users.ids)
        # Real presence status from native bus.presence / res.users.im_status (never faked)
        im_map = {
            u.id: (getattr(u, "im_status", None) or "offline")
            for u in users.sudo()
        }
        items = []
        for u in users:
            partner = u.sudo().partner_id
            pub = emp_meta.get(u.id, {})
            dept = pub.get("department", "")
            job = pub.get("job_title", "")
            subtitle = " · ".join(part for part in (dept, job) if part)
            raw_im = im_map.get(u.id, "offline")
            im_status = raw_im if raw_im in ("online", "away", "offline") else "offline"
            write_token = str(partner.write_date or "")
            items.append(
                {
                    "user_id": u.id,
                    "partner_id": partner.id,
                    "name": partner.name or u.name or "",
                    "department": dept,
                    "job_title": job,
                    "subtitle": subtitle,
                    "im_status": im_status,
                    "avatar_url": f"/web/image/res.partner/{partner.id}/avatar_128"
                    + (f"?unique={write_token.replace(' ', '_')}" if write_token else ""),
                }
            )
        return items

    @api.model
    def tp_search_colleagues(self, query="", limit=30, include_self=False):
        """Search active internal colleagues for Task sharing, Calendar invites, and Discuss."""
        self._tp_require_internal_caller()
        safe_limit = max(1, min(int(limit or 30), 60))
        root_user_id = self.env["ir.model.data"]._xmlid_to_res_id("base.user_root")
        odoobot_partner_id = self.env["ir.model.data"]._xmlid_to_res_id("base.partner_root")

        domain = Domain("active", "=", True) & Domain("share", "=", False)
        if root_user_id:
            domain &= Domain("id", "!=", root_user_id)
        if odoobot_partner_id:
            domain &= Domain("partner_id", "!=", odoobot_partner_id)
        if not include_self:
            domain &= Domain("id", "!=", self.env.uid)

        company_ids = self.env.companies.ids or [self.env.company.id]
        domain &= Domain("company_ids", "in", company_ids)

        q = (query or "").strip()
        if q:
            org_domain = (
                Domain("active", "=", True)
                & Domain("user_id", "!=", False)
                & Domain("company_id", "in", company_ids)
                & (
                    Domain("department_id.name", "ilike", q)
                    | Domain("job_id.name", "ilike", q)
                    | Domain("job_title", "ilike", q)
                )
            )
            matched_emps = self.env["hr.employee"].sudo().search(org_domain, limit=100)
            org_matched_uids = matched_emps.mapped("user_id").ids
            text_domain = Domain("name", "ilike", q) | Domain("partner_id.name", "ilike", q)
            if org_matched_uids:
                text_domain |= Domain("id", "in", org_matched_uids)
            domain &= text_domain

        users = self.sudo().search(domain, order="name asc, id asc", limit=safe_limit)
        return self._tp_format_colleagues(users)
