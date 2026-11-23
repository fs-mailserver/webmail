# Webmail — Paket 1 Implementation Blueprint v1.0

**Status:** POTVRĐENO · 22. studenoga 2026. (05:47:35 UTC)  
**Temelj:** Architecture Baseline v1.0 · ADR-001–ADR-146 · P1-01–P1-09  
**Vrsta:** plan buduće implementacije, **ne** autorizacija za implementaciju  
**Izvor:** [izvorni tekst Blueprinta](../architecture/IMPLEMENTATION-BLUEPRINT-v1.0-SOURCE.md), razgovor `GitHub Repozitorij pregled`, ID `6b0020d4-c274-83eb-b3da-0a31ff5bc3d9`.

> Ova je verzija uređena samo radi čitljivosti u Markdownu: uklonjeni su prikazni UI tagovi i kontrola za odabir opcije. Sadržaj zadataka, ovisnosti, kriteriji, zabrane i upute za agente preneseni su iz izvornika. Za eventualnu dvojbu mjerodavan je [izvorni zapis](../architecture/IMPLEMENTATION-BLUEPRINT-v1.0-SOURCE.md).

## 1. Cilj i granice

Paket 1 uspostavlja izolirani razvojni temelj novog Webmail sustava koji će kasnije zamijeniti SnappyMail.

**U opsegu:** monorepo, FastAPI, Next.js, Celery, PostgreSQL/Alembic, Passkey/MFA, RBAC, Credential Broker, mock adapteri, sigurnosni audit, CI i početni PWA.

**Izvan opsega:** stvarni IMAP/SMTP, sadržaj e-mailova, Inbox, Composer, produkcijski mailboxi, produkcijski PostgreSQL, izmjene mailservera, pilot i deployment.

## 2. Radni paketi i ovisnosti

| Zadatak | Naziv | Ovisnost | Rezultat |
|---|---|---|---|
| T01 | Monorepo i konfiguracija | — | Struktura i razvojna pravila |
| T02 | Izolacija testnog okruženja | T01 | Mrežne granice i mock-only startup |
| T03 | PostgreSQL i Alembic | T01–T02 | Testne sheme i migracije |
| T04 | FastAPI i OpenAPI | T01–T03 | API kostur i TS klijent |
| T05 | Identity & Authentication | T03–T04 | Passkey, MFA, sesije, recovery |
| T06 | Authorization Service | T03–T05 | RBAC, grantovi, delegacije |
| T07 | Credential Broker i adapteri | T04–T06 | Mock IMAP/SMTP/Admin |
| T08 | Next.js Frontend Foundation | T04–T06 | Login, Security Center, Admin Shell |
| T09 | Audit, Observability i CI | T01–T08 | Sigurnosna evidencija i kontrolne provjere |
| T10 | Integration & Acceptance | T01–T09 | Dokazi i Acceptance Report |

**Napomena:** osnovni CI, audit ugovori i instrumentacija trebaju se postaviti ranije, tijekom T01–T04. T09 je završno povezivanje i provjera tih temelja, a ne njihovo prvo uvođenje.

## 3. Konkretni izlazni artefakti

| Zadatak | Planirani artefakti |
|---|---|
| T01 | Monorepo workspace, `AGENTS.md`, `README.md`, lockfileovi |
| T02 | Development Compose, mrežna pravila, startup validacija |
| T03 | SQLAlchemy modeli, Alembic, testni fixturei |
| T04 | Pydantic ugovori, OpenAPI dokument, generirani TS klijent |
| T05 | Auth servisi, WebAuthn, MFA, session i recovery testovi |
| T06 | Authorization engine, permissions, delegations i negativni testovi |
| T07 | Credential Broker, mock secret store, adapter contracts |
| T08 | Next.js App Router, UI komponente, i18n, Security Center |
| T09 | Audit chain, OTel, metrike, CI workflowi, sigurnosne provjere |
| T10 | Test matrica, isolation report, security review, acceptance report |

Artefakti su navedeni kao očekivani rezultati; izvorni Blueprint ne tvrdi da su izrađeni.

## 4. Acceptance kriteriji po zadatku

| Zadatak | Uvjet prihvaćanja |
|---|---|
| T01 | Jasne granice modula, determinističke ovisnosti |
| T02 | Dokazano da testne usluge ne mogu pristupiti produkcijskom IMAP/SMTP-u |
| T03 | Migracije prolaze na praznoj i prethodnoj testnoj shemi; aplikacijska rola nema DDL |
| T04 | OpenAPI stabilan; TS klijent prolazi typecheck; autorizacija se ne zaobilazi |
| T05 | WebAuthn challenge replay odbijen; TOTP/recovery/session scenariji prolaze |
| T06 | Default deny, bez admin pristupa tuđoj pošti i eskalacije delegacijom |
| T07 | Nema izlaganja tajni; opoziv i rotacija testirani; nema stvarnih mrežnih operacija |
| T08 | Prijava i Security Center prolaze E2E, WCAG i šest jezika |
| T09 | Audit integritet provjerljiv; kritične radnje fail-closed; CI bez produkcijskih ovlasti |
| T10 | Svi obvezni testovi i neovisni review prolaze, nema otvorenih High/Critical nalaza |

**Sigurnosni blokatori:** Paket se ne smije prihvatiti ako postoji neovlašten pristup podacima, eskalacija ovlasti, neučinkovit opoziv sesije, izlaganje tajni, nedopušten pristup produkcijskoj infrastrukturi ili neuspješan kritični audit. Formalno prihvaćanje zahtijeva stvarne dokaze izvršenih testova.

