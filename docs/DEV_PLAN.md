# KartoffelFax – Entwicklungsplan

Stand: 2026-11-07, Basis-Commit `9495abd` ("Initial project scaffold"). Dieses
Dokument zerlegt die verbleibende Arbeit in unabhängige **Work Packages
(WP)**, jedes mit festem Datei-Scope, Abhängigkeiten und einem fertigen
Prompt, der 1:1 an einen Subagenten gegeben werden kann.

## Spielregeln für Subagenten

1. **Branch pro WP.** Jeder Subagent arbeitet auf `feature/wp-XX-<slug>`,
   niemals direkt auf `main`. Kein Push ohne ausdrückliche Freigabe.
2. **Datei-Scope einhalten.** Nur die unter "Dateien" gelisteten Pfade
   anfassen. Wenn eine Änderung außerhalb nötig scheint, anhalten und fragen
   statt eigenmächtig zu erweitern.
3. **Keine Fantasie-Implementierungen.** Wenn eine externe Abhängigkeit
   (Ghostscript, pjsua2, echte Fritz!Box) fehlt und nicht simuliert werden
   kann, das ehrlich im Report vermerken statt `NotImplementedError` durch
   Pseudo-Code zu ersetzen, der nie getestet wurde.
4. **Definition of Done ist bindend:** `pytest`, `ruff check .` müssen grün
   sein, neue Logik braucht Tests. Kein WP gilt als fertig, wenn Tests fehlen.
5. **Conventions aus dem Scaffold übernehmen:** Type Hints überall,
   `async def` für alles was I/O macht, Pydantic-Modelle in
   `backend/kartoffelfax/schemas/`, keine Kommentare die nur wiederholen was
   der Code sagt.
6. **Commit-Message-Stil:** kurzer Titel + Begründung (warum), wie im
   Initial-Commit. Co-Authored-By-Zeile nicht nötig für Subagenten, außer der
   jeweilige Agent-Prompt verlangt es explizit.

## Abhängigkeits-Überblick

```
WP-0 (CI/Tooling)              — keine Abhängigkeit, jederzeit
WP-1 (Contacts CRUD)           — keine Abhängigkeit
WP-2 (Fax CRUD/Upload)         — keine Abhängigkeit
WP-3 (PDF → G3 TIFF)           — keine Abhängigkeit
WP-4 (TIFF → PDF Empfang)      — sollte Tool-Wahl von WP-3 kennen (lesen, nicht blockiert)
WP-5 (TR-064 Client)           — keine Abhängigkeit
WP-6a (SIP/T.38 Spike/ADR)     — keine Abhängigkeit
WP-6b (SIP/T.38 Implementierung) — braucht WP-6a + WP-3 + WP-4, braucht echte Testumgebung
WP-7 (CAPI Fallback)           — keine Abhängigkeit, niedrige Priorität
WP-8 (.srl Parser)             — BLOCKIERT bis Beispieldateien vorliegen (Mensch)
WP-9 (Legacy-DB-Import)        — BLOCKIERT bis Beispielexport vorliegt (Mensch)
WP-10 (Frontend-Views)         — kann parallel zu Backend laufen (Contracts stehen in schemas/)
WP-11 (Packaging)              — sinnvoll erst nach WP-1/WP-2, kann aber vorbereitet werden
WP-12 (Code-Qualität, laufend) — Teil von WP-0, danach fortlaufend
WP-13 (MCP-Server)             — braucht WP-1, WP-2, WP-5 (laut Stand bereits gemergt)
```

**Sofort parallel startbar, ohne Kollisionen:** WP-0, WP-1, WP-2, WP-3, WP-5,
WP-6a, WP-10 — berühren alle unterschiedliche Dateien.

---

## WP-0: CI-Pipeline & Dev-Tooling

**Ziel:** Jeder PR/Push wird automatisch gegen Lint + Tests geprüft, damit
spätere WPs nicht unbemerkt kaputtgehen.

**Dateien:** `.github/workflows/ci.yml` (neu), `scripts/dev.sh` (neu)

**Abhängigkeiten:** keine

**Aufgaben:**
- GitHub-Actions-Workflow: Python 3.12 Matrix, `pip install -e ".[dev]"`,
  `ruff check .`, `pytest`.
- `scripts/dev.sh` mit Kurzbefehlen (`setup`, `test`, `lint`, `run`) für
  lokale Entwicklung ohne die Befehle jedes Mal nachzuschlagen.

**Definition of Done:**
- Workflow läuft bei einem Test-Push grün (gegen aktuellen Scaffold-Stand,
  der ja schon `pytest`-fähig ist).

