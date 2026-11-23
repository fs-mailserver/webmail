# Webmail — Paket 1 Implementation Blueprint v1.0 — izvorni zapis

- **Status:** izvorna verzija, neizmijenjena; potvrđena 2026-11-22.
- **Izvor:** korisnički izvoz ChatGPT razgovora `GitHub Repozitorij pregled` (`6b0020d4-c274-83eb-b3da-0a31ff5bc3d9`).
- **Izvorni odgovor asistenta:** 2026-11-22 05:46:56 UTC.
- **Napomena:** izvor sadrži izvorne UI oznake i neizvršive kontrole; služi za reviziju tekstualne vjernosti.

## Izvorni tekst Blueprinta (verbatim)

<row align="center" gap={2}>
  <icon name="check-circle" color="success"/>
  **Implementation Blueprint v1.0 — pripremljen za pregled**
</row>

Objedinjujemo svih devet potvrđenih specifikacija P1-01–P1-09 u jedan provedbeni plan za **Webmail Paket 1 — Foundation & Security**.

Blueprint definira konkretne radne cjeline, ovisnosti, očekivane rezultate, kriterije prihvaćanja i zasebne odgovornosti agenata. Ovo je **plan za buduću implementaciju**, ne nalog za njezino pokretanje.

# Webmail — Paket 1 Implementation Blueprint v1.0

<row align="center" gap={2} wrap="wrap">
  <badge color="secondary">SPECIFIKACIJA</badge>
  <text color="secondary" size="xs">Architecture Baseline v1.0 · ADR-001–146 · P1-01–P1-09</text>
</row>

## 1. Cilj i granice

Paket 1 uspostavlja izolirani razvojni temelj novog Webmail sustava koji će kasnije zamijeniti SnappyMail.

<box border radius="lg" padding={3} gap={2}>
  **U opsegu Paketa 1**
  <text size="sm">Monorepo, FastAPI, Next.js, Celery, PostgreSQL/Alembic, Passkey/MFA, RBAC, Credential Broker, mock adapteri, sigurnosni audit, CI i početni PWA.</text>
  <divider color="subtle"/>
  **Izvan opsega**
  <text size="sm">Stvarni IMAP/SMTP, sadržaj e-mailova, Inbox, Composer, produkcijski mailboxi, produkcijski PostgreSQL, izmjene mailservera, pilot i deployment.</text>
</box>

## 2. Radni paketi i ovisnosti

Predlažem deset tehničkih zadataka, poredanih tako da svaki ima provjerljiv rezultat.

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

Artefakti su navedeni kao očekivani rezultati. Nijedan još nije izrađen.

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

### Obvezni sigurnosni blokatori

Paket se ne smije prihvatiti ako postoji neovlašten pristup podacima, eskalacija ovlasti, neučinkovit opoziv sesije, izlaganje tajni, nedopušten pristup produkcijskoj infrastrukturi ili neuspješan kritični audit.

Za formalno prihvaćanje zahtijeva se stvarni dokaz izvršenih testova, ne samo oznaka da su testovi napisani.

## 5. Razdvajanje zadataka za agente

<box gap={3}>
  <row align="start" gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="code-2" size="lg"/>
    </box>
    <box flex="1" gap={1}>
      **Claude Code — programiranje**

      <text color="secondary" size="sm">Nakon posebnog Implementation GO: implementacija T01–T09, Python i TypeScript moduli, testovi, mock adapteri, tehnička dokumentacija. Ne pokreće produkcijske servise i ne obavlja GitHub merge.</text>
    </box>
  </row>
  <divider color="subtle"/>
  <row align="start" gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="git-pull-request" size="lg"/>
    </box>
    <box flex="1" gap={1}>
      **GitHub Copilot — Git i PR operacije**

      <text color="secondary" size="sm">Nakon zasebnog Git/PR GO: priprema grana, Pull Requestova, CI konfiguracije i evidencije statusnih provjera. Merge samo nakon izričitog odobrenja; bez deploymenta.</text>
    </box>
  </row>
  <divider color="subtle"/>
  <row align="start" gap={3}>
    <box background="surface-secondary" radius="lg" padding={3}>
      <icon name="scan-search" size="lg"/>
    </box>
    <box flex="1" gap={1}>
      **Codex — neovisna revizija**

      <text color="secondary" size="sm">Provjera arhitekturnih granica, sigurnosti, pokrivenosti testovima, Alembic migracija, izolacije mreže i dokumentiranje nalaza. Revizija ne daje automatski GO.</text>
    </box>
  </row>