## 5. Razdvajanje zadataka za agente

**Claude Code — programiranje.** Nakon posebnog Implementation GO: implementacija T01–T09, Python i TypeScript moduli, testovi, mock adapteri, tehnička dokumentacija. Ne pokreće produkcijske servise i ne obavlja GitHub merge.

**GitHub Copilot — Git i PR operacije.** Nakon zasebnog Git/PR GO: priprema grana, Pull Requestova, CI konfiguracije i evidencije statusnih provjera. Merge samo nakon izričitog odobrenja; bez deploymenta.

**Codex — neovisna revizija.** Provjera arhitekturnih granica, sigurnosti, pokrivenosti testovima, Alembic migracija, izolacije mreže i dokumentiranje nalaza. Revizija ne daje automatski GO.

## 6. Pravila GO odobravanja

| Vrsta odobrenja | Stanje u trenutku usvajanja Blueprinta |
|---|---|
| Architecture Baseline v1.0 | Potvrđen |
| Specifikacije P1-01–P1-09 | Potvrđene |
| Implementation Blueprint v1.0 | **Naknadno potvrđen korisničkom porukom navedenom niže** |
| Implementation GO | Nije izdan |
| Git/PR GO | Nije izdan |
| Merge GO | Nije izdan |
| Staging GO | Nije izdan |
| Production GO | Nije izdan |

Sva odobrenja ostaju zasebna i vezana uz konkretni opseg.

## 7. Buduća uputa za Claude Code (nacrt — NE IZVRŠAVATI)

**Referentna arhitektura:** Architecture Baseline v1.0, ADR-001–146.  
**Odobrene specifikacije:** P1-01–P1-09.  
**Status:** NEMA IMPLEMENTACIJSKOG GO.

Nakon zasebnog odobrenja implementiraj isključivo zadatak i podzadatke navedene u tom odobrenju.

**Obvezna arhitekturna pravila:**

- Monorepo s `apps/web`, `apps/api`, `apps/worker` i zajedničkim paketima.
- FastAPI `/api/v1` i generirani OpenAPI TypeScript klijent.
- Jedna PostgreSQL baza `webmail_db` s modularnim shemama i centralnim Alembicom.
- Passkey-first, MFA, server-side sesije, default-deny RBAC.
- Credential Broker i mock IMAP/SMTP/Admin Agent adapteri.
- Strukturirani audit, OpenTelemetry i sigurnosne CI provjere.
- Šest jezika i WCAG 2.2 AA za obuhvaćene frontend funkcije.

**Stroge zabrane:**

- Bez produkcijskog IMAP/SMTP pristupa.
- Bez produkcijskih tajni ili korisničkih podataka.
- Bez promjena postojećeg docker-mailservera.
- Bez produkcijskih PostgreSQL migracija.
- Bez neodobrenih Git operacija, mergea ili deploymenta.

**Za svaki odobreni zadatak isporuči:** popis promijenjenih datoteka, kratak opis implementacije, rezultate testiranja, sigurnosne nalaze i preostale rizike, odstupanja od specifikacije. Ne započinji sljedeći zadatak bez odobrenja.

## 8. Buduća uputa za GitHub Copilot (nacrt — NE IZVRŠAVATI)

Projekt: Webmail Paket 1 — Foundation & Security. **Status:** NEMA GIT/PR GO.

Nakon zasebnog odobrenja pripremi GitHub postupak za točno navedeni implementacijski zadatak.

**Obvezna pravila:** zaštita `main` grane; zaseban PR za odobreni opseg; obvezni CI i sigurnosne provjere; poveznice na P1 specifikacije; dokumentirani testni rezultati; bez automatskog mergea ili produkcijskog deploymenta; bez produkcijskih tajni u GitHub Actions.

**Izlaz:** PR opis, popis promjena, rezultati provjera, rizici i uvjeti za review. Ne spajaj PR bez izričitog Merge GO.

## 9. Buduća uputa za Codex (nacrt — NE IZVRŠAVATI)

Referentni dokumenti: Architecture Baseline v1.0, ADR-001–146, P1-01–P1-09 i ovaj Blueprint v1.0.

Neovisna revizija samo nad dostupnim i izričito odobrenim artefaktima: granice modula, PostgreSQL/Alembic, Passkey/MFA/recovery/sesije, RBAC i delegacije, Credential Broker, CSRF/XSS/CSP, audit integritet, redakcija logova, CI, mrežna izolacija, test coverage i Acceptance Gate.

**Izvještaj:** ozbiljnost, dokaz, relevantni ADR/P1 zahtjev, preporučena korekcija i status provjere. Bez promjene koda, infrastrukture ili GitHub stanja bez odobrenja. Bez samostalnog Implementation/Merge/Production GO.

## 10. Formalna potvrda

**Izvorna korisnička poruka, 2026-11-22 u 05:47:35 UTC:**

> Potvrđujem Webmail Paket 1 Implementation Blueprint v1.0, radne zadatke T01–T10, njihove ovisnosti, artefakte, acceptance kriterije i odvojene uloge Claude Code, Copilot i Codex. Sljedeće pripremi detaljnu specifikaciju T01 Monorepo & Development Foundation. Bez implementacijskog, Git, merge ili deployment GO.

**Važeći status:** Blueprint v1.0 potvrđen, Implementation/Git/PR/Merge/Staging/Production GO nije izdan ovom odlukom.