**Subagent-Prompt:**
> Richte in `/home/mint/kartoffelFax` eine GitHub-Actions-CI-Pipeline unter
> `.github/workflows/ci.yml` ein, die bei Push/PR auf Python 3.12 `pip
> install -e ".[dev]"`, dann `ruff check .` und `pytest` ausführt. Lege
> außerdem `scripts/dev.sh` mit Subcommands `setup|test|lint|run` an. Arbeite
> auf einem Branch `feature/wp-00-ci`, committe, aber push nicht ohne
> Rückfrage. Prüfe lokal, dass `ruff check .` und `pytest` auf dem
> aktuellen Repo-Stand durchlaufen, bevor du den Workflow schreibst, damit
> die Pipeline nicht sofort rot ist.

---

## WP-1: Contacts CRUD (Backend)

**Ziel:** `backend/kartoffelfax/api/routes_contacts.py` von
`NotImplementedError`-Stubs zu echten, getesteten Endpunkten.

**Dateien:**
- `backend/kartoffelfax/api/routes_contacts.py` (ändern)
- `backend/kartoffelfax/db/repositories/__init__.py` (neu)
- `backend/kartoffelfax/db/repositories/contact_repository.py` (neu)
- `backend/tests/test_contacts_api.py` (neu)

**Abhängigkeiten:** keine (Schema `contacts` existiert bereits in
`backend/kartoffelfax/db/schema.sql`)

**Aufgaben:**
- Repository-Funktionen (`list_contacts`, `create_contact`,
  `update_contact`, `delete_contact`, `get_contact`) auf Basis von
  `kartoffelfax.db.database.get_connection()`.
- Routen in `routes_contacts.py` an das Repository anbinden, inkl.
  `query`-Filter (einfacher `LIKE`-Suchfilter auf `display_name`/`fax_number`).
- 404 werfen (`HTTPException`), wenn `contact_id` nicht existiert.
- Tests mit `httpx.AsyncClient` + `ASGITransport` gegen eine temporäre
  SQLite-Datei (nicht `:memory:`, da `aiosqlite` pro Request neu verbindet —
  siehe `config.settings.database_url` zum Überschreiben in Tests via
  `monkeypatch`).

**Definition of Done:**
- Alle Endpunkte in `routes_contacts.py` ohne `NotImplementedError`.
- Tests decken Create, List (mit und ohne `query`), Update, Delete,
  404-Fall ab.

**Subagent-Prompt:**
> Implementiere in `/home/mint/kartoffelFax` die Contacts-CRUD-API. Die
> Routen-Stubs liegen in `backend/kartoffelfax/api/routes_contacts.py`, das
> Pydantic-Schema in `backend/kartoffelfax/schemas/contact.py`, die
> SQLite-Tabelle `contacts` in `backend/kartoffelfax/db/schema.sql`,
> Connection-Handling in `backend/kartoffelfax/db/database.py`
> (`get_connection()` als async Context-Manager). Lege ein Repository unter
> `backend/kartoffelfax/db/repositories/contact_repository.py` an und binde
> die Routen daran an. Schreibe Tests in
> `backend/tests/test_contacts_api.py` gegen eine temporäre SQLite-Datei
> (per `monkeypatch` auf `kartoffelfax.config.settings`). Arbeite auf Branch
> `feature/wp-01-contacts-crud`. `ruff check .` und `pytest` müssen grün
> sein, bevor du fertig bist. Fasse nur Dateien in diesem Scope an.

---

## WP-2: Fax-Message CRUD, Upload, Entwürfe (Backend)

**Ziel:** `routes_fax.py` implementieren — **ohne** echten Versand (das ist
WP-6b). Ein Fax landet nach `send_fax` erstmal nur als `status=queued`,
`folder=outbox` in der DB; ein echter Sende-Worker kommt später.

**Dateien:**
- `backend/kartoffelfax/api/routes_fax.py` (ändern)
- `backend/kartoffelfax/db/repositories/fax_repository.py` (neu)
- `backend/tests/test_fax_api.py` (neu)

**Abhängigkeiten:** keine (unabhängig von WP-1, andere Dateien)

**Aufgaben:**
- `upload_document`: Datei nach `settings.data_dir / "uploads"` speichern
  (UUID-Dateiname, Original-MIME-Type merken), `stored_path` zurückgeben.
- `send_fax`: legt `fax_messages`-Zeile an (`direction=outgoing`,
  `folder=outbox`, `status=queued`), verknüpft `source_file_paths` als
  `fax_source_files`-Zeilen. **Kein** Aufruf von `pdf_to_fax` oder SIP hier —
  das ist explizit außerhalb des Scopes.
- `list_fax_messages`, `get_fax_message`, `delete_fax_message` analog zu
  WP-1 implementieren.
- `config.py`: `ensure_directories()` um `uploads/` ergänzen.

