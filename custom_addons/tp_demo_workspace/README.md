# tp_demo_workspace — UI-DEMO-001

Native Odoo workspace that shows TANPHAT ONE to leadership on an **isolated demo database with synthetic data**
(`tp_tanphat_demo_ui001`). It is not installed on dev/test and not part of the official React frontend.
Spec: [TP_UI_DEMO_001_SPEC.md](../../docs/architecture/TP_UI_DEMO_001_SPEC.md);
runbook: [UI_DEMO_001.md](../../ops/runbooks/UI_DEMO_001.md).

## Navigation (UI-DEMO-002, CHG-20261030-005)

Implemented and live-checked on 31 October 2026; **IMPLEMENTED_PENDING_AUDIT**.
Full file/test/screenshot handoff: [UI_DEMO_002_HANDOFF.md](../../docs/demo/UI_DEMO_002_HANDOFF.md).

The Demo app has a Vietnamese work navigation: **Tổng quan**, **Dự án & công việc**,
**Hợp đồng & hồ sơ**, **Kinh doanh**, **Nguồn lực**, **Đề nghị**. “Tất cả phân hệ”
opens a native searchable dialog showing the standard TP names, descriptions and every
permitted existing leaf action. Below 992px the same dialog opens from “Phân hệ”.
Search ignores Vietnamese accents and case, and accepts familiar English aliases.
It searches menu labels/descriptions only, never business records.

The catalog in `static/src/navigation/` enriches only leaves in the native menu
service tree. Leadership receives 12 modules / 17 leaves; engineering receives 10
modules / 15 leaves, with CRM and Bid absent from menu, catalog and search. Contracts
stay available to both; Finance retains backend record/amount/file restrictions.
Mixed modules label their illustrative leaves explicitly (staffing, acceptance/cash).

QWeb inheritance replaces native sections only while current app is
`tp_demo_workspace.menu_demo_root`. A minimal static `NavBar.components` patch
registers the two template components because NavBar has no component registry hook.
It does not override `adapt`, router, menu service, action service or the upstream
WebClient. Selection calls native `menu.selectMenu(actualMenu)`; active selection
observes the native current controller without dispatching an extra action.
The other TANPHAT ONE app and native applications retain their navigation.

## What is real and what is illustrative

| Screen | Real source (canonical model) | Illustrative part ("Minh họa định hướng") | Limits |
|---|---|---|---|
| TP Dashboard | KPI counts via `search_count` on project, task, revision, document, `crm.lead` | Link opportunity → project by same customer | A KPI click opens the same domain it counted |
| TP Projects | `project.project` (list, kanban, form) + overview client action | Survey/design panels | No new project fields |
| TP Survey, TP Design | — | Backend catalog rows: list, sample detail, filter | No model, no workflow |
| TP Contracts | `tp.contract`, `tp.contract.revision`, submissions, audit (read-only) | — | Draft/in_review/returned come from the real CTR-002a workflow; review complete, BASE, signature and effectivity stay out of scope |
| TP Tasks | `project.task` kanban/list/form | — | No Gantt, no Enterprise |
| TP HR | `hr.employee.public` | Staffing per project (catalog) | No payroll, no private employee data |
| TP Finance | `tp.contract.line.amount` behind `financial_read` | Accepted value and cash columns | Only reviewed revisions are totalled, one currency per total, no profit |
| TP Documents | `tp.contract.document` general vs financial | — | Financial files need `financial_read` (record rule), including `/web/content` |
| CRM | `crm.lead` read-only, demo business group only | — | No CRM → bid → contract link, no new base fields |
| Request | — | BASE-style request list with a proposed TP flow | BASE remains the approver; amounts only with `financial_read` |
| Bid | — | Tan Phat as bidder | No `purchase_requisition`; business group only |

## Security model

- `group_demo_viewer` opens the menus and the read projection `tp.demo.workspace`; it implies `tp_core.group_user` only.
  `group_demo_business` adds the CRM and bid screens and read access on `crm.lead`.
- The projection reads in the caller's environment (no `sudo`), so company, assignment and `financial_read`
  rules of `tp_project`/`tp_contract` decide what is returned. Amounts are formatted on the server and never shipped
  in static assets; the illustrative catalog lives in Python and is filtered per project before it is returned.
- Demo views are read-only and have no chatter. The demo does not change any ACL, rule or workflow of the TP addons.
- Demo actors get no `base.group_allow_export`; even with it, `export_data` reads through the same record rules
  (covered by `test_demo_access`). Financial files return 404 on `/web/content` for users without the grant.

## Data

`demo_seed.seed(env, passwords)` creates the dataset under the `tp_demo_seed` XML-ID namespace and refuses any
database that is not `tp_tanphat_demo_*`. It is idempotent; contracts C2–C4 move through the TP Contracts workflow
as two password-less workflow users (`demo.lap-hd`, `demo.ra-soat`). Only `demo.lanhdao` (overview,
`financial_read` on all three projects) and `demo.kysu` (one project, no financial grant) get passwords, which
`scripts/ui_demo.py` generates into the ignored `.local/ui-demo-001/credentials.json`.

## Tests

```powershell
.\.venv\Scripts\python.exe scripts\ui_demo.py test
.\.venv\Scripts\python.exe -m unittest scripts.tests.test_ui_demo
```

Native JS tests: authenticate on the owned demo/test runtime and open
`/web/tests?filter=tp_demo_workspace`; the six HOOT tests cover normalization,
permitted mapping/filtering, active identity and native window update behavior.
Python navigation tests assert the actual server menu/action XML-ID mapping for
both actors. Browser proof and screenshots for CHG-005 live under the ignored
`.local/ui-demo-002/review/`; see the spec/status for actual outcomes and limits.

Final CHG-005 results: Odoo **21 passed, 0 failed/errors** on the owned demo test
database; HOOT **6/6**; live **17/17 leadership + 15/15 engineering** destinations.
Both actors pass five viewport sizes (1440 through 375px), native Chromium zoom
125%/150%, keyboard/focus, project context/history and app switching. The old
SCSS and all application code outside this addon match the pre-change snapshot.
The Odoo log retains known Windows filestore GC messages and an optional markdown2
warning; these are not a production filestore acceptance claim.
