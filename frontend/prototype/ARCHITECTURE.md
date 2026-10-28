# Frontend architecture

Architecture update, 2026-10-28: the selected direction is an independent web frontend calling Odoo APIs. The current design is [TP_PLATFORM_SOURCE_STRUCTURE.md](../docs/architecture/TP_PLATFORM_SOURCE_STRUCTURE.md). This file describes the existing vanilla JS prototype; no runtime files have been moved in this design change.

`frontend/` is a standalone browser prototype, kept easy to run and review without a Python or PostgreSQL setup. The future production UI is a separate React/TypeScript/Vite app calling an Odoo API.

```text
index.html
└── app/bootstrap.js          route, state, events, module registry
    └── app/shell.js          sidebar, project selector, shared dialog
        └── modules/<name>/   department feature boundary
            ├── module.js     page registry and initial state
            ├── data.js       synthetic fixture only
            ├── repository.js effective records, KPI and business rules
            ├── components.js  department-specific tables and ledgers
            └── pages/         overview, lists and drill-down views
        └── shared/            formatters, accessible UI helpers, SVG charts
```

The data direction is one way: `repository.js` reads raw rows, applies effective-record rules, and returns a snapshot; pages render that snapshot; pages never add financial numbers. Search and sort stay presentation-only unless a page explicitly marks a control as a financial scope filter.

To extend this prototype with another department (production uses business features and department workspaces instead):

1. Copy the boundary under `src/modules/<department>/` and give it a stable `id`.
2. Keep that department's fixture, repository, field mappings and rules inside the boundary. Reuse `shared/` for formatting and generic layout primitives.
3. Export a module object with `id`, `name`, `pages`, `initialState` and `load()`, then add it to the `modules` map in `src/app/bootstrap.js`.
4. Keep prototype fixtures representative. The production API contract will be designed and reconciled on the backend rather than copying client-side fixture algorithms.

Production integration replaces the mock repository with an API client in the standalone web app. Authoritative financial and effective-record rules move to Odoo model/actions, with OpenAPI DTOs at the boundary. Odoo addons own models, security and thin API controllers; native views support administration. The prototype has not been migrated in this design change.