**Definition of Done:**
- Alle Endpunkte implementiert, Tests für Upload + Send (Status landet
  korrekt als `queued`/`outbox`) + List/Get/Delete.

**Subagent-Prompt:**
> Implementiere in `/home/mint/kartoffelFax` die Fax-Message-API in
> `backend/kartoffelfax/api/routes_fax.py` (Schema:
> `backend/kartoffelfax/schemas/fax.py`, Tabellen `fax_messages` und
> `fax_source_files` in `backend/kartoffelfax/db/schema.sql`). Wichtig: Baue
> **keinen** echten Faxversand — `send_fax` soll nur eine DB-Zeile mit
> `status=queued`, `folder=outbox` anlegen und hochgeladene Dateien als
> `fax_source_files` verknüpfen. `upload_document` soll die Datei unter
> `settings.data_dir / "uploads"` ablegen (ergänze dafür
> `ensure_directories()` in `backend/kartoffelfax/config.py`). Lege ein
> Repository unter `backend/kartoffelfax/db/repositories/fax_repository.py`
> an (falls `contact_repository.py` dort schon existiert, folge dessen
> Stil). Tests in `backend/tests/test_fax_api.py`. Branch
> `feature/wp-02-fax-crud`. `ruff check .` + `pytest` müssen grün sein.

---

## WP-3: PDF-Zusammenführung & G3/TIFF-Konvertierung

**Ziel:** `core/fax/pdf_to_fax.py` fertigstellen — Dokumente zu einem PDF
mergen, PDF zu faxfähigem G3-TIFF rastern.

**Dateien:**
- `backend/kartoffelfax/core/fax/pdf_to_fax.py` (ändern)
- `pyproject.toml` (ggf. neue Dependencies ergänzen)
- `backend/tests/test_pdf_to_fax.py` (neu, inkl. kleiner generierter
  Test-PDFs)

**Abhängigkeiten:** keine

**Aufgaben:**
- `merge_to_pdf`: mehrere PDFs/Bilder zu einem PDF zusammenführen (`pypdf`
  ist schon Dependency; für Bild→PDF ggf. `img2pdf` oder `Pillow` ergänzen).
- `pdf_to_g3_tiff`: PDF-Seiten rastern (204×98 Standard- bzw. 204×196
  Fine-Resolution) und als Group-3/4-TIFF schreiben. Realistischer Weg:
  Ghostscript-CLI (`gs -sDEVICE=tiffg3/tiffg4 ...`) per `subprocess` statt
  eine Python-Bibliothek, die das nicht zuverlässig kann — **das muss im
  Report dokumentiert werden**, inkl. der Systemvoraussetzung
  "Ghostscript muss installiert sein" (README entsprechend ergänzen).
- Fehlerfall behandeln: Ghostscript nicht installiert / Exit-Code ≠ 0 →
  aussagekräftige Exception, kein stiller Fehlschlag.

**Definition of Done:**
- Beide Funktionen funktionieren nachweislich lokal (Test erzeugt ein
  Mini-PDF, merged es, konvertiert zu TIFF, prüft TIFF-Header/Auflösung).
- README-Abschnitt "Systemvoraussetzungen" um Ghostscript ergänzt.

**Subagent-Prompt:**
> Implementiere `merge_to_pdf` und `pdf_to_g3_tiff` in
> `/home/mint/kartoffelFax/backend/kartoffelfax/core/fax/pdf_to_fax.py`.
> `merge_to_pdf` führt mehrere Dateien (PDF, ggf. Bilder) zu einem PDF
> zusammen. `pdf_to_g3_tiff` rastert das PDF zu einem faxfähigen
> Group-3/4-TIFF (Standard 204×98, Fine 204×196 dpi) — nutze dafür
> Ghostscript per `subprocess` (`gs -sDEVICE=tiffg3` o.ä.), falls das die
> zuverlässigste Option ist, und dokumentiere diese Systemabhängigkeit in
> der README unter einem neuen Abschnitt "Systemvoraussetzungen". Ergänze
> `pyproject.toml` um evtl. zusätzlich nötige Python-Pakete. Schreibe Tests
> in `backend/tests/test_pdf_to_fax.py`, die on-the-fly ein Mini-PDF
> erzeugen und den kompletten Weg PDF→TIFF prüfen (Dateigröße > 0, korrekter
> TIFF-Header reicht als Nachweis, wenn Ghostscript in der Testumgebung
> fehlt: Test sauber skippen mit Begründung, nicht fälschlich grün machen).
> Branch `feature/wp-03-pdf-to-fax`.

---

## WP-4: Fax-Empfang – TIFF → PDF, Thumbnail

**Ziel:** `core/fax/fax_receiver.py` fertigstellen (Gegenrichtung zu WP-3).

