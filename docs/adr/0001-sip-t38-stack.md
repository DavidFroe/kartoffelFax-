# ADR 0001: SIP/T.38-Stack für den Faxversand

- Status: **Vorläufig (Proposed)** – Recherche per Websuche, nicht praktisch validiert
- Datum: 2026-11-08
- Betrifft: WP-6b (`core/fritzbox/sip_client.py`)

## Kontext

KartoffelFax soll Faxe über die Fritz!Box senden und empfangen, ohne CAPI. Dazu
registriert sich die App als IP-Telefon an der Fritz!Box (Telefonie →
Telefoniegeräte → „LAN/WLAN (IP-Telefon)"), LAN oder WireGuard-Tunnel
spielen keine Rolle. Faxe laufen über T.38 (UDPTL) oder als G.711-Audio mit
Software-Faxmodem. Ob T.38 oder G.711 greift, hängt laut AVM-Doku und
Forenberichten vom Provider und von der T.38-Einstellung der Fritz!Box ab.

Das Projekt braucht: Registrierung, Anruf auf/ab, T.38-Aushandlung und
Fax-Protokoll (T.30), Packaging per PyInstaller für Windows 11 und Linux.

## Was die Recherche belegt – und was nicht

| Aussage | Status |
|---|---|
| Asterisk hat T.38 über `res_pjsip_t38` (eigenes Modul mit T.38-Zustandsmaschine, SDP, UDPTL) auf PJSIP aufgesetzt | belegt (Asterisk-Mailinglisten) |
| pjproject/pjsua2 bringt T.38/UDPTL selbst mit | **nicht belegt.** Keine Treffer in pjproject-Doku; alle T.38-Treffer betreffen Asterisks eigene Schicht. Starke Vermutung: nein |
| spandsp (T.38-Kern + Faxmodem) ist LGPL-2.1, Testsuite GPL | belegt (Distro-Metadaten) |
| Python-Bindings für spandsp / Windows-Build von spandsp | **nicht gefunden**, offen |
| Offizielle pjsua2-Wheels auf PyPI | **nicht geprüft**; üblich ist Build aus Quellen via SWIG |
| Fritten&Fax (Open Source, Windows/Android) faxt per SIP ohne CAPI, registriert sich als IP-Telefon an der Fritz!Box | belegt (Forum), Quellcode und T.38-Handling **nicht eingesehen** |

## Optionen

**A: pjsua2 (pjproject) für SIP/RTP + spandsp als Faxmodem über G.711**
Ausgereifter SIP-Stack mit Python-Bindings, GPL-2.0 (oder kommerziell) –
kompatibel mit GPL-3.0-or-later des Projekts nur mit Prüfung der
Lizenzkompatibilität (GPLv2-only vs. GPLv3). Kein T.38; Fax läuft als
G.711-Audio, dafür muss spandsp-Faxmodem-Audio erzeugen/dekodieren. Risiko:
G.711-Fax ist störanfälliger (Jitter, Paketverlust, Echo-Kompensation).

**B: Eigener asyncio-SIP/UDPTL-Stack + spandsp (`t38_terminal`)**
Volle Kontrolle, echtes T.38, keine schwere C-Abhängigkeit für SIP. Aufwand
hoch (SIP-Digest-Auth, SDP, Retransmits, UDPTL-Redundanz/FEC), spandsp muss
über ctypes/cffi eingebunden werden, Windows-Build offen.

**C: Referenz Fritten&Fax prüfen, ggf. Architektur übernehmen**
Existiert, ist Open Source, löst genau dieses Problem. Vor jeder
Eigenentwicklung den Quellcode lesen (Stack, T.38 ja/nein, Lizenz).

## Entscheidung (vorläufig)

**WP-6b baut nicht blind auf einer dieser Optionen auf.** Stattdessen ein
kurzer praktischer Spike als Gate vor WP-6b:

1. Quellcode von Fritten&Fax lesen: welcher SIP/Fax-Stack, T.38 oder G.711,
   Lizenz.
2. Minimal-PoC mit Option A: Registrierung an einer Fritz!Box als
   IP-Telefon, ein Testanruf mit G.711. Danach Fax-Senden mit spandsp.
3. Entscheidung A vs. B anhand des PoC und der Packaging-Tauglichkeit
   (PyInstaller, Windows).

Arbeitshypothese: **A als Einstieg** (schnellster Weg zu einem funktionierenden
Versand), T.38 (Option B) als spätere Erweiterung, falls G.711 in der Praxis
zu unzuverlässig ist.

## Systempakete (ungeprüft, im Spike verifizieren)

- Linux (Debian/Ubuntu/Mint): `build-essential python3-dev swig libssl-dev
  libspandsp-dev ghostscript`
- Windows 11: Visual Studio Build Tools (MSVC), SWIG, pjproject aus Quellen;
  spandsp-Build offen.

## Konsequenzen

- WP-6b bleibt blockiert, bis der Spike entschieden ist und eine echte
  Fritz!Box oder ein SIP-Testserver (Asterisk mit T.38) verfügbar ist.
- Die Lizenzfrage (pjproject GPLv2 vs. Projekt GPLv3+, spandsp LGPL) muss
  vor der Entscheidung geklärt werden.
- Packaging: C-Abhängigkeiten (pjsua2, spandsp) erschweren PyInstaller; im
  Spike früh testen.

## Quellen

- Asterisk `res_pjsip_t38` Code-Review: <https://lists.digium.com/pipermail/asterisk-dev/2013-July/061450.html>
- AVM: Externes Fax einrichten: <https://at.fritz.com/en/apps/knowledge-base/fritz-box-7590-ax/108_Setting-up-an-external-fax-in-the-FRITZ-Box>
- Fritten&Fax (Forum): <https://www.ip-phone-forum.de/threads/fritten-fax-%E2%80%93-kostenloses-fax-f%C3%BCr-die-fritz-box-windows-10-11-android-open-source.327009/post-2649898>
- spandsp-Lizenz (Alpine-Paket): <https://pkgs.alpinelinux.org/package/v3.20/main/x86_64/spandsp>
