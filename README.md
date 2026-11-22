# Webmail

New clean monorepo foundation for the Webmail project (T01 scaffold).

## Structure
- `apps/web/` — planned Next.js frontend (T08)
- `apps/api/` — planned FastAPI API service (T04)
- `apps/worker/` — planned background worker
- `packages/backend/` — shared backend components
- `packages/ui/` — shared UI components
- `packages/api-client/` — API client
- `docs/` — architecture, ADRs, specs, execution orders
- `infra/` — isolated non-production infrastructure
- `tests/` — future test suites

## Status
Only directory skeleton and project conventions are present. No application,
database migration, mailserver integration, or deployment is included.

Architecture Baseline v1.0 and ADR-001–146 were discussed and approved in previous
project conversations, but their complete original texts have not been verified.
Do not reconstruct or label missing documents as verified.

Any further implementation, PR/merge, infrastructure changes, and deployment require
separate explicit GO.