**Dateien:**
- `backend/kartoffelfax/core/fax/fax_receiver.py` (ändern)
- `backend/tests/test_fax_receiver.py` (neu)

**Abhängigkeiten:** Keine harte Abhängigkeit, aber **vor dem Start
`core/fax/pdf_to_fax.py` lesen**, sobald WP-3 gemerged ist, um dieselbe
Tool-Wahl (Ghostscript vs. Python-Lib) zu verwenden — zwei verschiedene
PDF-Toolchains im selben Modul wären unnötige Inkonsistenz.

**Aufgaben:**
- `tiff_to_pdf`: empfangenes G3-TIFF zu durchsuchbarem/anzeigbarem PDF.
- `generate_thumbnail`: erste Seite als PNG/JPEG-Vorschau (für die
  Nachrichtenliste im Frontend).

**Definition of Done:** Tests mit einem synthetisch erzeugten TIFF
(z. B. via Pillow geschrieben) belegen beide Funktionen.

**Subagent-Prompt:**
> Implementiere `tiff_to_pdf` und `generate_thumbnail` in
> `/home/mint/kartoffelFax/backend/kartoffelfax/core/fax/fax_receiver.py`.
> Lies zuerst `backend/kartoffelfax/core/fax/pdf_to_fax.py` — falls dort
> bereits eine Konvertierungs-Toolchain (z. B. Ghostscript) etabliert wurde,
> nutze dieselbe, statt eine zweite einzuführen. Tests in
> `backend/tests/test_fax_receiver.py` mit einem synthetisch erzeugten
> Test-TIFF. Branch `feature/wp-04-fax-receiver`.

---

## WP-5: TR-064-Client & Settings-API

**Ziel:** Echte TR-064-SOAP-Calls statt nur Reachability-Check, plus
CRUD für Fritz!Box-Verbindungsprofile mit verschlüsselter
Zugangsdaten-Speicherung.

**Dateien:**
- `backend/kartoffelfax/core/fritzbox/tr064_client.py` (ändern)
- `backend/kartoffelfax/core/security.py` (neu — Fernet-Verschlüsselung)
- `backend/kartoffelfax/api/routes_settings.py` (ändern)
- `backend/kartoffelfax/db/repositories/connection_repository.py` (neu)
- `backend/kartoffelfax/config.py` (ändern — `secret_key`-Setting)
- `backend/tests/test_tr064_client.py`, `backend/tests/test_settings_api.py`
  (neu)

**Abhängigkeiten:** keine

**Aufgaben:**
- `core/security.py`: Fernet-Helfer (`encrypt`/`decrypt`), Schlüssel aus
  `settings.secret_key` (neues Feld, aus `.env`/Umgebungsvariable, beim
  ersten Start generieren und persistieren falls nicht gesetzt — **nie
  im Klartext committen oder loggen**).
- `TR064Client.get_device_info()`: echten SOAP-Envelope für
  `urn:dslforum-org:service:DeviceInfo:1#GetInfo` bauen, per `httpx`
  senden, Antwort parsen (`xml.etree.ElementTree` reicht, keine neue
  Dependency nötig). HTTP-Digest-Auth berücksichtigen, falls die Box das
  verlangt.
- `routes_settings.py`: `list_connections`, `create_connection`,
  `test_connection` ans Repository anbinden; Passwörter nur verschlüsselt
  speichern, nie in API-Responses zurückgeben.
- Tests gegen eine echte Fritz!Box sind nicht möglich in CI — **mocke die
  HTTP-Schicht** (z. B. `httpx.MockTransport` oder `respx`) mit einer
  realistischen TR-064-SOAP-Antwort.

**Definition of Done:** Tests laufen ohne echte Fritz!Box durch (gemockt),
Passwörter liegen nachweislich verschlüsselt in der DB (Test liest die
Rohdaten aus der Tabelle und prüft, dass der Klartext nicht vorkommt).

**Subagent-Prompt:**
> Implementiere den echten TR-064-Client in
> `/home/mint/kartoffelFax/backend/kartoffelfax/core/fritzbox/tr064_client.py`
> (`get_device_info()` via echtem SOAP-Call auf
> `urn:dslforum-org:service:DeviceInfo:1#GetInfo`, HTTP via `httpx`, Parsing
> via `xml.etree.ElementTree`). Lege `backend/kartoffelfax/core/security.py`
> mit Fernet-Verschlüsselung für gespeicherte Zugangsdaten an (Key über ein
> neues `secret_key`-Feld in `backend/kartoffelfax/config.py`, bei fehlendem
> Key beim ersten Start generieren und persistieren, nie loggen). Baue
> `backend/kartoffelfax/db/repositories/connection_repository.py` und binde
> `backend/kartoffelfax/api/routes_settings.py` daran an — Passwörter
> werden nur verschlüsselt gespeichert und nie im Klartext zurückgegeben.
> Da keine echte Fritz!Box in der Testumgebung verfügbar ist, mocke die
> HTTP-Schicht in den Tests (`backend/tests/test_tr064_client.py`,
> `backend/tests/test_settings_api.py`) mit einer realistischen
> SOAP-Antwort statt echter Netzwerkcalls. Branch `feature/wp-05-tr064`.

