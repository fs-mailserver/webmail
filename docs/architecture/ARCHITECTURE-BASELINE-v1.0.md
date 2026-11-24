# Webmail — Architecture Baseline v1.0 (objedinjeni dokument)

> **Status arhitekturnih odluka:** Zaključene potvrdom ADR-146, 22. 11. 2026., 05:40:05 UTC.  
> **Status ove datoteke:** Naknadno sastavljen referentni pregled (24. 11. 2026.), **nije izvorni, doslovno objavljeni Baseline dokument**.  
> **Mjerodavni izvori:** [ADR registar](../adr/ADR-REGISTER.md), [ADR-146](../adr/ADR-146.md), [Implementation Blueprint v1.0](IMPLEMENTATION-BLUEPRINT-v1.0.md), [P1-01–P1-09](../specifications/), [T01 specifikacija](../specifications/T01.md), [T01 Execution Order](../execution-orders/T01.md).  
> **GO status:** Bez Implementation, Git/PR, Merge, Staging, Pilot ili Production GO.

## 1. Podrijetlo i ograničenja

U korisnikovom izvozu ChatGPT razgovora `GitHub Repozitorij pregled` (conversation ID `6b0020d4-c274-83eb-b3da-0a31ff5bc3d9`) pronađena je **izričita potvrda ADR-146** i zaključavanje naziva *Webmail Architecture Baseline v1.0*. Provjera relevantnih poruka nije pronašla zasebno objavljen, cjeloviti dokument Baselinea; ADR-146 u izvornom prijedlogu tek predlaže njegovu izradu. Stoga je ovaj dokument **novi konsolidirani indeks zaključene arhitekture**, ne rekonstrukcija navodnog izgubljenog izvornika.

Ovdje navedene sažete arhitekturne tvrdnje treba uvijek čitati uz puni sadržaj nadležnog ADR-a i kasnije prihvaćene specifikacije. Ako postoji konflikt, ne mijenjati povijesni izvor bez dokumentiranog amandmana. Ovaj pregled sam po sebi nije nova arhitekturna odluka.

## 2. Namjena i osnovna arhitektura

**Cilj:** Novi samohostirani Webmail, buduća zamjena za SnappyMail, uz zadržavanje postojećeg Postfix/Dovecot mailservera kao autoritativnog sustava za poštu.

```text
Next.js Webmail / Admin Console (UI, PWA, više jezika)
              |
          /api/v1
              v
FastAPI (Identity / Authorization / Mail API / Operations)
       |           |             |              |
   PostgreSQL   Celery/Redis   Credential     Privilegirani
    aplikacija  workers/jobs     Broker       Mail Admin Agent
       |           |             |              |
       +-----------+-------------+--------------+
                           |
               adapteri za vanjski mailserver
                           |
           Postfix SMTP / Dovecot IMAP (izvor istine)
```

- **Pošta:** Dovecot/IMAP je izvor istine za poruke, mape i zastavice; Postfix je mail transport. [ADR-001](../adr/ADR-001.md), [ADR-003](../adr/ADR-003.md), [ADR-146](../adr/ADR-146.md).
- **Sinkronizacija:** hibridni Sieve signal + IMAP IDLE + periodični reconciliation, uz IMAP `UIDVALIDITY`/`UID`. ADR-003 je izričito naknadno potvrđen 23. 11. 2026. [ADR-003](../adr/ADR-003.md).
- **Baza:** PostgreSQL s Webmail identitetom, autorizacijom, nacrtima, metapodacima i indeksima; izvorna potvrda ADR-004 dopušta i pohranu **punog teksta poruka** u PostgreSQL-u radi pretrage. Nemoj reducirati ADR-004 na *samo metapodatke*. [ADR-004](../adr/ADR-004.md), [P1-02](../specifications/P1-02.md).
- **Autorizacija:** prava na poštu odvojena od administratorske uloge; default-deny i granularni mailbox grantovi. [ADR-146](../adr/ADR-146.md), [P1-04](../specifications/P1-04.md).
- **Tajne i privilegirani rad:** Credential Broker i izdvojeni ograničeni Mail Admin Agent; bez izlaganja tajni aplikacijskom sloju i bez automatskog admin pristupa sadržaju poruka. [P1-06](../specifications/P1-06.md).
- **Frontend/API/worker:** Next.js + TypeScript, FastAPI + Python, Celery + Redis. Frontend ne pristupa izravno PostgreSQL-u, IMAP-u ili SMTP-u. [P1-01](../specifications/P1-01.md), [P1-05](../specifications/P1-05.md), [P1-07](../specifications/P1-07.md).

## 3. Paketizacija i ovisnosti

| Paket | Opseg | Preduvjet |
|---|---|---|
| 1 — Foundation & Security | Monorepo, izolacija, testna baza/migracije, API, Identity/Passkeys/MFA, RBAC, Credential Broker, mock adapteri, frontend shell, audit i CI | Nema produkcijskih integracija |
| 2 — Mail Sync | IMAP sinkronizacija, checkpointi, UIDVALIDITY i indeks | Paket 1 prihvaćen |
| 3 — Inbox & Composer | Inbox, nacrti, SMTP, Sent, privitci | Paketi 1–2 |
| 4 — Admin & Operations | Domene, mailboxi, administracija, monitoring | Paketi 1–3 |
| 5 — Hardening & Release | Sigurnosne, E2E, DR, WCAG i pilot provjere | Svi prethodni |

