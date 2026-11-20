# SPEC.md: Arhitektura i tehnička specifikacija modernog Webmail klijenta

## 1. Pregled i ciljevi projekta
Cilj projekta je zamjena postojećih rješenja (SnappyMail i Django `blocklist-admin`) s novim, iznimno brzim, samohostiranim monorepo webmail sustavom.

Sustav se sastoji od:
1. **Frontend:** **Next.js 15 (App Router, TypeScript, Tailwind CSS, shadcn/ui)** — optimiziran za osjećaj desktop aplikacije (Superhuman / Linear UX) uz 3-pane resizable layout, virtualizirano skrolanje na 60 FPS, tipkovničke kratice i instantno učitavanje.
2. **Backend:** **FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 17 + Redis** — hibridno spremanje metapodataka i `tsvector` indeksa za pretragu u bazi, dok se sirove `.eml` poruke i privitci pohranjuju na disk.
3. **IMAP & Real-Time Sync:** Dvostruki mehanizam: Dovecot Sieve webhook (0ms latencija za nove poruke) + pozadinski `aioimaplib` IDLE worker za praćenje promjena zastavica (pročitano, obrisano) s vanjskih klijenata, uz distribuciju događaja preko WebSocketa.
4. **Admin & Mailbox Ops:** Integrirano upravljanje Docker Mailserverom (dodavanje/brisanje mailboxa preko Docker socket API-ja), Postfix sender blocklist i Firebase Cloud Messaging (FCM) push notifikacije za mobilne uređaje.
5. **AI asistent:** Ugrađeni adapter za Gemini i OpenAI za 1-klik sažimanje dugih threadova i generiranje pametnih prijedloga odgovora (Smart Reply).

---

## 2. Struktura monorepo repozitorija

Repozitorij je smješten unutar `webmail` sa sljedećom strukturom:

```text
webmail/
├── compose.yaml                # Glavni Docker Compose (mailserver, db, redis, backend, frontend, worker)
├── SPEC.md                     # Ovaj arhitektonski nacrt
├── AGENTS.md                   # Pravila, protokoli i standardi za AI agente
├── docker-data/                # Postojeći i novi volumeni podataka
│   ├── dms/                    # Docker Mailserver podaci i konfiguracija
│   ├── storage/                # Novi disk volume za privitke i .eml datoteke
│   │   ├── attachments/        # /app/storage/attachments/{account_id}/{sha256}
│   │   └── eml/                # /app/storage/eml/{account_id}/{message_id}.eml
│   └── secrets/                # Kredencijali (Firebase, JWT, Fernet ključevi)
├── backend/                    # FastAPI asinkroni backend
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic/                # Asinkrone migracije baze
│   ├── app/
│   │   ├── main.py             # FastAPI entrypoint, middleware, lifespan
│   │   ├── core/               # Konfiguracija (.env), sigurnost (JWT, Fernet), DB sesija, Redis
│   │   ├── models/             # SQLAlchemy 2.0 deklarativni async modeli
│   │   ├── schemas/            # Pydantic v2 sheme za API ugovor
│   │   ├── api/v1/             # REST rute (auth, accounts, messages, threads, send, admin, ai)
│   │   ├── sync/               # IMAP IDLE worker, Sieve webhook handler, MIME parser
│   │   ├── realtime/           # WebSocket connection manager & Redis Pub/Sub
│   │   ├── admin/              # Docker CLI wrapper (setup email), Postfix blocklist generator
│   │   ├── push/               # FCM Firebase multicast servis
│   │   └── ai/                 # Gemini / OpenAI streaming adapteri
│   └── tests/                  # Pytest testovi
└── frontend/                   # Next.js 15 App Router
    ├── Dockerfile
    ├── package.json
    ├── components.json         # shadcn/ui konfiguracija
    ├── tailwind.config.ts
    ├── src/
    │   ├── app/                # App router (login, (mail)/inbox, admin, api proxy)
    │   ├── components/
    │   │   ├── ui/             # shadcn/ui primitivi (button, dialog, input, etc.)
    │   │   ├── layout/         # 3-Pane Resizable Layout, Header, CommandPalette
    │   │   ├── sidebar/        # Unified Inbox, Domain/Account stablo s bojama, Folders
    │   │   ├── list/           # Virtualized Message List (@tanstack/react-virtual)
    │   │   ├── thread/         # ThreadView, Sandboxed iframe za HTML mail, Privacy Banner
    │   │   ├── composer/       # Tiptap Rich Text Editor, Potpisi, Privitci, Floating Modal
    │   │   └── admin/          # Mailbox manager, Postfix blocklist UI, FCM logs
    │   ├── hooks/              # useMailWebSocket, useHotkeys, useSearch, useThread
    │   ├── lib/                # API klijent, state management, pomoćne funkcije
    │   └── types/              # TypeScript definicije generirane iz OpenAPI sheme
```