---

## WP-6a: Technologie-Spike SIP/T.38 (Architecture Decision Record)

**Ziel:** Fundierte Entscheidung **vor** der eigentlichen Implementierung,
welche SIP/T.38-Bibliothek genutzt wird — das ist der riskanteste Teil des
gesamten Projekts.

**Dateien:** `docs/adr/0001-sip-t38-stack.md` (neu)

**Abhängigkeiten:** keine

**Aufgaben:**
- Mindestens `pjsua2` (pjproject-Python-Bindings, hat T.38-Support) sowie
  die Alternative "eigener minimaler SIP/RTP-Stack auf asyncio" bewerten.
- Kriterien: T.38-Reife, Packaging-Tauglichkeit für Windows **und** Linux
  (PyInstaller-Kompatibilität!), Lizenz, Wartungsstand, Lernkurve.
- Ergebnis als ADR: Kontext, Optionen, Entscheidung, Konsequenzen.

**Definition of Done:** ADR beantwortet explizit "baut WP-6b darauf auf,
ja/nein" und nennt die konkret nötigen System-Pakete pro Plattform.

**Subagent-Prompt:**
> Recherchiere und dokumentiere in
> `/home/mint/kartoffelFax/docs/adr/0001-sip-t38-stack.md` eine
> Architecture-Decision für die SIP/T.38-Anbindung von KartoffelFax an die
> Fritz!Box (sendet/empfängt Faxe als SIP-Endgerät über T.38, Fallback
> G.711). Vergleiche mindestens `pjsua2` (pjproject) gegen einen
> selbstgebauten asyncio-SIP/RTP-Stack, bewerte nach T.38-Reife,
> Cross-Platform-Packaging (muss per PyInstaller auf Windows 11 **und**
> Linux laufen), Lizenz und Wartungsstand. Triff eine klare Empfehlung mit
> den konkret nötigen System-/Python-Paketen je Plattform. Kein Code,
> reine Recherche + Entscheidungsdokument. Branch `feature/wp-06a-sip-adr`.

---

## WP-6b: SIP/T.38-Client-Implementierung

**Ziel:** `core/fritzbox/sip_client.py` real implementieren: Registrierung,
ausgehender Faxversand, eingehender Faxempfang.

**Dateien:** `backend/kartoffelfax/core/fritzbox/sip_client.py`,
`backend/kartoffelfax/api/routes_fax.py` (Anbindung an echten Versand),
`backend/tests/test_sip_client.py`

**Abhängigkeiten:** WP-6a (Technologieentscheidung), WP-3 (G3-TIFF-Erzeugung),
WP-4 (TIFF→PDF-Empfang)

**⚠️ Nicht blind an einen Subagenten geben:** Diese WP braucht entweder eine
echte Fritz!Box im Zugriff oder einen SIP-Testserver (z. B. lokaler
Asterisk mit T.38-Unterstützung). Ohne Testumgebung kann ein Agent nur
Code schreiben, der nie tatsächlich eine Verbindung aufgebaut hat — das
muss im Report klar als "ungetestet gegen echte Hardware" markiert werden.

**Subagent-Prompt (erst nach WP-6a und mit Testumgebung starten):**
> Implementiere `SIPFaxClient.register/send_fax/listen_for_incoming` in
> `/home/mint/kartoffelFax/backend/kartoffelfax/core/fritzbox/sip_client.py`
> auf Basis der in `docs/adr/0001-sip-t38-stack.md` getroffenen
> Technologie-Entscheidung. `send_fax` nutzt die G3-TIFF-Erzeugung aus
> `core/fax/pdf_to_fax.py`, eingehende Faxe laufen durch
> `core/fax/fax_receiver.py` und legen eine `fax_messages`-Zeile
> (`folder=inbox`) an. Binde den echten Versand in
> `backend/kartoffelfax/api/routes_fax.py::send_fax` ein (ersetzt die
> bisherige reine DB-Zeile aus WP-2 durch einen Hintergrund-Task, der den
> Status über `/ws/status` live meldet). **Wichtig:** Wenn keine echte
> Fritz!Box oder SIP-Testserver erreichbar ist, markiere im Abschlussbericht
> explizit, welche Pfade nur gegen Mocks und welche gegen echte Hardware
> getestet wurden. Branch `feature/wp-06b-sip-implementation`.

