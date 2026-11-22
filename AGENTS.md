# Webmail — Agent Rules

## Scope
This repository has been reset to a clean T01 monorepo skeleton.
The existence of these instructions is not an approval to implement anything else.

## Responsibilities and approval gates
- Claude Code: implementation/code changes only with a separate Implementation GO.
- Copilot: Git and PR operations only with a separate Git/PR GO.
- Codex: independent review as authorized.
- Merge and deployment require their own explicit GO.
- T01 must not touch any production mailserver, database, credentials, or Docker socket.

## Constraints
- Dovecot is authoritative for mail messages; PostgreSQL stores application data
  and indexes, not a replacement mailbox.
- Admin role does not automatically authorize access to mailbox content.
- Isolate privileged mailserver administration behind a separately controlled agent.
- Use mock-only external adapters until a later explicit GO.
- Never invent full ADR, Baseline, or approved specification text from summaries.
- Future changes must be scoped, reviewed and approved separately.

## T01 deliverable
Directory skeleton and neutral documentation only. No active API, worker,
frontend, database migrations, SMTP/IMAP access, secrets, or deployment.
