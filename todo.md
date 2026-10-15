# TODO

Stand: **15.10.2026, abends**. Diese Datei enthält die aktuelle Restliste und die
heutigen Entscheidungen. Frühere Meldungen „offen“ bleiben als historischer
Stand im [Snapshot vom 15.10.2026](docs/archive/2026-10-15/todo.md) erhalten.
Ältere Snapshots: [Archivübersicht](docs/archive/README.md).
Abnahmen stehen in [VALIDATION.md](docs/VALIDATION.md), technische Folgeschritte
im [Implementierungsplan](docs/IMPLEMENTATION_PLAN.md).

## Aktuell bestätigt und abgeschlossen

- [x] Release/CI-Stand von Andreas als passend bestätigt. Nachtfix und
  Energie-Ledger-Kompatibilität committed; CI-Dateimount korrigiert.
- [x] PV-Nachtfix live: SMA-Leistungssentinel wird für beide PV-Wechselrichter
  als 0 W behandelt; plant ready und laufende Hausleistungswerte bestätigt.
- [x] Energie-Ledger nach ausdrücklichem Wunsch gesichert neu begonnen.
  MQTT zeigt anschließend Tages- und Durchschnittsstatus partial statt
  configuration-changed; beide Durchschnittswerte vorhanden. Alte Basen/Historie
  dieses Ledgers wurden mit dem Reset bewusst abgelöst; InfluxDB bleibt erhalten.
- [x] Debug-Abschaltung besprochen und von Andreas als soweit passend bestätigt.
  Berechnungslogs benötigen SMAB_PLANT_DEBUG_ENABLED=true und SMAB_LOG_LEVEL=DEBUG;
  normale Tages-/Durchschnittsstatus sind auch ohne Debug in MQTT sichtbar.
- [x] Frühere AC-Profil-Installation, Profilabgleich und vollständige Tagesprüfung
  einschließlich Mitternacht/Neustart/Datenlücken von Andreas abgenommen.
  Diese Abnahme nicht als pauschal offen wiederholen.
- [x] Inventar/Grafana aktualisiert: 48 Vergleichspaare, neue Vergütung enthalten,
  fünf neue Items historisiert, PV-Tages-/Gesamtertragslinks korrigiert und geprüft.
- [x] Aktuelle 41 aktive SMA-Daten-Things mit bisherigen Exporten abgeglichen.
  Keine zusätzlichen Item-Link-Transformationen laut Andreas. sma_undef.js ist
  weder dort noch in den aktuellen Things eingebunden.
- [x] InfluxDB-Index-Neuaufbau von Andreas ausgeführt und als erfolgreich bestätigt;
  die zwei fremden gelöschten Messreihen sind kein offener SMA-Fehler.

## Unmittelbare Restarbeiten

- [ ] Nach dem heutigen Reset den nächsten Mitternachtsübergang und Folgetag prüfen:
  Tagesstatus, Hausverbrauch mit/ohne Wallbox sowie beide Sieben-Tage-Durchschnitte.
  Heute enthält nur die seit dem Neustart gemessene Zeit. Frühere Abnahme bleibt
  gültig; dies ist die gezielte Kontrolle des neuen Resets/Fensters.
- [ ] Frühere Abweichung von Hausverbrauch ohne Wallbox untersuchen: gespeicherter
  Tageswert lag über der Bilanz aus demselben Zählersnapshot. Grobe PV-Zähler und
  monotoner Akzeptanzschutz sind zu prüfen, kein weiterer Reset als Ersatz.
- [ ] InfluxDB-Kopie unabhängig nachprüfen: 205.552 Punkte für zwei Home-Manager-
  Leistungen und Carport L3 wurden bestätigt geschrieben. L1/L2 hatten keine
  Quelldaten. Post-Copy-Abnahme fehlte wegen voller Query-Warteschlange.
  Vor Item-Löschung Regeln/UI/Links prüfen; Originaldaten erhalten.
  [Ablauf](docs/INFLUX2_ITEM_MIGRATION.md).
- [ ] Früheren Zeitraum mit gemischten PV-Tages-/Gesamtertragswerten im
  Gesamtertragsitem beurteilen; keine automatische Historienkorrektur.
