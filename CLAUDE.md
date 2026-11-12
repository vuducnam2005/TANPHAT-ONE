# TANPHAT ONE — Claude entrypoint

Read [AGENTS.md](AGENTS.md) first, then follow its required reading order.
The same business gates, source boundaries and AI handoff apply to Claude.

For planning, implementation and review, use the shared project skill:
[tanphat-odoo-delivery](.agents/skills/tanphat-odoo-delivery/SKILL.md).
Its Claude adapter is in `.claude/skills/tanphat-odoo-delivery/`.
See [tooling playbook](docs/AI_TOOLING_PLAYBOOK.md) for installed tools,
reproducible commands, provenance and current limitations.

Use the current user task and `docs/PROJECT_STATUS.md`, not a source graph,
to decide what to do next. Native Odoo is the primary UI; complete KH-KD
before opening other departments. Optional upstream skills do not change
project authorization or require installation of every example dependency.