---

## WP-7: CAPI-over-TCP-Fallback (niedrige Priorität)

**Ziel:** Minimaler Fallback für lokale Windows-Installationen mit
bestehendem CAPI-Fax-Treiber. Kann beliebig aufgeschoben werden, da SIP/T.38
der primäre Pfad ist.

**Dateien:** `backend/kartoffelfax/core/fritzbox/capi_wrapper.py`,
`backend/tests/test_capi_wrapper.py`

**Abhängigkeiten:** keine

**Subagent-Prompt:**
> Implementiere `CapiFaxWrapper.send_fax` in
> `/home/mint/kartoffelFax/backend/kartoffelfax/core/fritzbox/capi_wrapper.py`
> als minimalen CAPI-over-TCP-Client. Das ist ein Fallback mit niedriger
> Priorität — wenn kein CAPI-over-TCP-Endpunkt zum Testen verfügbar ist,
> implementiere das Protokoll so weit wie ohne echte Gegenstelle sinnvoll
> möglich und dokumentiere im Report, was ungetestet bleibt. Branch
> `feature/wp-07-capi-fallback`.

---

## WP-8: `.srl`-Telefonbuch-Parser — **BLOCKIERT**

**Nicht an einen Agenten geben, bevor Folgendes erledigt ist:** Mindestens
2-3 reale `.srl`-Exportdateien aus der alten AVM-Fritz!fax-Installation
besorgen und unter `backend/tests/fixtures/srl_samples/` ablegen (falls
personenbezogene Daten enthalten sind: vorher anonymisieren/kürzen).

Erst danach ist dies ein startbares WP:

**Dateien:** `backend/kartoffelfax/core/importers/srl_parser.py`,
`docs/srl_format_notes.md` (neu), `backend/tests/test_srl_parser.py`,
Fixture-Dateien unter `backend/tests/fixtures/srl_samples/`

**Subagent-Prompt (erst nach Beschaffung der Beispieldateien verwenden):**
> In `/home/mint/kartoffelFax/backend/tests/fixtures/srl_samples/` liegen
> reale `.srl`-Exportdateien aus AVM Fritz!fax. Analysiere das Binärformat
> per Hexdump-Vergleich mehrerer Dateien, dokumentiere den erkannten Aufbau
> in `docs/srl_format_notes.md` und implementiere darauf basierend
> `parse_srl_file` in
> `backend/kartoffelfax/core/importers/srl_parser.py`. Teste gegen die
> echten Fixture-Dateien in `backend/tests/test_srl_parser.py`. Wenn sich
> einzelne Felder nicht sicher zuordnen lassen, das explizit als offene
> Frage im Dokument vermerken statt zu raten. Branch
> `feature/wp-08-srl-parser`.

---

## WP-9: Legacy-Fax-DB-Import — **BLOCKIERT**

**Nicht an einen Agenten geben, bevor Folgendes erledigt ist:** Einen
realen Export/eine Kopie der alten AVM-Fax-Datenbank (`.db`/`.mdb`)
besorgen, damit Spaltenstruktur und Inhalte bekannt sind.

**Dateien:** `backend/kartoffelfax/core/importers/legacy_db_importer.py`,
`backend/tests/test_legacy_db_importer.py`, Fixture unter
`backend/tests/fixtures/`

**Subagent-Prompt (erst nach Beschaffung des Beispielexports verwenden):**
> In `backend/tests/fixtures/` liegt ein realer Export der alten
> AVM-Fax-Datenbank. Analysiere die Struktur, implementiere
> `import_legacy_database` in
> `backend/kartoffelfax/core/importers/legacy_db_importer.py` so, dass
> Kontakte/Faxe idempotent (über `legacy_srl_id`/`legacy_import_id`) in die
> bestehenden Tabellen aus `backend/kartoffelfax/db/schema.sql` importiert
> werden. Test in `backend/tests/test_legacy_db_importer.py` gegen die
> Fixture. Branch `feature/wp-09-legacy-db-import`.

---

## WP-10: Frontend — Kontakte, Fax-Erstellung, Einstellungen, Live-Status

**Ziel:** Das Grundgerüst in `frontend/index.html` /
`frontend/static/js/app.js` um die fehlenden Ansichten erweitern.

**Dateien:**
- `frontend/index.html` (ändern)
- `frontend/static/js/app.js` (aufteilen in Module, z. B. zusätzlich
  `frontend/static/js/contacts.js`, `compose.js`, `settings.js`)
- `frontend/static/css/app.css` (ändern)

**Abhängigkeiten:** Kann **sofort parallel** zum Backend starten — die
Pydantic-Schemas in `backend/kartoffelfax/schemas/` legen die API-Verträge
schon fest, auch wenn die Endpunkte noch `NotImplementedError` werfen.
Gegen echte Daten testen, sobald WP-1/WP-2 gemergt sind.