**Važna granica:** Paket 1 je odobren kao **specifikacija**, a ne za izvršavanje. Konkretan raspored zadataka unutar njega definira [Implementation Blueprint v1.0](IMPLEMENTATION-BLUEPRINT-v1.0.md).

## 4. Paket 1: T01–T10

| Zadatak | Rezultat | Ovisnost |
|---|---|---|
| T01 | Monorepo & Development Foundation | — |
| T02 | Izolirano testno okruženje | T01 |
| T03 | PostgreSQL / Alembic | T01–T02 |
| T04 | FastAPI / OpenAPI | T01–T03 |
| T05 | Identity & Authentication | T03–T04 |
| T06 | Authorization Service | T03–T05 |
| T07 | Credential Broker i **mock** adapteri | T04–T06 |
| T08 | Next.js Frontend Foundation | T04–T06 |
| T09 | Audit, Observability & CI | T01–T08 |
| T10 | Integration & Acceptance | T01–T09 |

Detaljni zahtjevi: [P1-01](../specifications/P1-01.md), [P1-02](../specifications/P1-02.md), [P1-03](../specifications/P1-03.md), [P1-04](../specifications/P1-04.md), [P1-05](../specifications/P1-05.md), [P1-06](../specifications/P1-06.md), [P1-07](../specifications/P1-07.md), [P1-08](../specifications/P1-08.md), [P1-09](../specifications/P1-09.md).

## 5. Sigurnosne granice Paketa 1

- Isključivo izolirano razvojno/testno okruženje i sintetički podaci.
- Nema stvarne IMAP/SMTP veze s produkcijskim Dovecotom/Postfixom.
- Nema produkcijskih vjerodajnica, mailboxa, produkcijske baze ili migracija.
- Mail Admin Agent radi isključivo kao simulirani mock, bez Docker socketa ili privilegiranog produkcijskog pristupa.
- Ne mijenjati postojeći produkcijski Docker Compose, mailserver ili SnappyMail.
- Ne pokretati automatsko spajanje grana, staging/pilot ili produkcijski deployment.
- Bez zasebnih i izričitih GO odobrenja nema implementacije, Git/PR radnji, mergea ili deploymenta.

## 6. Formalni acceptance gate

- **T01:** CP-01–CP-05 i T01-AC01–T01-AC10; rezultati testova moraju imati stvaran dokaz, u protivnom `NOT VERIFIED`. [T01 nalog](../execution-orders/T01.md).
- **Paket 1:** obvezni unit, integration, contract, E2E, security, isolation, recovery, WCAG i i18n testovi, negativni RBAC/MFA/CSRF scenariji, bez otvorenih High/Critical sigurnosnih nalaza; neovisni review i Acceptance Report. [P1-09](../specifications/P1-09.md).
- **Promjene:** svaki korak od implementacije do releasea ima zasebni approval gate. [ADR-146](../adr/ADR-146.md), [Blueprint](IMPLEMENTATION-BLUEPRINT-v1.0.md).

## 7. Tehničke pretpostavke koje treba tek provjeriti

| Tema | Još nije potvrđeno operativnim testom |
|---|---|
| Dovecot | Točno IMAP QRESYNC/CONDSTORE i autentifikacijsko ponašanje instalirane verzije |
| Postfix | SMTP autorizacija, identifikacija slanja i korelacija s redom |
| Broker | Model leasinga i opoziva tajni te izolacija privilegiranih operacija |
| PostgreSQL | FTS jezici, indeksiranje, kapacitet, migracije i stvarne role |
| Docker/Traefik | Mrežna izolacija, proxy `/api`/`/ws`, TLS/cookie pravila |
| Backup/DR | Dosljednost kopija baze, Maildir i storagea, recovery ključevi i povratak na SnappyMail |

Arhitekturna potvrda nije dokaz da produkcijska konfiguracija već podržava svaku navedenu mogućnost. Ova tablica nije dozvola za pristup produkciji.

## 8. Izvori, evidencija i prioritet

1. [ADR-146 — izvorna potvrda Baselinea](../adr/ADR-146.md) i [ADR-REGISTER](../adr/ADR-REGISTER.md).
2. [Potvrđene P1-01–P1-09 specifikacije](../specifications/) i [Blueprint v1.0](IMPLEMENTATION-BLUEPRINT-v1.0.md).
3. [T01 specifikacija](../specifications/T01.md) i [T01 izvršni nalog](../execution-orders/T01.md).
4. Dokumentacijska provjera izvoza: razgovor `GitHub Repozitorij pregled`, 22. 11. 2026., ADR-146 korisnička potvrda u 05:40:05 UTC; kasniji T01 Preflight 1.20–1.23 potvrđuje da puni povijesni dokument nije zasebno objavljen.

**Zaključak:** Zaključena arhitekturna odluka iz 2026. i novi konsolidirani dokument nisu isto. Ovaj dokument služi za navigaciju i provedbenu sljedivost, bez dodavanja novih pravila i bez Implementation GO.