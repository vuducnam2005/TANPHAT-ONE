---
name: tanphat-odoo-delivery
description: Plan, implement or review TANPHAT ONE custom Odoo changes using its native UI, business gates, browser evidence and AI handoff. Use for work in this repository, including Claude implementation prompts and audits.
---

# TANPHAT ONE delivery

Read root `AGENTS.md` and the current `docs/PROJECT_STATUS.md` first. They
determine scope, coordinator versus implementer role, business gates and the
current task. This skill does not authorize new business actions or deployment.
Paths below are relative to the repository root, not the skill directory.

## Choose the relevant tools

- Direct source question: start with `rg`; use a source graph for structural
  questions spanning multiple files. Read the source-map section of
  `docs/AI_TOOLING_PLAYBOOK.md` before building or querying a graph.
- UI change: use available `frontend-design` for layout decisions and
  `playwright-cli` or the existing Playwright tests for observable behavior.
  Keep OWL/QWeb/SCSS and native Odoo views/controllers; a design reference
  using React or Ant Design is not a reason to introduce another frontend.
- Review: use `ponytail-review` if available, or its project adaptation below.
- AI provider integration: read the provider section in the playbook only
  when that integration is actually in scope. OmniRoute is not a prerequisite
  for KH-KD work.

## Plan a complete, small change

Trace model/action/security/view and their callers before designing another
layer. Prefer the existing project helper, native Odoo feature, then installed
dependencies. Keep validation, error handling, accessibility and business tests.
Do not shorten the solution by omitting part of the user's requested result.

Write observable acceptance criteria before implementation: actor, environment,
input/action, expected result and evidence. Separate technical verification,
user visual feedback, business acceptance and pilot authorization. A test run
does not accept a design on behalf of the user.

## Verify UI with evidence

Inspect the rendered screen and selectors before interacting. Reuse existing
`.cjs` tests and their browser package when suitable; do not migrate them merely
because an upstream example uses Python. Wait for the required Odoo element or
loaded data, not only `networkidle` (Odoo can hold long-lived connections).

Compare before/after screenshots at the same viewport, role, dataset and route.
Cover the affected list, detail, empty/loading/error states and relevant actions.
For responsive changes, include desktop and mobile, keyboard/focus and reduced
motion; touch-device emulation is not evidence of a real-device test. Scope hover
and animation to the custom addon and respect `prefers-reduced-motion`.

Use a named, isolated Playwright session. Keep screenshots, traces, source maps
and session material under ignored `.local/`; never close another agent's
session. Read-only inspection of dev does not authorize business writes there.
Use the existing test/clone and backup process when the task requires changes.

## Review and hand off

Review touched code plus callers for concrete bugs, permission/data leaks,
invalid transitions, concurrency and reuse. Report reproducible findings with
file/line, impact and the smallest adequate fix. State what was actually tested;
do not label self-review as independent audit.

Follow `scripts/ai_workflow.py start/finish/check` and update status/changelog.
Record source, assumptions and open gates for the next AI. The workflow checker
does not hash all skill/reference files; validate changed skills and links too.
Keep business approval and runtime deployment explicit in the handoff.