**Aufgaben:**
- Kontakte-Ansicht (Liste, Anlegen/Bearbeiten/Löschen) analog zum
  bestehenden Ordner-Pattern in `app.js`.
- "Neues Fax"-Dialog: Drag & Drop für Dateien (`upload`-Endpunkt), Empfänger
  aus Kontakten wählen oder Faxnummer frei eingeben.
- Einstellungen-Ansicht: Fritz!Box-Verbindungen anlegen/testen
  (`/api/settings/connections`).
- Detail/Vorschau-Pane: PDF-Anzeige (`<iframe>` reicht für den Anfang),
  Status-Timeline aus `fax_events`.
- `/ws/status`-Events tatsächlich auf die Nachrichtenliste anwenden (aktuell
  nur `console.debug` in `app.js`).

**Definition of Done:** Manuell im Browser gegen den laufenden Dev-Server
geprüft (`uvicorn kartoffelfax.main:app --app-dir backend --reload`) —
Golden Path: Kontakt anlegen → Fax-Entwurf mit diesem Kontakt erstellen →
Entwurf erscheint in der Liste.

**Subagent-Prompt:**
> Erweitere das Frontend in `/home/mint/kartoffelFax/frontend/` um die
> fehlenden Ansichten: Kontakte-Verwaltung, "Neues Fax"-Dialog mit Drag &
> Drop-Upload, Einstellungen für Fritz!Box-Verbindungen, sowie eine
> PDF-Vorschau + Status-Timeline im Detail-Pane. Die API-Verträge stehen in
> `backend/kartoffelfax/schemas/contact.py` und `.../schemas/fax.py` fest.
> Baue auf dem bestehenden Pattern in `frontend/static/js/app.js` auf
> (Ordner-Navigation, Fetch gegen `/api/...`, WebSocket auf `/ws/status`)
> und teile neuen Code in eigene Module auf (`contacts.js`, `compose.js`,
> `settings.js`). Starte den Dev-Server mit `uvicorn
> kartoffelfax.main:app --app-dir backend --reload` und teste den Golden
> Path manuell im Browser (Kontakt anlegen → Fax-Entwurf → erscheint in
> Liste). Backend-Endpunkte können noch `NotImplementedError` werfen, wenn
> die zugehörige Backend-WP noch nicht gemergt ist — baue defensiv gegen
> Fehlerantworten. Branch `feature/wp-10-frontend-views`.

---

## WP-11: Packaging (PyInstaller, Docker, Flatpak)

**Ziel:** Aus den Platzhaltern in `packaging/` echte, lauffähige Builds
machen.

**Dateien:** `packaging/pyinstaller/kartoffelfax.spec` (neu),
`packaging/docker/Dockerfile` (prüfen/fixen), `packaging/flatpak/*.yml`
(neu)

**Abhängigkeiten:** sinnvoll erst, wenn WP-1/WP-2 einen funktionierenden
Golden Path liefern — vorher ist es nur eine leere Hülle zum Testen.

**Subagent-Prompt:**
> Baue in `/home/mint/kartoffelFax/packaging/pyinstaller/` ein lauffähiges
> `.spec`, das `backend/kartoffelfax` + `frontend/` zu einem
> Single-File-Executable für Linux bündelt (Windows-Build parallel
> dokumentieren, falls kein Windows zum Testen verfügbar ist). Prüfe und
> reparier `packaging/docker/Dockerfile` (`docker build` + `docker run`
> müssen tatsächlich funktionieren, nicht nur plausibel aussehen). Lege ein
> Flatpak-Manifest-Grundgerüst unter `packaging/flatpak/` an. Teste jeden
> Build-Weg tatsächlich aus und dokumentiere das Ergebnis ehrlich im
> Report, inklusive was nicht getestet werden konnte. Branch
> `feature/wp-11-packaging`.

---

## WP-13: MCP-Server (LLM-Schnittstelle)

**Ziel:** KartoffelFax über das Model Context Protocol ansprechbar machen,
damit ein LLM (z. B. Claude) Kontakte/Faxe verwalten kann. Spezifikation
steht bereits fest: [`mcp_interface_spec.md`](mcp_interface_spec.md) — hier
nur noch implementieren, nicht neu designen.

**Dateien:**
- `backend/kartoffelfax/mcp/__init__.py`, `server.py`, `tools.py` (neu)
- `pyproject.toml` (neuer `kartoffelfax-mcp`-Entry-Point, `mcp`-Dependency)
- `backend/tests/test_mcp_tools.py` (neu)

