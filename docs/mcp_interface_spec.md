# KartoffelFax MCP-Schnittstellenspezifikation

Status: **Entwurf**, noch nicht implementiert (siehe WP-13 in
[`DEV_PLAN.md`](DEV_PLAN.md)). Dieses Dokument legt fest, welche Tools ein
MCP-Server für KartoffelFax anbietet, bevor jemand Code dafür schreibt.

## Zweck

Ein LLM (z. B. Claude über Claude Desktop/Code) soll KartoffelFax als
Werkzeug benutzen können: Kontakte nachschlagen, den Posteingang/-ausgang
abfragen, ein Fax vorbereiten und (mit Bestätigung) versenden. Das ist eine
**zusätzliche Transport-Schicht**, keine neue Business-Logik — die Tools
rufen dieselben Repositories unter `backend/kartoffelfax/db/repositories/`
auf, die auch die REST-API in `backend/kartoffelfax/api/` benutzt.

## Architektur

- Eigener Einstiegspunkt `kartoffelfax-mcp` (neues Script in
  `pyproject.toml` neben `kartoffelfax`), implementiert mit dem offiziellen
  Python-`mcp`-SDK.
- **Transport: stdio, lokal, standardmäßig kein Netzwerk-Listener.**
  KartoffelFax verwaltet Fritz!Box-Zugangsdaten und kann (sobald WP-6b
  steht) echte Telefonate auslösen — das ist kein Dienst, den man ohne
  weiteres Nachdenken über HTTP/SSE exponieren sollte. Eine
  Netzwerk-Transport-Option kann später ergänzt werden, aber nur hinter
  eigener Authentifizierung, nicht als Standard.
- Importiert direkt die Repositories (`contact_repository`,
  `fax_repository`, `connection_repository`) statt über die REST-API zu
  gehen — spart eine Transport-Hürde, braucht aber dieselbe
  `kartoffelfax.db.database`-Initialisierung (`init_db()`) beim Start des
  MCP-Prozesses.
- Liegt unter `backend/kartoffelfax/mcp/` (neues Package: `server.py`,
  `tools.py`).

## Sicherheitsmodell (bindend, nicht optional)

1. **Zugangsdaten nie zurückgeben.** Jedes Tool, das
   `fritzbox_connections`-Daten liest, maskiert `tr064_password_enc` /
   `sip_password_enc` vollständig (nicht mal verschlüsselt anzeigen).
2. **Versenden erfordert zwei Schritte.** `fax.queue_send` ohne
   `confirm=true` liefert nur eine Vorschau (Zielnummer, Seitenzahl,
   verknüpfter Kontakt) zurück und legt **nichts** in der DB an. Erst mit
   `confirm=true` wird tatsächlich eine Zeile in `fax_messages`
   (`status=queued`) erzeugt. Sobald WP-6b (echter SIP-Versand) steht, gilt
   dieselbe Regel für das tatsächliche Wählen — ein LLM darf nie in einem
   Schritt sowohl entscheiden als auch unwiderruflich auslösen.
3. **Standardmäßig lokal.** Kein Netzwerk-Transport ohne explizite
   Konfiguration (siehe oben).
4. **Gleiche Validierung wie die REST-API.** Tools nutzen dieselben
   Pydantic-Schemas aus `backend/kartoffelfax/schemas/`, keine duplizierte
   oder laxere Validierung.

## Tools

| Tool | Wirkung | Risiko-Stufe |
|---|---|---|
| `contacts.list(query?)` | liest `contacts` | read-only |
| `contacts.get(id)` | liest einen Kontakt | read-only |
| `contacts.create(payload)` | legt Kontakt an | mutierend, reversibel |
| `contacts.update(id, payload)` | ändert Kontakt | mutierend, reversibel |
| `contacts.delete(id)` | löscht Kontakt | mutierend, reversibel |
| `fax.list(folder)` | listet `fax_messages` nach Ordner | read-only |
| `fax.get(id)` | Status, Metadaten, `fax_events`-Timeline | read-only |
| `fax.get_pdf(id)` | liefert PDF als Binär-Resource | read-only |
| `fax.upload_document(file)` | speichert Datei unter `uploads/`, gibt `stored_path` | mutierend, reversibel (nur Datei im Upload-Verzeichnis) |
| `fax.queue_send(fax_number, subject?, contact_id?, source_file_paths, confirm=false)` | ohne `confirm`: Vorschau; mit `confirm=true`: legt `status=queued` an | **mutierend, siehe Sicherheitsmodell Punkt 2** |
| `fax.cancel_queued(id)` | entfernt eine noch nicht gewählte Fax-Zeile | mutierend, reversibel solange `status=queued` |
| `settings.list_connections()` | Verbindungsprofile, Passwörter maskiert | read-only |
| `settings.test_connection(id)` | TR-064-Reachability-Check, keine Datenänderung | read-only (Netzwerk-Seiteneffekt) |
| `settings.create_connection(payload)` | legt Profil an, Zugangsdaten werden über `core/security.py` verschlüsselt gespeichert | mutierend, reversibel |

Absichtlich **nicht** im ersten Umfang: `settings.delete_connection` und
jedes Tool, das den tatsächlichen SIP-Versand direkt auslöst, bevor WP-6b
abgeschlossen und das Bestätigungs-Verhalten dafür separat geprüft ist.

## Fehlerverhalten

MCP-Tool-Fehler spiegeln die `HTTPException`-Semantik der REST-API:
`404` → "nicht gefunden"-Fehlertext, `400` (z. B. unbekannter
`contact_id`, nicht-existierender `stored_path`) → Validierungsfehler mit
derselben Meldung wie in `routes_fax.py`/`routes_contacts.py`. Keine
stillen Fehlschläge — ein Tool-Call liefert entweder ein Ergebnis oder
einen MCP-Error, nie `null` bei einem tatsächlichen Fehler.

## Offene Fragen für die Implementierung (WP-13)

- Soll `fax.queue_send`-Vorschau (ohne `confirm`) bereits die
  PDF-Zusammenführung aus `core/fax/pdf_to_fax.py` anstoßen (um Seitenzahl
  korrekt anzuzeigen), oder reicht eine Schätzung? Tendenz: ja anstoßen,
  aber in ein temporäres Verzeichnis, nicht in `outbox`.
- Wird der MCP-Server als eigener Prozess neben `uvicorn` gestartet, oder
  teilen sich beide dieselbe SQLite-Datei bei parallelem Zugriff
  (SQLite erlaubt das, aber Timeouts/Locking sollten getestet werden)?
