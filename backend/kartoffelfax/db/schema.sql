-- KartoffelFax SQLite schema
-- SQLite 3.35+ (STRICT tables, generated columns)
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- contacts: address book, replaces AVM Fritz!fax phonebook (.srl import target)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contacts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name    TEXT NOT NULL,
    company         TEXT,
    fax_number      TEXT,
    phone_number    TEXT,
    email           TEXT,
    street          TEXT,
    postal_code     TEXT,
    city            TEXT,
    country         TEXT DEFAULT 'DE',
    notes           TEXT,
    legacy_srl_id   TEXT UNIQUE,     -- original ID from imported .srl phonebook, for idempotent re-import
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;

CREATE INDEX IF NOT EXISTS idx_contacts_fax_number ON contacts(fax_number);
CREATE INDEX IF NOT EXISTS idx_contacts_display_name ON contacts(display_name);

-- ---------------------------------------------------------------------------
-- fritzbox_connections: one or more Fritz!Box targets (local, VPN/WireGuard)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fritzbox_connections (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    name                    TEXT NOT NULL,
    host                    TEXT NOT NULL,              -- e.g. 192.168.178.1 or VPN-side IP
    tr064_port              INTEGER NOT NULL DEFAULT 49000,
    tr064_username          TEXT,
    tr064_password_enc      TEXT,                        -- encrypted at rest (Fernet/OS keyring)
    sip_username            TEXT,
    sip_password_enc        TEXT,
    sip_port                INTEGER NOT NULL DEFAULT 5060,
    transport                TEXT NOT NULL DEFAULT 'sip_t38' CHECK (transport IN ('sip_t38', 'sip_g711', 'capi_tcp')),
    is_default              INTEGER NOT NULL DEFAULT 0 CHECK (is_default IN (0, 1)),
    requires_vpn            INTEGER NOT NULL DEFAULT 0 CHECK (requires_vpn IN (0, 1)),
    vpn_interface           TEXT,                         -- e.g. wg0, informational only
    created_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;

-- ---------------------------------------------------------------------------
-- fax_messages: one row per fax, inbox/outbox/drafts/archive via `folder`
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fax_messages (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    direction           TEXT NOT NULL CHECK (direction IN ('outgoing', 'incoming')),
    folder              TEXT NOT NULL CHECK (folder IN ('inbox', 'outbox', 'drafts', 'archive', 'trash')),
    status              TEXT NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft', 'queued', 'dialing', 'sending', 'sent',
                                           'failed', 'received', 'cancelled')),
    contact_id          INTEGER REFERENCES contacts(id) ON DELETE SET NULL,
    fax_number          TEXT NOT NULL,                   -- snapshot, independent of contact edits
    subject             TEXT,
    pdf_path            TEXT,                            -- final/received PDF, relative to data dir
    thumbnail_path      TEXT,
    page_count          INTEGER,
    connection_id       INTEGER REFERENCES fritzbox_connections(id) ON DELETE SET NULL,
    transport_used      TEXT CHECK (transport_used IN ('sip_t38', 'sip_g711', 'capi_tcp')),
    duration_seconds    INTEGER,
    error_message        TEXT,
    retry_count         INTEGER NOT NULL DEFAULT 0,
    legacy_import_id    TEXT UNIQUE,                      -- id/hash from legacy AVM DB import
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    queued_at           TEXT,
    sent_at             TEXT,
    received_at         TEXT
) STRICT;

CREATE INDEX IF NOT EXISTS idx_fax_messages_folder ON fax_messages(folder);
CREATE INDEX IF NOT EXISTS idx_fax_messages_status ON fax_messages(status);
CREATE INDEX IF NOT EXISTS idx_fax_messages_contact ON fax_messages(contact_id);
CREATE INDEX IF NOT EXISTS idx_fax_messages_created_at ON fax_messages(created_at);

-- ---------------------------------------------------------------------------
-- fax_source_files: original drag&drop documents merged into an outgoing fax
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fax_source_files (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fax_message_id  INTEGER NOT NULL REFERENCES fax_messages(id) ON DELETE CASCADE,
    original_name   TEXT NOT NULL,
    stored_path     TEXT NOT NULL,
    mime_type       TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0
) STRICT;

CREATE INDEX IF NOT EXISTS idx_fax_source_files_message ON fax_source_files(fax_message_id);

-- ---------------------------------------------------------------------------
-- fax_events: append-only transmission/status log per fax (incl. VPN drops)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fax_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fax_message_id  INTEGER NOT NULL REFERENCES fax_messages(id) ON DELETE CASCADE,
    event_type      TEXT NOT NULL,     -- e.g. 'dial', 'vpn_dropped', 'retry', 'completed', 'error'
    detail          TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;

CREATE INDEX IF NOT EXISTS idx_fax_events_message ON fax_events(fax_message_id);

-- ---------------------------------------------------------------------------
-- import_jobs: tracks .srl phonebook / legacy AVM DB migrations
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS import_jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type        TEXT NOT NULL CHECK (job_type IN ('srl_phonebook', 'legacy_fax_db')),
    source_path     TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'done', 'failed')),
    imported_count  INTEGER NOT NULL DEFAULT 0,
    skipped_count   INTEGER NOT NULL DEFAULT 0,
    error_count     INTEGER NOT NULL DEFAULT 0,
    error_message    TEXT,
    started_at      TEXT,
    finished_at     TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;

-- ---------------------------------------------------------------------------
-- settings: generic key/value app configuration
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS settings (
    key             TEXT PRIMARY KEY,
    value           TEXT NOT NULL,
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;

-- ---------------------------------------------------------------------------
-- schema_migrations: tracks applied migration filenames (see db/migrations/)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schema_migrations (
    version         TEXT PRIMARY KEY,
    applied_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;