- [x] 15 Zusatzkanäle einzeln bewertet und nachts um 21:39 lesend geprüft:
  vier Netzleistungen gültig, neun DC-Werte nicht verfügbar, zwei Carport-L1-Werte
  auf inaktiver Phase nicht verfügbar. Nach Andreas’ anschließender Entscheidung sechs DC-Strom-/Leistungskanäle
  mit bedingter Ersatznull umgesetzt: frische AC-Leistung 0 und Zustand OK.
  Spannungen bleiben nicht verfügbar. Lokal lesend um 21:58 bestätigt;
  Produktionsdeployment steht noch aus. Kein eindeutiger Standby-Code verfügbar.
  [Einzelbewertung](docs/INVALID_VALUE_AUDIT.md).
- [ ] Tagesrückkehr der neun DC-Kanäle prüfen; Umgang mit alten retained Werten
  bei einzelnen ungültigen Kanälen für openHAB/UI festlegen. Keine synthetischen
  Nullwerte oder automatische Historienänderungen.

## Produktionskonfiguration

- [x] smab.env.prod liegt als private Referenz vor; keine config.json und keine
  Host-Profilkopien laut Andreas. Git-Ausschluss für smab.env.* ergänzt.
- [x] Bereinigte smab.env.clean erstellt: 136 auf 64 aktive Variablen reduziert,
  Beschreibungen aus smab.example.env übernommen. Defaults mit Loader,
  gebündelten Profilen und Compose abgeglichen; aufgelöste Konfiguration offline
  gleich, besondere Präsenz-Semantik berücksichtigt, Werte/Quoting erhalten.
- [ ] Bereinigte Datei auf dem Zielhost übernehmen und nach Neuerstellung prüfen.
  Produktion nicht automatisch geändert. Private Konstanten/Zugangsdaten bleiben
  ausschließlich in ignorierten Dateien mit Modus 600.
- [ ] Bei endgültiger openHAB-Migration Energie-Offsets genau einmal anwenden und
  Rohzähler von korrigierten Gesamtständen unterscheiden. Keine zusätzlichen
  Transformationen an den bestätigten aktuellen Item-Links.

## Wallbox: Ruhe, Sitzungsreset und Zeitstempel

- [x] Laden am 15.10. lokal geprüft: einphasige L3-Leistung/Phasen/Gesamtenergie
  und Sitzungszuwachs plausibel. Kein allgemeiner Drei-Phasen-/Zielmodusnachweis.
- [x] Andreas bestätigt: Auto weiterhin angesteckt, heutige Ladung ungefähr
  13–16 Uhr. Ab-/Ansteckzeitpunkt beziehungsweise Sitzungswechsel nicht bestätigt.
- [x] Ruheprüfung API/SEMP und MQTT abgeschlossen: zwei Stichproben um 21:28/21:29,
  0 W, frischer konstanter Gesamtzähler, wartendes Fahrzeug. Sitzungsenergie
  unverändert mit Zeitstempel 16:28 und korrekt als stale gefiltert; MQTT zeigt
  alten retained Wert. [Evidenz](docs/ECHARGER_LIVE_CHECK_2026-10-15.md).
- [x] Absteck-Reset live bestätigt: Andreas abgesteckt, beide API/SEMP-Sitzungswerte
  frisch 0 kWh mit neuem Zeitstempel, Fahrzeug nicht verbunden; Gesamtzähler konstant.
- [x] Wiederanstecken von Andreas bestätigt: beide Quellen melden gesperrt, 0 W,
  Roh-Sitzungsenergie 0. Zeitstempel bleibt vom Abstecken und wird nach 180 s
  korrekt stale; Gesamtzähler bleibt frisch und konstant. Keine Ladefreigabe geändert.
- [ ] Nächsten Ladebeginn separat prüfen; andere Reset-Auslöser und gewünschte
  Publikationssemantik für letzte/aktuelle Sitzung bleiben eigenständige Fragen.
- [ ] Health/Event/Modus/Autorisierung brauchen natürliche Zustandsänderung oder
  belastbare Protokollsemantik. Alte Zeitstempel nicht auf Empfangszeit erneuern.
- [ ] Erst danach pro Kanal Frischepolitik und Nutzen des Timestamp-Recorders
  entscheiden; Aufzeichnungen separat archivieren. Kein pauschales Filterabschalten.

