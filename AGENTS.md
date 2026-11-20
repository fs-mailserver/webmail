# AGENTS.md: Upute i pravila za AI agente

Ovaj dokument propisuje stroga pravila, standarde koda i redoslijed izvođenja za sve AI agente i programere koji rade na ovom monorepo projektu.

---

## 1. Temeljna načela arhitekture

1. **Čiste granice monorepa:**
   - Sav backend kod ide isključivo u `backend/`.
   - Sav frontend kod ide isključivo u `frontend/`.
   - Ne miješati biblioteke niti dependencies između backenda i frontenda.
   - Sve promjene konfiguracije kontejnera usklađuju se u `compose.yaml`.

2. **Nikada ne blokirati Event Loop:**
   - Backend je 100% asinkron (FastAPI + `async def`).
   - Sve I/O operacije (baza, IMAP, SMTP, datotečni sustav) moraju koristiti asinkrone biblioteke (`asyncpg`, `aioimaplib`, `aiosmtplib`, `aiofiles`).
   - Ako je nužno pozvati sinkroni kod (npr. `docker` python SDK ili `firebase-admin`), obavezno ga omotati s `anyio.to_thread.run_sync` ili `starlette.concurrency.run_in_threadpool`.

3. **Sigurnost kredencijala i privatnost:**
   - Lozinke korisnika se hashiraju s `bcrypt` / `argon2`.
   - IMAP/SMTP lozinke se u bazi pohranjuju isključivo enkriptirane Fernet algoritmom (`MAILBOX_CREDENTIAL_ENCRYPTION_KEY`).
   - Nikada ne ispisivati sirove lozinke u logove ili odgovore API-ja (`[redacted-password]`).
   - HTML e-mail poruke se na frontendu moraju renderirati isključivo u sandboxed `<iframe>` elementu uz blokiranje vanjskih slika po defaultu.

---

## 2. Standardi za Backend (FastAPI + SQLAlchemy 2.0 Async)

1. **Python verzija:** Python 3.12+
2. **SQLAlchemy 2.0 stil:**
   - Koristiti deklarativni stil s `Mapped[...]` i `mapped_column(...)`.
   - Upiti se pišu isključivo preko 2.0 `select()`, nikada preko legacy `query()`.
   - Sve bazične operacije koriste `AsyncSession` dobiven preko FastAPI dependency injekcije (`get_db_session`).
3. **Migracije (Alembic):**
   - Nema ručnog kreiranja tablica u produkciji. Svaka promjena modela mora imati generiranu Alembic migraciju (`alembic revision --autogenerate`).
4. **Validacija i tipizacija (Pydantic v2):**
   - Strogi tipovi za sve ulazne i izlazne podatke (`response_model`).
   - Korištenje `ConfigDict(from_attributes=True)`.
5. **Rukovanje greškama:**
   - Definirati unificirane HTTP iznimke (`HTTPException` s jasnim `detail` porukama).
6. **Testovi:**
   - `pytest` i `pytest-asyncio` s mockanim IMAP/SMTP sesijama.

---

## 3. Standardi za Frontend (Next.js 15 + TypeScript)

1. **Next.js App Router:**
   - Korištenje Next.js 15 (ili zadnje stabilne verzije) sa strogim TypeScript postavkama (`strict: true`, bez `any`).
2. **UI komponente:**
   - Tailwind CSS + **shadcn/ui** primitivi (Zinc tema).
   - Tamna tema je zadana (`dark` class preko `next-themes`), uz podršku za svjetlu temu i sustavnu sinkronizaciju.
   - Lucide React za sve ikone.
3. **Upravljanje stanjem i podacima:**
   - **TanStack Query (React Query v5)** za sve serverske podatke i cache.
   - WebSocket kuka (`useMailWebSocket`) prima događaje s backend-a i poziva `queryClient.invalidateQueries` ili radi optimistične updateove u listi.
   - Frontend **nikada** ne čeka direktan IMAP poziv — podaci dolaze u par milisekundi iz lokalne baze.
4. **Virtualizacija:**
   - Za listu poruka u srednjem stupcu **obavezno** koristiti `@tanstack/react-virtual` kako bi skrolanje kroz tisuće mailova ostalo na 60 FPS.