---

## 3. Mrežna i Docker topologija (Traefik usmjeravanje)

Sustav koristi dvije odvojene poddomene preko postojećeg Traefik reverse proxija:
- **Frontend URL:** `https://${WEBMAIL_HOST}` (npr. `webmail.example.com` ili tvoja definirana domena) -> prosljeđuje na Next.js (port 3000).
- **Backend API URL:** `https://${MAIL_API_HOST}` (npr. `api-mail.example.com`) -> prosljeđuje na FastAPI (port 8000) za REST i `/ws` (WebSockets).

### Kontejneri u `compose.yaml`:
1. `mailserver` (ghcr.io/docker-mailserver/docker-mailserver:17.0.0) — SMTP (25, 465, 587) i IMAP (993).
2. `mail-backend` — FastAPI aplikacija (port 8000) spojena na `postgis` i `proxy` mrežu.
3. `mail-worker` — Pozadinski proces koji vrti asinkroni `aioimaplib` IDLE sync pool.
4. `mail-frontend` — Next.js 15 produkcijski server (port 3000) spojen na `proxy` mrežu.
5. `redis` — Predmemorija i Pub/Sub sabirnica za WebSocket notifikacije (port 6379, interna mreža).

---

## 4. Shema baze podataka (PostgreSQL 17 + SQLAlchemy 2.0 Async)

Baza koristi čistu novu shemu s optimiziranim indeksima i `tsvector` punom tekstualnom pretragom (Clean break pristup).

### 4.1. Korisnici i autentifikacija
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(32) NOT NULL DEFAULT 'user', -- 'admin' ili 'user'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 4.2. Povezani e-mail računi (Mailbox Accounts)
```sql
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    color_code VARCHAR(16) NOT NULL DEFAULT '#3b82f6', -- Hex boja za badge u Unified Inboxu
    imap_host VARCHAR(255) NOT NULL,
    imap_port INT NOT NULL DEFAULT 993,
    imap_use_ssl BOOLEAN NOT NULL DEFAULT TRUE,
    smtp_host VARCHAR(255) NOT NULL,
    smtp_port INT NOT NULL DEFAULT 587,
    smtp_use_tls BOOLEAN NOT NULL DEFAULT TRUE,
    encrypted_password TEXT NOT NULL, -- Kriptirano pomoću cryptography.fernet
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sync_status VARCHAR(32) NOT NULL DEFAULT 'idle', -- 'syncing', 'idle', 'error'
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_account_email UNIQUE (user_id, email)
);
```

### 4.3. Mape (Folders)
```sql
CREATE TABLE folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    path VARCHAR(255) NOT NULL, -- npr. 'INBOX', 'INBOX.Archive', 'Sent'
    delimiter VARCHAR(8) NOT NULL DEFAULT '/',
    special_use VARCHAR(32), -- 'inbox', 'sent', 'drafts', 'trash', 'spam', 'archive'
    uid_validity BIGINT,
    uid_next BIGINT,
    unread_count INT NOT NULL DEFAULT 0,
    total_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_account_folder_path UNIQUE (account_id, path)
);
```