</box>

## 6. Pravila GO odobravanja

| Vrsta odobrenja | Trenutačno stanje |
|---|---|
| Architecture Baseline v1.0 | Potvrđen |
| Specifikacije P1-01–P1-09 | Potvrđene |
| Implementation Blueprint v1.0 | Pripremljen, čeka pregled |
| Implementation GO | Nije izdan |
| Git/PR GO | Nije izdan |
| Merge GO | Nije izdan |
| Staging GO | Nije izdan |
| Production GO | Nije izdan |

Sva odobrenja ostaju zasebna i vezana uz konkretni opseg.

## 7. Predložak buduće upute za Claude Code

Ovo je pripremljeni tekst zadatka, **nije poslan agentu**.

<WritingBlock id="74182" variant="document"># Webmail — Paket 1: Foundation & Security

## Zadatak za Claude Code — nacrt, NE IZVRŠAVATI

Referentna arhitektura: Architecture Baseline v1.0, ADR-001–146.

Odobrene specifikacije: P1-01–P1-09.

**Trenutačni status: NEMA IMPLEMENTACIJSKOG GO.**

Nakon zasebnog odobrenja implementiraj isključivo zadatak i podzadatke navedene u tom odobrenju.

### Obvezna arhitekturna pravila

- Monorepo s `apps/web`, `apps/api`, `apps/worker` i zajedničkim paketima.
- FastAPI `/api/v1` i generirani OpenAPI TypeScript klijent.
- Jedna PostgreSQL baza `webmail_db` s modularnim shemama i centralnim Alembicom.
- Passkey-first, MFA, server-side sesije, default-deny RBAC.
- Credential Broker i mock IMAP/SMTP/Admin Agent adapteri.
- Strukturirani audit, OpenTelemetry i sigurnosne CI provjere.
- Šest jezika i WCAG 2.2 AA za obuhvaćene frontend funkcije.

### Stroge zabrane

- Bez produkcijskog IMAP/SMTP pristupa.
- Bez produkcijskih tajni ili korisničkih podataka.
- Bez promjena postojećeg docker-mailservera.
- Bez produkcijskih PostgreSQL migracija.
- Bez neodobrenih Git operacija, mergea ili deploymenta.

### Za svaki odobreni zadatak isporuči

1. Popis promijenjenih datoteka.
2. Kratki opis implementacije.
3. Rezultate testiranja.
4. Sigurnosne nalaze i preostale rizike.
5. Odstupanja od specifikacije, ako postoje.

Ne započinji sljedeći zadatak bez odgovarajućeg odobrenja.
</WritingBlock>

## 8. Predložak buduće upute za Copilot

<WritingBlock id="74183" variant="document"># Webmail — GitHub & PR Workflow

## Zadatak za GitHub Copilot — nacrt, NE IZVRŠAVATI

Projekt: Webmail, Paket 1 — Foundation & Security.

**Trenutačni status: NEMA GIT/PR GO.**

Nakon zasebnog odobrenja pripremi GitHub postupak za točno navedeni implementacijski zadatak.

### Obvezna pravila

- Zaštita grane `main`.
- Zaseban PR za odobreni opseg.
- Obvezne CI i sigurnosne provjere.
- Poveznice na pripadajuće P1 specifikacije.
- Dokumentirani testni rezultati.
- Bez automatskog mergea.
- Bez automatskog produkcijskog deploymenta.
- Bez produkcijskih tajni u GitHub Actions.

### Izlazni rezultat

Pripremi PR opis, popis promjena, rezultate provjera, rizike i uvjete za review.