## Verbleibende openHAB-/Messwertabnahme

- [ ] Alle 100 [Migrationszeilen](docs/migration-coverage.csv) einschließlich Regeln,
  Maps, Vorzeichen, UI, Persistence und Tages-/Sommerzeitgrenzen abschließen.
  Aktuelle [Zuordnung](docs/OPENHAB_ITEM_MAPPING.md) verwenden; historische Zahlen
  zu unzugeordneten Altlinks nicht als aktuelle Restanzahl übernehmen.
- [ ] Numerische Grafana-Vergleiche nur für noch ungeklärte Serien abschließen;
  Erstellung/Aktualisierung des Vergleichsdashboards ist erledigt.
- [ ] Home-Manager-DateTime-Link auf planttimeiso prüfen; numerisches planttime
  für bestehende Historie getrennt erhalten. Neues Naming batteryenergyreturnratio
  verwenden, keine erneute Einführung des alten Namens batteryefficiency.
- [ ] Basic-Abdeckungsstatus bei Diagnose=false sowie Home-Manager-Protokolldiagnosen
  unabhängig von Advanced gezielt abnehmen. Basic-Tagesstatus sind aktuell sichtbar.
- [ ] Storage-Frequenz und AC-Strom L1 separat vergleichen; Sunny-Boy-L2/weitere
  Phasen bisher ohne gültigen Nachweis nicht umdeuten. DC-B-Belegung bleibt offen.
- [ ] Weitere natürliche Derating-Zustände prüfen; „Keine Abregelung“ bereits belegt.
  AC-Batterieenergiegrenze ist gut belegt; Resetverhalten und Rückgabegrad bleiben
  von einem unabhängig gemessenen physikalischen Wirkungsgrad zu unterscheiden.

## Ladeprüfungen und spätere Pflege

- [ ] Garagenwidget bei natürlichem Laden live abnehmen: Anzeigen, Bedienung,
  reaktive Aktualisierung und unveränderte Schreibsperren; installierte YAML sichern.
- [ ] Physische Ladezielerreichung, Rückkehr aus Zielmodus und weitere Lastpunkte
  prüfen; maximale Ladeleistung/Winter-Einphasenbetrieb gemäß
  [Grenzen und Belegen](docs/ECHARGER_POWER_LIMIT.md). Schreiben nur mit Zielauftrag;
  Home Manager bleibt Regler.
- [ ] Watchtower/Autoheal für diese Bridge und Versionsstrategie prüfen; vorhandene
  Host-Container allein belegen noch keine passende Service-Einbindung.
- [ ] Docker-Bridge-Netzwerk bei Home-Manager-Modbus bei Bedarf bewerten;
  UDP-Multicast nur bei gewähltem UDP. Frühere Betriebs-/Ressourcenabnahme bleibt zu.
- [ ] Hersteller-Pollergrenzen und konkrete Alarmgrenzen bei Bedarf dokumentieren;
  weitere Vereinfachungen nur mit konkretem Nutzen. Später Wiki aus
  [openHAB-Anleitung](openHAB/openHAB.md).

## Zurückgestellte Erweiterungen

- [ ] Weitere Modbus-/Wallbox-/SEMP-/Portal-Kanäle erst nach Priorisierung:
  [Modbus-Audit](docs/MODBUS_TOPIC_AUDIT.md),
  [Wallbox-Audit](docs/ECHARGER_TOPIC_AUDIT.md),
  [SEMP-Steuerwerte](docs/ECHARGER_CONTROL_OBSERVATIONS.md).
  Insbesondere Schein-/Blindleistung, Leistungsfaktor, alternative PV-Zähler,
  BMS-Strings, GI1/GO1, Capability-/Planungsfelder, PCC-/Fallbackgrenzen und
  aktueller Lademix brauchen eigene Evidenz; keine neuen Setter automatisch.
- [ ] Ursache delegierter Home-Manager-NaN-Werte nur bei Bedarf prüfen; kein
  Grid-Guard-Testschreiben. Mindest-PV und Tagesanteile sind kein Live-Lademix.

API-only-Fallback-Ausbau bei abgeschaltetem SEMP bleibt aus dem Umfang gestrichen.