### 4.4. Threadovi (Konverzacije)
```sql
CREATE TABLE threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    first_message_id VARCHAR(512),
    subject TEXT,
    normalized_subject TEXT, -- Uklonjeni 'Re:', 'Fwd:' prefiksi za grupiranje
    snippet TEXT,
    last_message_at TIMESTAMPTZ NOT NULL,
    message_count INT NOT NULL DEFAULT 1,
    is_unread BOOLEAN NOT NULL DEFAULT TRUE,
    is_starred BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_threads_account_last_msg ON threads(account_id, last_message_at DESC);
CREATE INDEX idx_threads_account_unread ON threads(account_id, is_unread);
```

### 4.5. Poruke (Messages)
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    folder_id UUID NOT NULL REFERENCES folders(id) ON DELETE CASCADE,
    uid BIGINT NOT NULL,
    message_id VARCHAR(512) NOT NULL,
    in_reply_to VARCHAR(512),
    references_header TEXT,
    sender_name VARCHAR(255),
    sender_email VARCHAR(255) NOT NULL,
    to_recipients JSONB NOT NULL DEFAULT '[]',
    cc_recipients JSONB NOT NULL DEFAULT '[]',
    bcc_recipients JSONB NOT NULL DEFAULT '[]',
    reply_to VARCHAR(255),
    subject TEXT,
    date TIMESTAMPTZ NOT NULL,
    snippet TEXT,
    body_plain TEXT,
    body_html TEXT,
    has_attachments BOOLEAN NOT NULL DEFAULT FALSE,
    eml_storage_path VARCHAR(512), -- Putanja do sirovog .eml na disku
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    is_starred BOOLEAN NOT NULL DEFAULT FALSE,
    is_draft BOOLEAN NOT NULL DEFAULT FALSE,
    flags JSONB NOT NULL DEFAULT '[]', -- IMAP zastavice: '\Seen', '\Flagged', etc.
    search_vector tsvector,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_account_folder_uid UNIQUE (account_id, folder_id, uid)
);
CREATE INDEX idx_messages_search_vector ON messages USING GIN(search_vector);
CREATE INDEX idx_messages_thread_date ON messages(thread_id, date ASC);
CREATE INDEX idx_messages_sender ON messages(sender_email);
```

### 4.6. Privitci (Attachments)
```sql
CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    filename VARCHAR(512) NOT NULL,
    content_type VARCHAR(255) NOT NULL,
    size_bytes BIGINT NOT NULL,
    content_id VARCHAR(255), -- Za inline slike unutar HTML-a (cid:...)
    is_inline BOOLEAN NOT NULL DEFAULT FALSE,
    storage_path VARCHAR(512) NOT NULL, -- Putanja do datoteke na volumenu
    sha256_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 4.7. Potpisi po računima (Signatures)
```sql
CREATE TABLE account_signatures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    content_html TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 4.8. Postfix Sender Blocklist i Dnevnik
```sql
CREATE TABLE sender_blocklist_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind VARCHAR(32) NOT NULL, -- 'sender_email' ili 'sender_domain'
    value VARCHAR(255) NOT NULL UNIQUE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    note TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE blocklist_apply_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(16) NOT NULL, -- 'success' ili 'error'
    message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 4.9. Registracija mobilnih uređaja (FCM Push)
```sql
CREATE TABLE device_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_email VARCHAR(255) NOT NULL,
    fcm_token TEXT NOT NULL UNIQUE,
    platform VARCHAR(32) NOT NULL DEFAULT 'unknown', -- 'android', 'ios', 'web'
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_device_reg_email ON device_registrations(account_email, enabled);
```

---

## 5. Sinkronizacija i stvarna vremena (Real-Time Ingestion Engine)

Sinkronizacijski mehanizam ima dvije ulazne točke:

```
                  +--------------------------------+
                  | Dovecot Mail Delivery (LDA/LMTP)
                  +--------------------------------+
                                  |
                   Sieve filter: pipe to hook script
                                  |
                                  v
                  +--------------------------------+
                  | POST /api/v1/sync/sieve-webhook|  <--- 0ms latencija za novi mail
                  +--------------------------------+
                                  |
                                  +---------> 1. Spremi u PostgreSQL & na disk
                                  |           2. Pošalji FCM Push na mobitele
                                  |           3. Emitiraj WebSocket događaj u Next.js
                                  |
+------------------------------------+
| Pozadinski aioimaplib IDLE Worker  |  <--- Praćenje vanjskih klijenata (Thunderbird, iOS)
+------------------------------------+
  - Drži otvorenu IDLE vezu prema svakom aktivnom računu
  - Prima obavijesti o promjeni zastavica (\Seen, \Flagged, EXPUNGE)
  - Ažurira stanje u PostgreSQL i šalje WebSocket delta update na frontend
```

### WebSocket događaji prema Next.js klijentu:
- `mail:new`: Nova poruka u mapi s JSON objektom poruke i ažuriranim brojačem.
- `mail:flags_updated`: Ažurirane zastavice (npr. pročitano/označeno zvjezdicom) za ID poruke.
- `mail:moved`: Poruka premještena u drugu mapu (npr. Archive ili Trash).
- `mail:deleted`: Poruka trajno obrisana.
- `folder:counts`: Ažuriran unread i total broj po mapama.

---

## 6. Slanje mailova (SMTP Pipeline)
- Korištenje asinkrone biblioteke `aiosmtplib`.
- Prilikom slanja, backend se autentificira na Docker Mailserver preko SMTP porta 587 (STARTTLS) koristeći enkriptiranu lozinku odabranog računa.
- Nakon uspješnog slanja:
  1. Kopija poruke se putem IMAP `APPEND` naredbe automatski sprema u mapu `Sent` na mailserveru.
  2. Poruka se lokalno sprema u tablice `messages` i `threads`.
  3. Skica (`Draft`) se automatski uklanja ako se radilo o odgovoru.

---

## 7. AI Servisi (Smart Reply & Sažimanje threadova)
- **Podržani provideri:** Google Gemini API (`gemini-2.5-flash`) i OpenAI API (`gpt-4o-mini`).
- **Implementacija:**
  - `POST /api/v1/ai/summarize-thread`: Prima cijeli thread (tijela poruka kronološki posložena) i vraća sažeti pregled (bullet points: tko traži što, dogovoreni rokovi i otvorena pitanja).
  - `POST /api/v1/ai/smart-reply`: Analizira zadnju pristiglu poruku i kontekst threada te vraća 3 brza kratka prijedloga odgovora (npr. Potvrdan, Odbijajući, Upit za dodatne detalje).
  - Korisnik jednim klikom ubacuje prijedlog u Tiptap editor za daljnje uređivanje.

---

## 8. Frontend UX i komponente (Next.js 15)

### 8.1. 3-Pane Resizable Layout (`react-resizable-panels`)
- **Lijevi stupac (Sidebar):**
  - **Unified Inbox:** Glavni gumb na vrhu s ukupnim brojem nepročitanih poruka iz svih spojenih računa.
  - **Stablo računa:** Vizualno odvojeni računi po domenama s dodijeljenom bojom (npr. Račun A = zelena, Račun B = plava, Račun C = narančasta).
  - **Mape:** Inbox, Starred, Sent, Drafts, Archive, Spam, Trash.
  - **Brzi link na Admin panel** (vidljiv samo korisnicima s `admin` rolom).
- **Srednji stupac (Message List):**
  - Virtualizirana lista (`@tanstack/react-virtual`) sposobna za rad s više od 50.000 poruka bez pada performansi.
  - Kartica poruke prikazuje: Pošiljatelja, Subject, datum/vrijeme, oznaku boje računa, snippet od 2 linije, ikonu spajalice ako ima privitak i plavu točku za nepročitano.
  - Gornja traka: Tražilica (pretražuje `tsvector` u bazi u realnom vremenu uz debounce od 250ms), brzi filteri (`All`, `Unread`, `Starred`, `Attachments`).