**Abhängigkeiten:** WP-1 (Contacts-Repository), WP-2 (Fax-Repository),
WP-5 (Connection-Repository, `core/security.py`) müssen existieren —
sind laut aktuellem Stand bereits gemergt.

**Aufgaben:**
- Tools exakt wie in `mcp_interface_spec.md` tabelliert umsetzen, inklusive
  des Zwei-Schritt-Bestätigungsverhaltens für `fax.queue_send`.
- stdio-Transport als Standard, kein Netzwerk-Listener ohne explizite Opt-in-
  Konfiguration.
- Zugangsdaten-Maskierung in `settings.list_connections` testen (Test muss
  nachweisen, dass `tr064_password_enc`/`sip_password_enc` nie im
  Tool-Ergebnis auftauchen).

**Definition of Done:** Alle Tools aus der Tabelle implementiert und
getestet, Sicherheitsmodell-Punkte 1–4 aus der Spec sind durch Tests belegt
(nicht nur behauptet).

**Subagent-Prompt:**
> Implementiere den MCP-Server für KartoffelFax gemäß
> `/home/mint/kartoffelFax/docs/mcp_interface_spec.md` — die Tool-Liste,
> das Sicherheitsmodell (insbesondere: `fax.queue_send` ohne `confirm=true`
> darf nichts in der DB anlegen, Zugangsdaten werden nie zurückgegeben,
> stdio-Transport als Standard ohne Netzwerk-Listener) sind dort bereits
> festgelegt, nicht neu entscheiden. Lege das Package unter
> `backend/kartoffelfax/mcp/` an, nutze direkt die bestehenden Repositories
> unter `backend/kartoffelfax/db/repositories/` (nicht über HTTP gehen).
> Ergänze `pyproject.toml` um einen `kartoffelfax-mcp`-Entry-Point und die
> `mcp`-SDK-Dependency. Schreibe Tests in
> `backend/tests/test_mcp_tools.py`, die insbesondere das
> Bestätigungs-Verhalten von `fax.queue_send` und die
> Zugangsdaten-Maskierung in `settings.list_connections` nachweisen.
> Branch `feature/wp-13-mcp-server`.

---

## Nachtrag: Abweichungen aus der bisherigen Umsetzung (Stand 2026-11-08)

- WP-0, WP-1, WP-2, WP-3, WP-5 und ein Teil von WP-10 wurden umgesetzt,
  allerdings alle auf einem gemeinsamen Branch (`feature/wp-00-ci`) statt
  pro WP ein eigener Branch. Für künftige WPs gilt die Branch-pro-WP-Regel
  weiterhin — bitte nicht wieder sammeln.
- `routes_fax.py` hat zwei zusätzliche, im ursprünglichen WP-2-Scope nicht
  vorgesehene Endpunkte bekommen: `GET /api/fax/message/{id}/pdf` und
  `GET /api/fax/message/{id}/events` (inkl. Tests). Beide sind sinnvolle
  Ergänzungen für das Detail-Pane im Frontend (WP-10) und werden hiermit
  nachträglich als Teil von WP-2 bestätigt.
- WP-2 liefert aktuell **keine** Entwürfe (`folder=drafts`) — `send_fax`
  legt direkt `folder=outbox`, `status=queued` an. Der Frontend-Golden-Path
  endet deshalb im Postausgang statt in den Entwürfen. Falls ein
  Entwürfe-Flow gewünscht ist, braucht es einen zusätzlichen
  `POST /api/fax/draft`-Endpunkt (nicht in diesem Plan vorgesehen, bei
  Bedarf als eigenes WP nachreichen).
- WP-6a (ADR) ist **vorläufig**: ungeklärt, ob `pjsua2`/pjproject T.38
  tatsächlich unterstützt. WP-6b darf nicht gestartet werden, bevor das per
  praktischem Spike (nicht nur Websuche) geklärt ist.
- WP-4, WP-7, WP-11 sind offen. WP-6b, WP-8, WP-9 bleiben wie geplant
  blockiert.

---

## Empfohlene Reihenfolge (falls nicht alles parallel gefahren wird)

1. WP-0 (CI) zuerst oder parallel zu allem anderen.
2. WP-1, WP-2, WP-3, WP-5, WP-6a, WP-10 gleichzeitig starten — alle ohne
   Abhängigkeiten, berühren disjunkte Dateien.
3. Nach WP-3 + WP-4: WP-6b erst, wenn eine echte Fritz!Box/SIP-Testumgebung
   bereitsteht.
4. WP-7 jederzeit dazwischenschieben, niedrige Priorität.
5. WP-8/WP-9 bleiben blockiert, bis die jeweiligen Beispieldateien
   beschafft sind — das ist eine Aufgabe für dich, nicht für einen Agenten.
6. WP-11 gegen Ende des ersten funktionierenden Durchstichs (nach WP-1/2).
