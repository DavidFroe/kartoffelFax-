# 🥔 KartoffelFax

Ein moderner, plattformübergreifender Open-Source-Nachfolger für **AVM Fritz!fax
für Fritz!Box**. Die Original-Software läuft unter Windows 11 nicht mehr
zuverlässig und wurde für Linux nie nativ angeboten — KartoffelFax schließt
diese Lücke.

## Features (geplant / in Arbeit)

- **Plattformübergreifend:** läuft nativ unter Windows 11 und Linux (Ubuntu,
  Debian, Fedora/Bazzite, …).
- **Vertraute Oberfläche:** 3-Spalten-Layout (Ordner → Nachrichtenliste →
  Vorschau/Detail), angelehnt an die funktionale Struktur von Fritz!fax.
- **WireGuard/VPN-ready:** funktioniert transparent, wenn die Fritz!Box remote
  über eine VPN-IP (z. B. `192.168.178.1` über `wg0`) erreichbar ist.
- **SIP/VoIP & TR-064 statt CAPI:** die Fritz!Box wird direkt als SIP-Endgerät
  (T.38/G.711) sowie über die TR-064-API angesprochen. Ein CAPI-over-TCP-Fallback
  für lokale Windows-Installationen ist optional vorgesehen.
- **Altdaten-Import:** Einlesen alter AVM-Telefonbücher (`.srl`) sowie Migration
  historischer Fax-Datenbanken in eine lokale SQLite-Datenbank.
- **PDF-Workflow:** Dokumente per Drag & Drop versenden (Konvertierung zu
  G3/T.38), eingehende Faxe werden automatisch als PDF gespeichert.

## Tech-Stack

| Bereich    | Technologie                                             |
|------------|----------------------------------------------------------|
| Backend    | Python 3.11+, FastAPI, Asyncio, SQLite (aiosqlite), Pydantic |
| Frontend   | HTML5, TailwindCSS, JavaScript (WebSockets für Live-Status) |
| Packaging  | PyInstaller (Windows/Linux-Binaries), Docker, Flatpak (Linux) |

## Projektstruktur

```
kartoffelFax/
├── backend/
│   └── kartoffelfax/
│       ├── main.py              # FastAPI-Einstiegspunkt
│       ├── config.py            # Konfiguration (pydantic-settings)
│       ├── db/                  # SQLite-Schema, Connection-Handling, Migrationen
│       ├── api/                 # REST-Routen + WebSocket (Fax, Kontakte, Settings)
│       ├── core/
│       │   ├── fritzbox/        # TR-064-Client, SIP/VoIP-Client, CAPI-Fallback
│       │   ├── fax/             # PDF→G3-Konvertierung, Fax-Empfang
│       │   └── importers/       # .srl-Telefonbuch-Parser, Legacy-DB-Import
│       └── schemas/             # Pydantic-Modelle
│   └── tests/
├── frontend/
│   ├── index.html                # 3-Spalten-Layout
│   └── static/{css,js,icons}/
├── packaging/
│   ├── pyinstaller/
│   ├── flatpak/
│   └── docker/
└── docs/
```

## Entwicklung

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
uvicorn kartoffelfax.main:app --app-dir backend --reload
```

Die App ist danach unter <http://127.0.0.1:8000> erreichbar (Frontend wird
direkt von FastAPI ausgeliefert).

## Status

Frühe Grundgerüst-Phase: Repository-Struktur, SQLite-Schema und API-/UI-Skelette
stehen; die eigentliche TR-064/SIP-Anbindung, der PDF→Fax-Workflow und die
Altdaten-Importer (`.srl`, Legacy-DB) sind als Stubs angelegt und folgen als
nächste Schritte.

## Lizenz

[GPL-3.0-or-later](LICENSE)