- **Desni stupac (Thread View & Inline Composer):**
  - Zaglavlje threada s popisom sudionika i akcijama: Reply, Reply All, Forward, Archive, Delete, Spam, Block Sender (1-klik).
  - **Siguran prikaz HTML poruka:** Prikaz unutar sandboxed `<iframe>` komponente (`sandbox="allow-popups allow-popups-to-escape-sandbox"`).
  - **Zaštita privatnosti:** Vanjske slike su blokirane po defaultu. Na vrhu se prikazuje traka: *"Vanjske slike su blokirane radi zaštite privatnosti. [Učitaj slike] [Uvijek prikazuj za ovog pošiljatelja]"*. Učitane slike prolaze kroz FastAPI proxy endpoint (`/api/v1/proxy/image?url=...`) kako se ne bi otkrio IP korisnika.
  - **Galerija privitaka:** Pregled slika (lightbox modal), PDF preglednik i 1-klik preuzimanje.
  - **Inline Reply na dnu:** Brzi Tiptap editor koji se otvara odmah ispod zadnje poruke.

### 8.2. Floating Composer (Gmail stil)
- Pritiskom na tipku `C` ili klikom na *"New Message"* otvara se lebdeći prozor u donjem desnom kutu (s opcijama minimiziranja i proširenja na puni zaslon).
- **Značajke:**
  - Padajući izbornik *"From:"* s automatskom promjenom pripadajućeg potpisa u editoru.
  - Drag-and-drop privitaka i paste slika iz clipboarda direktno u tekst.
  - Auto-save u drafts svakih 10 sekundi.
  - Slanje preko kratice `Cmd/Ctrl + Enter`.

### 8.3. Tipkovničke kratice (`hotkeys-js`)
| Prečac | Akcija |
|---|---|
| `J` / `K` (ili `Down` / `Up`) | Navigacija na sljedeću / prethodnu poruku u listi |
| `Enter` / `O` | Otvori / fokusiraj odabrani thread |
| `R` | Odgovori pošiljatelju (Reply) |
| `A` | Odgovori svima (Reply All) |
| `F` | Proslijedi (Forward) |
| `E` | Arhiviraj (Move to Archive) |
| `Delete` / `Backspace` | Premjesti u smeće (Trash) |
| `S` | Označi / ukloni zvjezdicu (Star) |
| `U` | Označi kao nepročitano / pročitano |
| `C` | Sastavi novu poruku (Compose Modal) |
| `Cmd/Ctrl + Enter` | Pošalji sastavljeni mail |
| `Cmd/Ctrl + K` | Command Palette (pretraga mapa, promjena računa, postavke) |
| `Escape` | Zatvori modal ili vrati fokus na listu |

---

## 9. Administratorske operacije (Zamjena Django funkcija)

U sklopu FastAPI backend-a i Next.js Admin sučelja implementiraju se:
1. **Upravljanje Mailboxima:**
   - FastAPI preko `/var/run/docker.sock` izvršava naredbe unutar `mailserver` kontejnera:
     - `setup email add <email> <password>`
     - `setup email del -y <email>`
     - `setup email list`
     - `doveadm mailbox create -u <email> Archive`
2. **Postfix Sender Blocklist:**
   - Dodavanje i uređivanje pravila (e-mail ili cijela domena).
   - Generiranje konfiguracijske datoteke `/tmp/docker-mailserver/postfix-sender-blocklist`.
   - Pokretanje `postfix reload` unutar `mailserver` kontejnera bez rušenja servisa.
   - 1-klik akcija unutar poruke: *"Blokiraj pošiljatelja"* automatski unosi pravilo i primjenjuje Postfix reload.
3. **FCM Push Relay:**
   - Endpoint `POST /api/v1/sync/sieve-webhook` poziva `firebase-admin` za slanje push notifikacije svim aktivnim uređajima tog računa.
   - Nevaljani FCM tokeni se automatski deaktiviraju.