Ne spajaj PR bez izričitog Merge GO.
</WritingBlock>

## 9. Predložak buduće upute za Codex

<WritingBlock id="74184" variant="document"># Webmail — Independent Architecture & Security Review

## Zadatak za Codex — nacrt, NE IZVRŠAVATI

Referentni dokumenti: Architecture Baseline v1.0, ADR-001–146, P1-01–P1-09 i Paket 1 Implementation Blueprint v1.0.

Provedi neovisnu reviziju samo nad artefaktima koji budu dostupni i izričito odobreni za pregled.

### Fokus revizije

- Granice modula i dependency pravila.
- PostgreSQL i Alembic sigurnost.
- Passkey, MFA, recovery i sesije.
- RBAC, delegacije i zabrana eskalacije ovlasti.
- Credential Broker i izolacija mock adaptera.
- CSRF/XSS/CSP zaštita.
- Audit integritet, redakcija logova i CI.
- Dokazi mrežne izolacije.
- Test coverage i Acceptance Gate.

### Izvještaj

Za svaki nalaz navedi ozbiljnost, dokaz, relevantni ADR/P1 zahtjev, preporučenu korekciju i status provjere.

Ne mijenjaj kod, infrastrukturu ni GitHub stanje bez zasebnog odobrenja. Ne izdaji samostalno Implementation, Merge ili Production GO.
</WritingBlock>

## 10. Sljedeća odluka

Sadržaj Blueprinta sada je pripremljen. Prije bilo kakvog programiranja predlažem njegovu **formalnu provjeru i zaključavanje**, pa tek zatim zasebnu odluku o prvom konkretnom zadatku.

{@body const [choice,setChoice] = DIL.useState("review")}
<box border radius="lg" padding={3} gap={3}>
  <radio-group direction="col" value={choice} onChange={setChoice}>
    <radio value="review">
      **A — Potvrdi Blueprint v1.0 i pripremi prvi zadatak T01 (preporučujem)**

      <text color="secondary" size="sm">Zaključujemo plan i sljedeće detaljno definiramo T01 — Monorepo & Development Foundation, bez izvršavanja.</text>
    </radio>
    <radio value="audit">
      **B — Prije potvrde napravi provjeru svih ovisnosti i sigurnosnih rizika**

      <text color="secondary" size="sm">Dodatno analiziramo postojeći Blueprint, moguće arhitekturne praznine i slijed zadataka, bez implementacije.</text>
    </radio>
  </radio-group>
  <button block onClick={()=>GenUI.issueNewTurn(choice==="review"?"Potvrđujem Webmail Paket 1 Implementation Blueprint v1.0, radne zadatke T01–T10, njihove ovisnosti, artefakte, acceptance kriterije i odvojene uloge Claude Code, Copilot i Codex. Sljedeće pripremi detaljnu specifikaciju T01 Monorepo & Development Foundation. Bez implementacijskog, Git, merge ili deployment GO.":"Prije potvrde Blueprinta v1.0 napravi završnu provjeru ovisnosti T01–T10, sigurnosnih granica, rizika i mogućih arhitekturnih nedosljednosti. Bez implementacijskog, Git, merge ili deployment GO.")}>Potvrdi sljedeći korak</button>
</box>

**Trenutačni status:** 146 arhitekturnih odluka i P1-01–P1-09 potvrđeni. Blueprint v1.0 pripremljen za pregled. Nijedan agent nije pokrenut, nijedna datoteka nije izmijenjena i nijedna produkcijska operacija nije odobrena.

---

## Korisnička potvrda (verbatim, 2026-11-22 05:47:35 UTC)

> Potvrđujem Webmail Paket 1 Implementation Blueprint v1.0, radne zadatke T01–T10, njihove ovisnosti, artefakte, acceptance kriterije i odvojene uloge Claude Code, Copilot i Codex. Sljedeće pripremi detaljnu specifikaciju T01 Monorepo & Development Foundation. Bez implementacijskog, Git, merge ili deployment GO.