5. **Tipkovničke kratice:**
   - Korištenje `hotkeys-js` kroz centraliziranu kuku `useHotkeys`.
   - Onemogućiti aktivaciju kratica (osim `Cmd+Enter` i `Escape`) dok je fokus unutar polja za unos teksta (`input`, `textarea`, `tiptap contenteditable`).

---

## 4. Faze implementacije (Redoslijed za agente)

Agenti moraju rješavati zadatke striktno po ovim fazama:

### Faza 1: Temelj, Baza i Kredencijali
1. Postaviti `backend/` strukturu s `pyproject.toml`, FastAPI aplikacijom i Dockerfile-om.
2. Definirati SQLAlchemy 2.0 async modele prema `SPEC.md` (`User`, `Account`, `Folder`, `Thread`, `Message`, `Attachment`, `SenderBlocklistRule`, `DeviceRegistration`).
3. Konfigurirati Alembic i generirati početne migracije za PostgreSQL.
4. Implementirati enkripciju lozinki (`cryptography.fernet`) i JWT autentifikaciju (`/api/v1/auth/login`, `/api/v1/auth/me`).
5. Urediti `compose.yaml` za podizanje baze, redis-a i backend servisa.

### Faza 2: IMAP Sync Engine & WebSocket Realtime
1. Implementirati Dovecot Sieve webhook prijemnik (`POST /api/v1/sync/sieve-webhook`) za 0ms detekciju novih mailova.
2. Razviti MIME parser koji ekstrahira čist tekst, HTML, zaglavlja i privitke (sprema privitke na disk u `/app/storage/attachments`).
3. Implementirati pozadinski `aioimaplib` IDLE worker za praćenje promjena zastavica i sinkronizaciju mapa.
4. Postaviti WebSocket poslužitelj s Redis Pub/Sub sabirnicom za distribuciju live događaja klijentima.

### Faza 3: Next.js 3-Pane UI (Desktop Web klijent)
1. Inicijalizirati `frontend/` s Next.js 15, Tailwindom, shadcn/ui i tamnom temom.
2. Izraditi 3-Pane Resizable Layout (`react-resizable-panels`):
   - Lijevi stupac: Unified Inbox i stablo računa s dodijeljenim bojama.
   - Srednji stupac: Virtualizirana lista poruka (`@tanstack/react-virtual`), brzi filteri i pretraga.
   - Desni stupac: ThreadView, sandboxed `<iframe>` za HTML, blokada vanjskih slika i galerija privitaka.
3. Spojiti TanStack Query i WebSocket kuku za automatsko osvježavanje bez treptanja ekrana.
4. Implementirati prečace tipkovnice (`J`/`K`, `R`, `E`, `Delete`, `Cmd+K`).

### Faza 4: Slanje, Tiptap Composer, AI & Administratorske funkcije
1. Implementirati Tiptap editor za pisanje novih mailova (Floating modal na tipku `C`) i brzi Inline Reply na dnu threada.
2. Dodati SMTP slanje preko `aiosmtplib` s automatskim spremanjem u mapu `Sent` i potpisima po računu.
3. Integrirati AI adaptere (Gemini i OpenAI) za 1-klik sažimanje threada i Smart Reply prijedloge odgovora.
4. Reimplementirati administratorske funkcije u FastAPI i dodati Next.js Admin tab:
   - Upravljanje mailboxima preko Docker socket API-ja (`setup email add/del/list`).
   - Postfix sender blocklist uređivač s `postfix reload` i 1-klik blokiranjem u pregledu poruke.
   - FCM push relay servis za obavijesti na mobilne telefone.

---

## 5. Protokol za verifikaciju i provjeru koda

Prije predaje bilo kojeg dijela posla, agent mora provjeriti:
1. **Backend:**
   - `pytest` prolazi bez grešaka.
   - FastAPI server se podiže bez grešaka i generira ispravan OpenAPI schema (`/openapi.json`).
   - Alembic migracije se uspješno primjenjuju na bazu (`alembic upgrade head`).
2. **Frontend:**
   - TypeScript provjera prolazi bez ijednog tipskog upozorenja (`npm run build` ili `npx tsc --noEmit`).
   - Nema hydration pogrešaka na konzoli preglednika.
3. **Integracija:**
   - Kontejneri u `compose.yaml` se podižu bez rušenja (`docker compose ps` prikazuje zdrave kontejnere).

