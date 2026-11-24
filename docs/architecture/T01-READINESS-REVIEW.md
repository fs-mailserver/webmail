# T01 — Documentation & Implementation Readiness Review

**Datum pregleda:** 2026-11-24  
**Repozitorij:** `fs-mailserver/webmail`, `main`  
**Opseg:** samo čitanje izvornog sadržaja i dokumentacijska provjera; bez implementacije, izvršavanja testova i deploymenta.  
**Zaključak:** **CONDITIONAL / DOCUMENTATION GAP** — ne izdavati Implementation GO samo na temelju ovog pregleda.

## 1. Provjerene referencije

| Izvor | Nalaz |
|---|---|
| `docs/adr/ADR-001.md` – `ADR-146.md` | 146 datoteka postoje; potvrde evidentirane (ADR-001/002 kontekstualne, ADR-003–146 izričite) |
| `docs/specifications/P1-01.md` – `P1-09.md` | svih devet prisutno |
| `docs/architecture/IMPLEMENTATION-BLUEPRINT-v1.0.md` | prisutan; T01–T10 definirani |
| `docs/architecture/IMPLEMENTATION-BLUEPRINT-v1.0-SOURCE.md` | izvorni zapis prisutan |
| `docs/specifications/T01.md` | prisutan; T01-AC01–T01-AC10 |
| `docs/execution-orders/T01.md` | prisutan; CP-01–CP-05 i T01-AC01–T01-AC10 |
| Architecture Baseline v1.0 | **nije pronađen zaseban dokument u trenutačnom Git stablu** |
| `README.md`, `AGENTS.md` | postoje; pravila za odvojene GO ovlasti |

Provjera je provedena nad GitHub `main` nakon commita `f7e03546a2efe510f656cf6cf94cd56e2d974da6`.

## 2. Otvorena pitanja i blokatori

### DOC-01 — nedostaje zaseban Architecture Baseline v1.0 (dokumentacijski blokator)

Blueprint, P1-01 i T01 nalog pozivaju se na Architecture Baseline v1.0. U provjerenom Git stablu nije pronađena datoteka s tim nazivom.

**Preporučena radnja:** pronaći puni izvornik u korisničkom ChatGPT izvozu, sačuvati izvornu verziju i potvrdu te provjeriti usklađenost s ADR-001–146. Ne rekonstruirati povijesni izvor iz sažetaka.

### DOC-02 — zastarjela tvrdnja u README.md (dokumentacijsko odstupanje)

`README.md` još tvrdi da puni izvorni tekstovi ADR-ova nisu verificirani. Nakon obnove ADR-001–146, ta je tvrdnja zastarjela. Potrebno je ažurirati status uz očuvanje oznake kontekstualne potvrde za ADR-001/002.

### DOC-03 — arhivirane specifikacije sadrže povijesne UI oznake (uredničko ograničenje)

Izvorni P1 i T01 dokumenti namjerno čuvaju tekst nacrta i prikazne UI oznake. Mjerodavna je eksplicitna potvrda izdvojena u zaglavlju/odjeljku potvrde; oznaka `DRAFT` u izvornom prijedlogu ne poništava naknadnu potvrdu. Nijedan dokument ne predstavlja Implementation GO.

## 3. Trenutačni T01 kostur — inventura

U repozitoriju postoje samo direktoriji/README placeholderi za `apps/web`, `apps/api`, `apps/worker`, `packages/backend`, `packages/ui`, `packages/api-client`, `infra`, `tests`, te `AGENTS.md`, `README.md`, `.gitignore`, `.editorconfig`.

Nisu pronađeni `pnpm-workspace.yaml`, korijenski `package.json`, `pyproject.toml`, minimalne izvršne ulazne točke pod `apps/*/src`, centralni `migrations/`, poddirektoriji testova niti potrebne konfiguracije. **To su nedostajući implementacijski artefakti T01, a ne dokazi neuspjeha**, jer Implementation GO nije izdan.

Nisu pokretani buildovi, testovi, Docker niti mrežne provjere. T01-AC01–T01-AC10 ostaju **NOT VERIFIED** kao izvršni kriteriji.

## 4. Granice i odluka

- **Documentation:** ADR/P1/Blueprint/T01 uglavnom usklađeni po opsegu i redoslijedu; treba obnoviti Architecture Baseline v1.0 i ispraviti status README-ja.
- **Implementation:** nije odobrena ovim pregledom.
- **Git/PR, merge, deployment:** zasebne ovlasti; nisu odobrene ovim pregledom.
- **Production:** nije dirana.
- **Sljedeći korak:** obnoviti Architecture Baseline v1.0 iz izvoza razgovora, zatim ažurirati ovaj readiness pregled prije eventualnog zahtjeva za zasebni T01 Implementation GO.
