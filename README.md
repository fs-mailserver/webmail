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

ADR-001–146 source records and their approval evidence were recovered from the
user-provided ChatGPT export under `docs/adr/`. ADR-001/002 have contextual
confirmation; ADR-003–146 have explicit confirmation. See `docs/adr/ADR-REGISTER.md`.
Architecture Baseline v1.0 is formally approved by ADR-146; the separately
compiled overview in `docs/architecture/ARCHITECTURE-BASELINE-v1.0.md` is
clearly labeled as retrospective, not as a recovered verbatim original.
See `docs/architecture/T01-READINESS-REVIEW.md` for documentation readiness.

Any further implementation, PR/merge, infrastructure changes, and deployment require
separate explicit GO.
