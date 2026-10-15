# TODO

Stand: **15.10.2026**. Diese Liste enthält nur verbleibende Aufgaben und offene
Fragen. Abnahmen und Nachweise stehen in [docs/VALIDATION.md](docs/VALIDATION.md),
die Reihenfolge im [Implementierungsplan](docs/IMPLEMENTATION_PLAN.md).

Die bisherigen Tagesberichte und erledigten Aufgaben bleiben im
[Snapshot vom 13.10.2026](docs/archive/2026-10-13/todo.md) erhalten. Frühere
Entscheidungen und die ursprünglichen Fragen Q01–Q27 stehen auch im
[Archiv vom 11.10.2026](docs/archive/2026-10-11/todo.md). Historische Aussagen
wie „noch offen“ beschreiben den damaligen Stand, nicht die aktuelle Aufgabenliste.

## Nächste Schritte

- [ ] Topic-Gruppierung nach separatem Deployment live prüfen: sieben Basic-
  Abdeckungsstatus bei abgeschalteter Diagnose sichtbar; Home-Manager-Protokoll-
  diagnosen unabhängig von Advanced. Verwendete Host-Profile gezielt abgleichen,
  Zustand/Topics/Item-Links erhalten. [Zuordnung](docs/TOPIC_GROUPS.md).

- [ ] Bei **bezogener Energie** und **eingespeister Energie** die bestehenden
  openHAB-Offsets wegen des Energy-Meter-Wechsels berücksichtigen. Rohzähler und
  korrigierte Gesamtstände eindeutig unterscheiden; Offsets bei Migration,
  Berechnungen und Alt-/Neu-Vergleichen genau einmal anwenden und die Kontinuität
  bestehender Historien erhalten. ENV-Offsets und Rohzähler-Diagnosen sind lokal
  implementiert und offline geprüft; private Werte, Deployment und Entfernung
  der bisherigen openHAB-Korrekturen bleiben offen. Konkrete Offsetwerte bleiben privat.

- [x] Vergütung auf tatsächliche Netzeinspeisung × gemeinsamen Anlagentarif
  umgestellt; vorherige PV-Ertragsbewertung ausdrücklich ersetzt. Home Manager
  ist bevorzugte Quelle; doppelte Wechselrichter-Netzzähler werden nicht addiert.
  Zwei Sieben-Tage-Hausdurchschnitte unter sma-plant lokal umgesetzt.
  Später angepasst: heute plus sechs Vortage, verfügbare Tage mitteln; Wallbox abziehen statt
  ganze Ladetage ausschließen. Währung frei konfigurierbar, Standard €.
- [ ] Neue Vergütungs-/Durchschnittskanäle nach separatem Deployment live prüfen;
  das neue Fenster einschließlich heute vergleichen. Bestehende openHAB-Berechnungen bis zur
  getrennten Migration erhalten. Gemeinsamen Tarif und gegebenenfalls historischen
  Einspeise-Offset privat in smab.env eintragen.
- [ ] Durchschnittsverbrauch mit verfügbaren Tagen einschließlich heute prüfen: Berechnung mit und ohne Wallbox anhand der
  zugrunde liegenden Tageswerte nachvollziehen und Ergebnisse auf Plausibilität
  prüfen.

- [ ] Produktions-`smab.env` aufräumen: nur Werte behalten, die von den wirksamen
  Standardwerten abweichen, einschließlich notwendiger installationsspezifischer
  Angaben und Zugangsdaten. Defaults aus Loader und Compose abgleichen und prüfen,
  dass die bereinigte Datei dieselbe wirksame Konfiguration ergibt. Private Werte
  nicht protokollieren oder in öffentliche Beispiele übernehmen.

- [x] Neuer AC-Profil-Build auf dem Zielhost installiert, verwendete Profile
  abgeglichen, Energie-Ledger gesichert zurückgesetzt und installierte Version
  geprüft: von Andreas am 15.10.2026 als erledigt bestätigt.
- [x] Energieberechnungen über einen vollständigen Tag einschließlich Mitternacht,
  Neustart und Datenlücken live abgenommen: von Andreas am 15.10.2026 bestätigt.
  Feinere PV-Zähler bleiben eine getrennte mögliche Verbesserung.
- [ ] Grafana-/InfluxDB-Datenquelle, Schema, effektive Persistence und Messreihennamen
  lesend inventarisieren; anschließend Dashboard für die wichtigen Alt-/Neu-Paare
  aus [Vergleichsmatrix](docs/pv-comparison-2026-10-14.csv) erstellen. 38 aktuelle
  direkte Paare vorhanden, Anlagensummen lokal implementiert. Historien erhalten.
- [ ] Home-Manager-Item `smahomemanager_Anlagenzeit_DateTime` prüfen: aktueller Link
  zeigt noch auf numerisches planttime statt planttimeiso. Keine Änderung oder
  konkrete Wertstörung aus dem Inventar ableiten; bestehende Abhängigkeiten sichern.

- [x] Tagesbezug, Tageseinspeisung, Haus-Tagesverbrauch und Tagesverbrauch mit/
  ohne Wallbox sind umgesetzt und von Andreas am 15.10.2026 live abgenommen.
  Weitere openHAB-Migration und feinere PV-Zähler bleiben getrennte Aufgaben.

- [x] Freiwilliger Ressourcenvergleich nach dem Update abgeschlossen: vollständige
  24-Stunden-Datei am 14.10.2026 ausgewertet. [Nachweis](docs/RESOURCE_SOAK_ANALYSIS_2026-10-14.md):
  stabile CPU/Speichernutzung, alle Stichproben healthy, keine Neustarts. Installierte
  Version ist im Recorder nicht enthalten; separate Versionsbestätigung bleibt offen.
- [x] Vor diesem Deployment verwendete Host-Profilkopien mit den gebündelten
  Änderungen abgleichen (M01–M04/M09 und neue Gruppierungen), Zustandsvolume und
  bestehende Links/Historien erhalten. Von Andreas am 15.10.2026 bestätigt.
- [ ] Nach Deployment neue Kennzahl `measurements/batteryefficiency`, Basic-
  Verfügbarkeit von `diagnostics/deratingreason` und Home-Manager-ISO-Topic
  `measurements/planttimeiso` live prüfen. Bestehendes DateTime-Item bei Bedarf auf
  ISO-Link umstellen; Unix-Kanal `measurements/planttime` bleibt Advanced und muss
  für bestehende numerische Items/Historie weiter aktiviert sein.

## Zeitstempel und Datenqualität (Review 4 / E07)

- [ ] Verbleibende Wallbox-Kanäle anhand vorhandener und weiterer natürlicher
  Lade-/Ruheübergänge einordnen: Sitzungsenergie im Leerlauf und Resetgrenzen,
  Health-/Event-/Modus-/Autorisierungswerte, Phasenspannung/-leistung und alternative
  Energiekanäle. Je API/SEMP unterscheiden, ob Zeitstempel Erfassung oder Änderung
  bedeuten. Eindeutig periodische Kanäle sind bereits korrigiert; ungeklärte
  Filter nicht pauschal aufheben. [Erste Auswertung](docs/ECHARGER_TIMESTAMP_ANALYSIS_2026-10-12.md).
  [Liveprüfung am 15.10.2026](docs/ECHARGER_LIVE_CHECK_2026-10-15.md): aktuelle
  Leistung/Phasen/Gesamtenergie und Sitzungszuwachs während einphasiger Ladung
  plausibel; Ruhe/Reset und alte Health-/Event-/Modus-Zeitstempel weiter offen.
- [ ] Daraus verbleibenden Nutzen/Risiko der Frischeprüfungen entscheiden und
  gezielte Tests/UI-Abnahme abschließen. Anschließend separat entscheiden, ob
  Zeitstempeldiagnose deaktiviert und Aufzeichnungen archiviert/entfernt werden.
  Ressourcenrecorder wurde bereits aufgeräumt; das ist eine andere Aufzeichnung.

## Verbleibende openHAB-/Messwertabnahme

- [ ] Vollständige Migration aller 100 [Ledgerzeilen](docs/migration-coverage.csv)
  einschließlich sieben noch nicht zugeordneter Altlinks, Regeln, Maps, Vorzeichen,
  privaten Offsets, UI, Persistence und Tages-/Sommerzeitgrenzen abnehmen
  (Q02/Q09/Q12/Q14–Q19/Q27). Bereits bestätigte Wechselrichterwerte und ausgewählte
  Neustart-/Historienvergleiche nicht erneut als offen führen.
- [ ] Grafana-Parallelvergleich alter/neuer Zeitreihen für noch ungeklärte
  Migrationswerte erstellen, gleiche Einheiten und Messzeitpunkte verwenden.
- [ ] Noch nicht einzeln bestätigte Storage-Frequenz und AC-Strom L1 vergleichen
  (Rest M03). Sunny-Boy-L2 hat Metadaten, aber bisher SMA-NaN; keine gültigen Werte
  oder L1-Umdeutung behaupten. DC-B-Belegung bleibt unbekannt, Nullwerte sind gültig.
- [ ] Batterieenergie-Messgrenze und Resetverhalten bei Bedarf klären (M05/Q14).
  Beide Zähler sind plausibel und haben laut Andreas gemeinsamen Beginn;
  Energierückgabegrad ist kein unabhängig verifizierter physischer Wirkungsgrad.
- [ ] Andere Derating-Zustände nur bei natürlichem Auftreten vergleichen (M08).
  Aktuell „Keine Abregelung“ bestätigt; keine Testfehler absichtlich erzeugen.

## Ladeprüfungen – bis zum nächsten möglichen Laden zurückgestellt

- [ ] Vereinfachtes Garagenwidget beim nächsten Autoladen live testen:
  Fahrzeug-/Ladeanzeige, Lademodus, Ladeberechtigung, PV-/Planbedienung und
  Bestätigungen sowie unveränderte Schreibsperren bei Statuswechseln prüfen.
  Reaktive Aktualisierung ohne Seitenneuladen beobachten. Offline-Gleichheit ist
  bestätigt; MainUI-Abnahme bleibt offen. Vorher installierte Widget-YAML sichern
  und bei Abweichungen zurückspielen; denselben Installationsweg verwenden.
- [ ] Wallbox-L1/L2/L3-Wirkleistung und Gesamtleistung beim Laden vergleichen
  (E01). Einphasige L3-Stichprobe am 15.10.2026 im MQTT Explorer und per lokaler
  API bestätigt; alle Phasenwerte und Gesamtleistung konsistent. Weitere natürliche
  Betriebspunkte und openHAB-Itemvergleich bleiben getrennt. Passende Number:Power-
  Items mit W; bestehenden Gesamtzähler erhalten.
- [ ] Physische Ladezielerreichung, Sitzungsenergie und Rückwechsel aus Zielmodus
  prüfen (Q12/Q14). Bestätigte Planübertragung ersetzt nicht die Zielerreichung.
- [ ] Maximale Ladeleistung physisch abnehmen und einphasiges Winterladen
  untersuchen. [Grenzen und Belege](docs/ECHARGER_POWER_LIMIT.md). Neue Setter nur
  mit bestätigter Semantik/Units/Berechtigung; Live-Schreiben nur mit ausdrücklich
  angeforderten Zielwerten. Home Manager bleibt Laderegler.

## Infrastruktur und spätere Pflege

- [ ] Watchtower/Autoheal auf dem Zielhost einrichten und prüfen; automatische
  Updates mit Versionspinning abstimmen, Zustandserhalt und Wiederanlauf sichern.
- [ ] Docker-Bridge-Netzwerk bei Home-Manager-Modbus in beiden Compose-Dateien
  bewerten/umsetzen und Geräte-/MQTT-/DNS-/TLS-Verbindungen danach prüfen
  (Q04/Q05/Q10/Q26/Q27). UDP-Multicast nur abnehmen, wenn UDP tatsächlich gewählt
  wird. Bestehende Betriebsabnahme vom 13.10.2026 ist geschlossen.
- [ ] Herstellergrenzen für kurze Poller, Blockgrößen und Verbindungen bei Bedarf
  dokumentieren (Q07/Q21), konkrete Alarmgrenzen festhalten (Rest Q08).
  Betriebs-/Ressourcenprüfungen nicht deshalb erneut durchführen.
- [ ] Kleine Diagnose-/Frischeverbesserungen und gezielte Code-/Widgetvereinfachung
  nach konkretem Nutzen auswählen; gezielte Linterregeln am 13.10.2026 ergänzt.
  Formatierung, Importordnung und benannte Setting-Definitionen sind erledigt.
- [ ] Später Wiki-Artikel aus [openHAB-Anleitung](openHAB/openHAB.md) erstellen.
  Beispiel-Item-Dateien und Sitemaps bleiben aus dem Umfang gestrichen.

## Zurückgestellte Erweiterungen

Seit 13.10.2026 auf Andreas’ Wunsch nachrangig; erst nach erneuter Priorisierung
untersuchen oder implementieren. Bestandsbefunde bleiben in den verlinkten Audits.

- [ ] Weitere Modbus-Kandidaten auswählen (Q06/Q19, M06/M10): Schein-/Blindleistung,
  Leistungsfaktor, alternative Ertragszähler und Zeitdopplungen. 433 NaN und zwei
  nicht dekodierbare BMS-Strings bleiben aus erster Auswahl ausgeschlossen.
  [Registeraudit](docs/MODBUS_TOPIC_AUDIT.md), [Scan](docs/MODBUS_AVAILABILITY_2026-10-12.md).
- [ ] Drei vorhandene SEMP-Steuerwerte fachlich klären: ChrgActCnt-Zählumfang sowie
  WSptMaxNom/WSptMinNom-Einheit, Normierungsbasis, Vorzeichen und Wirkung. Keine
  PV-/Netzanteile oder Setter ableiten. [Bericht](docs/ECHARGER_CONTROL_OBSERVATIONS.md).
- [ ] Wallbox E02/E03/E05/E06: Schein-/Blindleistung, GI1/GO1, Ereignisse und
  Kommunikationsdiagnosen, weitere SEMP-Status-/Capability-/Planungsfelder und
  Ladeparameter (AMinCha, Plan.DurTmm, UseEnergyMeter, AcALim, PCC-Grenzen/Fallbacks).
  WMax nicht mit WMaxIn verwechseln; AveragePower nicht als Momentanleistung
  behandeln. [Kanalaudit](docs/ECHARGER_TOPIC_AUDIT.md).
- [ ] Home-Manager-Ursache der 45 delegierten NaN-Werte nur bei Bedarf klären;
  keine unbelegte dauerhafte Nichtunterstützung, kein Grid-Guard-Login/Testschreiben.
- [ ] Weitere Portalwerte/Profile und aktueller Lademix prüfen (Q22), nur mit
  bestätigten Einheiten, Zeitbezug und Gerät. Tagesanteile/Mindest-PV-Präferenz
  sind kein aktueller Lademix. Keine zusätzlichen Schreibfreigaben automatisch.

API-only-Fallback-Ausbau bei abgeschaltetem SEMP (E04) ist gestrichen.
Bestehende API-/SEMP-Mappings und alle bisherigen Topics bleiben erhalten.

## 2026-10-13 – Aufgabenliste bereinigt und Historie archiviert

- Vollständigen vorherigen Stand und Implementierungsplan als datierte Snapshots
  archiviert, erledigte Aufgaben/Tagesberichte aus dieser aktiven Liste entfernt.
- Doppelte Zeitstempelaufgaben zusammengeführt. Bestätigte M01-L3-, M02/M04-,
  Tripower-/Sunny-Boy-M03-, M07- und M09-Wertevergleiche nicht erneut offen geführt.
  Nicht bestätigte Restteile bleiben ausdrücklich erhalten.
- Ressourcenprüfung (22 h), Betriebsabnahme, Portal-Refresh/Widgets,
  Betriebsdauer-Anzeige und bisherige Reviews/Clean-Code-Schritte abgeschlossen.
  Migrations-/Lade-/Semantikfragen und lokaler v0.3.8-Release bleiben getrennt offen.
- Keine Runtime-/Geräte-/openHAB-Änderung, Veröffentlichung oder Deployment.
- Validierung: vollständiger Linter über 142 öffentliche Dateien, lokale Linkziele
  einschließlich Archivverweise und Diff-Prüfung bestanden.

## 2026-10-13 – Wiederholte Widget-Ausdrücke vereinfacht

- Auftrag von Andreas: Vereinfachung umsetzen, anschließend testen; Rückrollen bei Bedarf möglich.
- Drei Funktionen im vorhandenen oh-context: lokale Schreibsperre, separate Portal-Schreibsperre und Lademodus. Insgesamt 29 wiederholte Ausdrücke ersetzt; dynamische Auswertung statt einmaliger Konstanten. Offizielle openHAB-Dokumentation konsultiert.
- Kanonische YAML und generierter MainUI-Import aktualisiert. Vollständiger Vergleich der eingelesenen YAML nach Rückersetzung aller Funktionsaufrufe bestätigt Gleichheit mit der Ausgangsfassung; Props, Layout, Bestätigungen, Eingabegrenzen und Payloads erhalten.
- Anleitung um UI-/Reaktivitätsprüfung und Rückrollen über vorher gesicherte installierte YAML ergänzt. Live-MainUI-Test offen; keine Gerätebefehle oder Installation durchgeführt.
- Validierung: alle 253 Offline-Tests bestanden (lokale Testserver außerhalb der Socket-Sandbox); vollständiger Linter und Exportparität bestanden. Initialer Sandboxlauf scheiterte ausschließlich an vier localhost-Bind-Prüfungen.

## 2026-10-13 – Gezielte zusätzliche Linterregeln

- Auf Andreas’ Auftrag zehn Ruff-Regeln ergänzt: B006/B008 (Default-Argumente), B012 (Kontrollfluss in finally), B018/B032 (verlorene Ausdrücke/versehentliche Annotation), B020/B023 (Schleifenbindung), B025 (doppelte Exceptionhandler), RUF006 (Async-Task-Referenzen), RUF100 (veraltete noqa-Ausnahmen). Gepinnte Ruff-Version und read-only Linterablauf erhalten, keine pauschale neue Stilfamilie.
- Zunächst acht Closure-Hinweise in drei vorhandenen Testdateien gefunden; zusätzlich Schleifenbindung in der inzwischen hinzugekommenen JSON-Parsing-Testdatei korrigiert. Testvariante per Default-Argument fest binden; keine neue Ausnahme/Unterdrückung und keine Änderung von Assertions, virtuellen Zeiten oder Produktions-Timeouts.
- README mit Regelumfang/Herstellerreferenzen aktualisiert. Eigenständige Widget-/JSON-Änderungen im gemeinsamen Arbeitsverzeichnis gehören nicht zur Linter-Erweiterung; Runtime-Protokolle durch diese Arbeit unverändert.
- Validierung: alle zehn aktivierten Regeln erkennen ihre synthetischen Fehlerbeispiele mit der tatsächlichen Projektkonfiguration. Vollständiger Linter über 144 öffentliche Dateien, alle 256 Offline-Tests, Compose-Parität mit Overrides und Diff-Prüfung bestanden. Kein Commit/Push/Deployment.

## 2026-10-13 – Doppelte JSON-Prüflogik zusammengeführt

- Auftrag von Andreas: mit risikoarmen Doppelungen beginnen. Gleiche Prüfungen
  auf doppelte JSON-Schlüssel und nicht standardisierte Zahlenkonstanten in
  Konfigurationsloader und HTTP-Dekoder gefunden und nach json_codec.py extrahiert.
  Reine Datenfunktion ohne Datei-/Netzwerkzugriff oder Protokollabhängigkeiten.
- Beide Aufrufer behalten ihre bisherigen Fehlertypen, bereinigten Meldungen und
  unterdrückten Exception-Kontexte. Profil-/Übersetzungs-/Zustandsleser nutzen die
  gemeinsame Prüfung über ihre vorhandenen Aufrufwege. Keine neue Schema- oder
  Zahlenpolitik, kein Zusammenlegen von API-/Portal-Sitzungen, keine Änderung an
  Frische, Topics, Units, Pollingintervallen, TLS oder Schreibfreigaben.
- Drei neue Regressionen prüfen die öffentlichen Aufrufgrenzen: gültige Werte
  einschließlich Null/Unicode/großer Ganzzahlen, gleiche Schlüssel in getrennten
  Objekten, verschachtelte/escaped Duplikate, NaN/Infinity, Syntaxfehler und defektes
  UTF-8. 58 gezielte Tests vor und nach dem Umbau bestanden.
- Vollständige 256 Offline-Tests bestanden; anfänglicher Sandboxlauf scheiterte
  ausschließlich an vier localhost-Bind-Prüfungen, erneuter Lauf mit erlaubten
  lokalen Testservern erfolgreich. Compose-Parität samt Overrides bestanden.
- Vollständiger Linter über 144 öffentliche Dateien einschließlich Formatierung,
  Importordnung, neuer Korrektheitsregeln und Widget-Exportparität bestanden;
  abschließende Diff-Prüfung ebenfalls erfolgreich.
- Weiter offen: weitere konkrete Doppelungen zunächst auf gleiche Semantik prüfen;
  Authentifizierung, Zeitstempel, Wiederverbindung und Befehlsabläufe bleiben eigene
  spätere Schritte. Keine privaten Originale verändert, keine Installationsabfrage,
  Gerätebefehle, Veröffentlichung oder Deployment durchgeführt.

## 2026-10-13 – Release-Rückkehrpunkt vor dem ersten Umbau

- Andreas beauftragt einen neuen Release-Tag vor dem ersten Umbau sowie einen
  Commit nach jedem weiteren Umbau. Direkten Vorgänger e1c9a2d eindeutig geprüft:
  bisherige JSON-Routinen und ursprüngliches Widget vorhanden; gemeinsame
  JSON-Hilfsdatei noch nicht enthalten.
- Annotierten lokalen Tag v0.3.9 auf e1c9a2d gesetzt. Isolierter Git-Quellsnapshot
  besteht 253 Offline-Tests, vollständigen Linter über 140 öffentliche Dateien
  und Compose-Parität einschließlich Overrides. Kein Release-Image oder Live-
  Abnahmestand aus dem Tag abgeleitet.
- JSON-Umbau inzwischen im vorhandenen Commit 73a60bd zusammen mit Widget-
  Vereinfachung und Dokumentation enthalten. Bestehende Historie bleibt erhalten;
  keine nachträgliche Aufteilung, kein Reset oder Force-Push.
- Weitere Umsetzung: ein kleiner Modbus-Metadatenumbau mit eigenem geprüften
  Commit, anschließend Gesamtvergleich und lokaler Docker-/Container-Test.
  Keine Tag-/Commit-Veröffentlichung oder Zielhoständerung beauftragt.

## 2026-10-13 – Modbus-Messwertbeschreibungen zusammengeführt

- Zweiter kleiner Umbau: reine Property-Konstruktion nach profile_property in
  adapters/modbus.py extrahiert. Wechselrichter und delegierte Home-Manager-Werte
  verwenden benannte Argumente für Node, Frische, Format- und Readiness-Auswahl.
- Gefundene Unterschiede bewusst erhalten: Wechselrichter publizieren Formate nur
  für Enums und übernehmen requiredForReady; delegierte Home-Manager-Werte behalten
  ihre bisherigen Formate auch bei anderen Wertemappings und bleiben optional.
  Format-Reihenfolge samt Entfernung gleicher Einträge unverändert.
- Unabhängige Vergleichssnapshots mit 240 Fällen vor/nach Umbau bytegleich:
  sämtliche Property-Felder, MQTT-Discovery, Readiness-Schlüssel, Poller und
  Definitionen. Drei gebündelte Wechselrichterprofile, synthetische Enum-/Bool-/
  String-Mappings, Home-Manager-Zuordnungen samt doppelten/ungültigen Units,
  Gruppenflags, Intervall-Overrides und Frischeuntergrenzen abgedeckt.
- Drei neue Regressionen und 30 gezielte Tests vor/nach Umbau bestanden;
  vollständige 259 Offline-Tests und Compose-Parität mit Overrides erfolgreich.
  Registerdekodierung, Profile, Geräteidentität, Verbindungs-/Pollingabläufe,
  Readiness-Semantik und Schreibfreigaben unverändert. Kein Installationszugriff.
- Vollständiger Linter über 145 öffentliche Dateien und Diff-Prüfung bestanden.
  Eigener lokaler Umbau-Commit; anschließend noch
  abschließender Docker-Build und Container-Tests. Kein Push oder Deployment.

## 2026-10-13 – Zusammenführungsrunde mit Container-Prüfung abgeschlossen

- Eigener lokaler Metadaten-Umbau-Commit bf21423; der zuvor vorhandene JSON-/
  Widget-Commit 73a60bd wurde nicht umgeschrieben. Annotierter Rückkehrtag v0.3.9
  unverändert auf e1c9a2d vor beiden Umbauten. Nachweise/Commit-Regel zuvor in
  eigenem Dokumentationscommit 0e7b43a festgehalten.
- Aus bf21423 mit unverändertem gepinntem Dockerfile lokale ARM64-/AMD64-Images
  gebaut: Version 0.3.9-dev.3+bf214232. ARM64 nativ, AMD64 emuliert. Je Architektur
  alle 259 Offline-Tests im Container erfolgreich, außerdem exakte Versionsprüfung,
  check-config mit null aktivierten Quellen und Image-Ausschlüsse geprüft.
  Kein pip/ensurepip, private Konfiguration oder Git-Metadaten im Image.
- Container ohne externes Netzwerk und mit ausschließlich öffentlichen read-only
  Testmounts. Keine Installationsgeräte, Portalzugänge oder Broker verwendet.
  Lokale Testimages refactor-check-arm64/refactor-check-amd64 bleiben für Prüfung
  verfügbar; keine laufenden Testcontainer zurückgelassen.
- Abschließender Runtime-Diff gegenüber v0.3.9 umfasst nur JSON-/Metadaten-
  Extraktion in fünf Paketdateien. Profile, Runtime-Abhängigkeiten, Dockerfile,
  Compose-Einstellungen und private Daten unverändert. Verhaltensvergleich,
  lokale Tests und Linter bereits erfolgreich; Abschlussnachweise separat committen.
- Runde abgeschlossen. Jeder künftige Umbau bekommt nach Prüfung einen eigenen
  Commit. Größere Authentifizierungs-/Frische-/Schreibumbauten bleiben außerhalb
  dieser Runde. Kein Commit-/Tag-Push, GHCR-Release oder Deployment durch Codex.

## 2026-10-13 – Vollständige Nachprüfung und Heartbeat-Dateizugriffe

- Neuer Auftrag: gesamte Anwendung auf Codequalität, Dokumentation, Stabilität und
  CPU-/HDD-Verbrauch prüfen. Ausgangsstand: 259 Offline-Tests, sämtliche Linter und
  Compose-Parität bestanden. Die akzeptierte 22-Stunden-Messung zeigt stabile
  CPU-/Speichernutzung; HDD-Zähler und Prozessidentitäten fehlen darin.
- Heartbeats bleiben vollständige atomare Dateiersetzungen, erzwingen aber kein
  fsync mehr. Bei Standardintervall 10 s entfallen 17.280 explizite Sync-Aufrufe
  täglich. Keine Behauptung über tatsächliche HDD-Schreibmenge; OS-Dateicache und
  Docker-Logging bleiben eigene Einflussgrößen.
- Dauerhafte Befehlsjournale und Topic-Manifest behalten Datei-/Verzeichnis-Sync.
  Prozess-/Altersprüfung, Intervalle, Schreibsperren und Wiederanlauf unverändert.
- Zwei Regressionen: laufend/gestoppt ohne Sync, Recovery-State mit beiden Syncs;
  fehlgeschlagene Ersetzung erhält vorherige vollständige Datei. Alle 261 Tests,
  vollständiger Linter und Compose-Prüfung samt Overrides erfolgreich.
- Nächster begrenzter Schritt: unveränderliche Metadaten zwischenspeichern,
  Messwert-/Frische-/Rechte-Caches vermeiden und Vergleichsmessung durchführen.

## 2026-10-13 – Metadaten-Caches mit Gegenprüfung

- Property-Index und voreingestellte Readiness-Schlüssel pro Quelle wiederverwenden;
  neue Property-Tupel ersetzen den Cache. Konfigurierbare Frische und aktuelle
  Messwerte bleiben dynamisch. MQTT-Beschreibungen nur bei Inventar-/Flag-/Monitor-
  Änderungen neu konstruieren, einschließlich später Home-Manager-Zuordnungen.
- Drei neue Regressionen prüfen aktuelle Verfallsgrenzen, ungültige Messwerte,
  geänderte Units/Typen/Inventare, Readiness-Overrides und Discovery-Retirement.
  Unabhängiger Vergleich: 168 Fälle mit ursprünglichem SourceState bytegleich.
- Wiederholbarer Offline-Benchmark mit sieben Quellen/150 Properties:
  Status-/Frischepfade ca. 42 % weniger CPU-Zeit (Median 0,436556 s auf 0,251237 s,
  jeweils 2.000 Zyklen, fünf Wiederholungen); Prüfsumme der Ausgaben unverändert.
  Keine Hochrechnung auf gesamte Geräte-/Container-CPU oder tatsächliche HDD-I/O.
- Alle 264 Tests, sämtliche Linter und Compose-Parität erfolgreich. Unabhängig
  hinzugekommene Compose-Kommentare und .env.example bleiben außerhalb dieses
  Commits; keine fremden Änderungen überschrieben.
- Weiterer konkreter Härtungsbefund: kurze numerische Exponentwerte können beim
  MQTT-Payload-Formatieren sehr große Strings erzeugen. Vor einer Freigabe dieses
  Optimierungsstands eine konfigurierbare Ausgabebegrenzung gezielt prüfen.

## 2026-10-13 – Übergrößen beim MQTT-Payload begrenzt

- Vorheriger Befund behoben: neuer positiver Integer SMAB_MAX_PAYLOAD_BYTES,
  Standard 4096 UTF-8-Bytes, JSON runtime.maxPayloadBytes mit normaler Präzedenz.
  Erwartete feste Dezimallänge vor dem Formatieren prüfen, keine riesigen
  Exponent-Strings erzeugen. Ungültige Unicode-Surrogate ebenfalls zurückweisen.
- Neue Grenze für normale und Feedback-Quellen übernommen. Übliche Werte,
  ganzzahlige Homie-Darstellung, Nullwerte, Units und Topic-IDs unverändert.
  Übergrößen sind ungültige Beobachtungen, erfinden keine Null und erneuern keine
  Frische; MQTT erhält die letzte gültige Beobachtung wie bisher.
- Fünf Regressionen inklusive Extremexponenten ohne Formatieraufruf,
  positiven/negativen Längengrenzen, UTF-8-Bytes, Sign-/Nullfällen sowie JSON-/ENV-
  Präzedenz und Adapterübernahme erfolgreich. ENV-Beispiel vollständig nachgeprüft.
- Alle 269 Offline-Tests, sämtliche Linter, Compose-Parität mit Overrides,
  Python-Kompilierung, lokale Dokumentationslinks und Diff-Prüfung bestanden.
  Keine deutschsprachigen Quellkommentare bei ergänzender Sichtung gefunden.
- Separater lokaler Härtungscommit. Container-Gegenprüfung und Abschlussbericht
  folgen; keine Veröffentlichung oder Zielhoständerung.

## 2026-10-13 – Gesamtprüfung und Ressourcenrunde abgeschlossen

- Eigene Umsetzungsschritte separat committed: d570a36 (Heartbeat-Sync), 4da4293
  (Metadaten-Caches), e378535 (Payload-Begrenzung). Unabhängige Änderungen an
  Compose-Kommentaren/.env.example erhalten und nicht in diese Commits aufgenommen.
- Aktueller Quellstand als 0.3.10-dev.3+e378535e mit unveränderten gepinnten
  Abhängigkeiten für ARM64/AMD64 gebaut. Je Architektur alle 269 Tests ohne
  externes Netzwerk bestanden; native ARM64 ca. 7,8 s, emulierte AMD64 ca. 11,2 s.
  Version, deaktivierte Quellen und Image-Ausschlüsse zusätzlich auf ARM64 geprüft.
- Erster Buildversuch mit --network=none konnte die Installationsschicht nicht
  wiederverwenden und scheiterte am Paketdownload. Normaler Build mit vorhandenem
  Cache erfolgreich; beide eigentlichen Container-Testläufe blieben netzwerkisoliert.
- Abschlussbericht: docs/PERFORMANCE_REVIEW_2026-10-13.md. Weitere Ansatzpunkte
  sind Diagnose-/Docker-Logs, separater Healthcheck-Prozess, MQTT-State-Bestätigung
  und identische Manifest-Speicherungen. Erst Kosten isolieren, dann gezielt ändern;
  keine pauschalen Frische-, Rechte- oder Geräteidentitäts-Caches.
- Akzeptierte Ressourcen-/Betriebsprüfung bleibt geschlossen. Keine neue Live-
  CPU-/HDD-Ersparnis behauptet; Migration, Laden und Zeitstempel-Restfragen bleiben
  nach vorhandener Priorisierung offen. Kein Push, Release oder Deployment.

## 2026-10-13 – Ressourcenrecorder für Optimierungsvergleich erweitert

- Andreas beauftragt Erweiterung, Commit und neues Release; Deployment und Start
  der Aufzeichnung übernimmt er. Nächste freie Version nach Remote-Prüfung: v0.3.11.
- Schema 2 erfasst je Blockgerät cgroup-I/O (Bytes/Operationen) und Prozess-I/O
  (logische Bytes, Syscalls, Storage-/stornierte Schreibbytes). Read-only, keine
  zusätzlichen Geräteabfragen, Pakete oder Service-ENV-Einstellungen.
- Änderungsraten nur bei gleichem Containersegment, unveränderten Geräten und
  vollständiger Prozessmenge mit gleicher PID/Startzeit. Resets, Berechtigungs-
  fehler oder fehlende Controller ergeben null statt falscher Einsparungen.
  Prozess-/Containeridentitäten werden ausschließlich intern verwendet.
- Offizielle Kernel-Dokumentation geprüft. Logische Bytes, Dirty-Page-Zähler und
  Block-I/O unterscheiden; daraus keine direkten HDD-Seeks/Verschleißwerte ableiten.
  Docker-Logschreiben und Recorder-Ausgabe liegen außerhalb der Bridge-cgroup.
- Sechs zusätzliche Regressionen bestehen; Python-3.9-Syntax bleibt gültig.
  Vollständige Tests: 275 erfolgreich. Finaler Linter-/Compose-Lauf und Release-
  Prüfung folgen. Alten Recorder separat auf dem Host ersetzen; zweiminütige
  Berechtigungsprüfung vor Nachtlauf, ggf. sudo ohne Service-Rechte zu erweitern.
- Der alte Lauf bleibt akzeptiert. Neuer Lauf ist freiwilliger Optimierungsvergleich;
  CPU-Vergleich zur alten Basis möglich, HDD/I/O erhält erst jetzt eine Basis.

- Finaler Linter über 150 öffentliche Dateien und Compose-Parität erfolgreich;
  zusätzlicher echter Linux-procfs-Test im isolierten ARM64-Container bestanden.
  Keine Zielhost-Aufzeichnung gestartet, keine Service-Rechte verändert.

## 2026-10-13 – v0.3.11 veröffentlicht, Deployment bei Andreas

- Commit 058738e und annotierten Tag v0.3.11 atomar gepusht. Beide lokalen
  Release-Images melden exakt 0.3.11 und bestehen jeweils alle 275 Tests.
- Hosted CI 38454497216 und Release 38454496808 vollständig erfolgreich,
  einschließlich ARM64/AMD64-Containerprüfungen und Trivy-Sicherheitsgates.
- GHCR-Manifest 0.3.11 direkt geprüft: ARM64/AMD64 und Provenance vorhanden;
  Index-Digest in docs/VALIDATION.md. Öffentlicher Recorder exakt taggleich,
  Download-Link und zweiminütiger sudo-/Berechtigungstest dokumentiert.
- Beide veröffentlichten Plattformimages per Digest lokal heruntergeladen und
  ohne externes Containernetzwerk gestartet: jeweils exakt Version 0.3.11.
- Release-Aufgabe erledigt. Andreas deployt und startet die neue Aufzeichnung;
  kein Zielhostzugriff oder Live-CPU-/HDD-Vergleich durch Codex durchgeführt.

## 2026-10-14 – Laufender Vergleich und Berechnungsinventar

- Andreas bestätigt den laufenden Ressourcenrecorder auf dem Zielhost. Letzte
  gelieferte Stichprobe: 14.10. 19:45:04 Europe/Berlin, 21 h 59 min 5 s erfasst,
  running/healthy, Neustartzähler 0, Segment 1. Abschluss voraussichtlich gegen
  21:46 Uhr; vollständige Datei/Log und Gesamtauswertung noch offen. Recorder-
  Dateiname bestätigt nicht die tatsächlich installierte Bridge-Version.
- Wartezeit für Machbarkeitsprüfung der vier gewünschten Berechnungen genutzt:
  vorhandene MainUI-/Migrationsbefunde, Profile und Runtime-Struktur abgeglichen,
  offizielle openHAB-Persistence-Dokumentation konsultiert. Grundmesswerte liegen
  vor; Hausleistung ist der kleinste mögliche zustandslose Schritt.
- Tagesbezug und Haus-Tagesverbrauch integrieren bisher InfluxDB-Zeitreihen;
  Home-Manager-Zählerdifferenzen wären ein Methodenwechsel. Tageseinspeisungs-
  Formel und genaue Bedeutung von Hausgesamtverbrauch fehlen im Bestandsinventar.
  Aktuelle vier Regeln/Abfragen sowie Itemnamen/Units bei Andreas angefragt.
- Tagesgrenzen, Sommerzeit, Neustarts, fehlende Mitternachtsbasis, Ausfälle,
  Zählerwechsel und Frische als Anforderungen festgehalten. Keine Formeln oder
  Nullwerte geraten, keine bestehenden Regeln/Historien ersetzt. Laufender
  Zielhosttest unberührt; keine Runtime-/Deploymentänderung.
- Validierung: vollständiger Linter über 150 öffentliche Dateien und Diff-Prüfung
  bestanden; alle 275 Offline-Tests erfolgreich. Erster Sandboxlauf scheiterte
  ausschließlich an vier gesperrten localhost-Bind-Prüfungen, Wiederholung mit
  erlaubten lokalen Testservern bestanden.
- Präzisierung im Anschluss: Hausgesamtverbrauch ausdrücklich kWh, keine
  momentane Leistung. Alte vier Regeln/Abfragen sind keine Voraussetzung für die
  neue Zählerberechnung; diese Frage ist damit erledigt. Andreas möchte zunächst
  die Rechnung besprechen. Entwurf: Home-Manager-Tagesdifferenzen und Hausbilanz
  aus gemeinsamen PV-/Netz-/Batterie-Zählerdifferenzen. Ungeklärte AC/DC-Messgrenze
  der Batterie und bisher ganzzahlige PV-kWh begrenzen die Hausbilanz; Gesamtwert
  braucht gemeinsamen Startpunkt oder geprüften Anfangsstand. Noch kein Code.

## 2026-10-14 – Aktuelles PV-Inventar und Anlagensummen entworfen

- Andreas beauftragt lesendes Inventar der PV-Items/-Regeln als Grundlage für
  Bridge-Summen und ein späteres Grafana-Alt-/Neu-Dashboard. Zusätzlich aktuelle
  Hausleistung in W angefragt; vier Energieziele bleiben kWh. Zeitzonenfrage
  geklärt: bestehendes SMAB_TIMEZONE wiederverwenden, lokale Kalendertage/DST.
- Nach Zertifikatsblockade im In-App-Browser von Andreas ausdrücklich genannte
  HTTP-Adresse verwendet. MainUI und öffentliche Item-Metadaten lesend erfasst;
  geschützte Regeln/Links ausschließlich in der vorhandenen UI-Sitzung gelesen.
  Keine Zertifikatsprüfung abgeschaltet, keine Regeln ausgeführt/gespeichert.
- 129 bereinigte Inventareinträge: bisheriger PV-Baum mit 51 Einträgen inklusive
  Gruppen, vier neue Geräte-Gruppen mit 70 Homie-Items und vier externe
  Abhängigkeiten. Alle 109 aufgelisteten Regelcodeansichten gelesen, 29 relevante
  Regeln inklusive Forecasts, Smart-Grid, Anwesenheit, Fenster-/Saisonabhängigkeiten
  erfasst. Literalverweise sind kein vollständiger Beweis für dynamische Namen,
  Imports oder externe Skripte; Steuerungs-/Timerabnahme bleibt getrennt.
- Vier aktuelle InfluxDB-Abfragen inventarisiert. Tageseinspeisung ist nun
  eindeutig zugeordnet: Integration der alten Einspeiseleistung, wie Tagesbezug
  und Hausverbrauch 10-s-Mittelwerte ab Berlin-Mitternacht, Aktualisierung 300 s.
  Sieben-Tage-Durchschnitt behält Wallbox-Abhängigkeit; Zeitzonenoption auskommentiert.
- 70 aktuelle Homie-Kanalzuordnungen und 38 konkrete Alt-/Neu-Paare festgehalten;
  acht weitere Vergleichsziele sind vorgeschlagene Anlagensummen, vier Altwerte
  bleiben extern, 32 neue Items ohne eigenen alten Partner. Noch kein Grafana-
  Dashboard, Datenquellen-/Messreihenschema muss vorher geprüft werden.
- Rollen none/pv/battery/hybrid und separates Homie-Gerät sma-plant mit Nodes
  pv/battery/grid/house vorgeschlagen. Fehlende Beiträge nicht als Null, Profile
  mit Units/Messgrenzen prüfen, Hybrid-/Netz-Doppelzählung vermeiden. Alle neuen
  Namen/Flags/Topics bleiben Entwurf, keine Runtime- oder Deploymentänderung.
- Privattarife, Adressen, Zugangsdaten, Messzustände und Rohskripte nicht in
  Inventardateien übernommen. Private Originale, Items, Regeln, Links, Historien
  und laufende Ressourcenmessung unverändert. Validierung folgt.
- Alle 38 alten Direktlinks aktuell geprüft: 34 Modbus und vier SMA-Energy-Meter-
  Binding-Kanäle, weiterhin unabhängige Altquellen. Zuordnung ist kein bereits
  bestandener Werte-/Zeitreihenvergleich.
- Validierung: CSV-Struktur, 129 eindeutige Itemnamen, 70 Linkzuordnungen, 29 Regeln,
  vier Abfragen, Referenzen und alle 38 Paar-Types/Topics konsistent. Zwei
  deaktivierte Regeln getrennt erfasst; Berliner 23-/25-Stunden-Tage rechnerisch
  geprüft. Alle 275 Offline-Tests, vollständiger Linter über 156 öffentliche
  Dateien und abschließende Diff-Prüfung bestanden.

## 2026-10-14 – Ressourcenvergleich nach Update abgeschlossen

- Gelieferte JSONL-Datei unverändert lesend ausgewertet: 1.438 gültige Stichproben,
  13.10. 21:45:59 bis 14.10. 21:45:59 Europe/Berlin, volle 24 Stunden.
  Durchgehend running/healthy, Neustartzähler 0, Segment 1, keine großen Lücken.
- CPU-Mittel 4,300 % eines Kerns gegenüber 4,355 % zuvor: praktisch gleiches
  Niveau, keine kausal nachgewiesene Einsparung. Zweiprozess-RSS-Median 50,344 MiB
  statt 53,250 MiB; erste/letzte Stunde 52,656/50,234 MiB, kein Wachstumstrend.
- Neue I/O-Basis: gültige Prozessraten decken 93,46 % ab, darin etwa 159,25 MiB
  Storage-Schreibbuchhaltung. Cgroup meldet null Schreibbytes; keine tatsächliche
  HDD-Schreibmenge/Ersparnis ableitbar. Alte Messung hatte keine I/O-Zähler.
- Freiwilliger Vergleich erledigt, bestehende Ressourcenabnahme bleibt geschlossen.
  Dateiname ersetzt keine installierte Versionsprüfung. Keine Runtimeänderungen,
  Rohdatenübernahme, Zielhostzugriffe oder Änderung privater Originale.
- Validierung: vollständiger Linter über 162 öffentliche Dateien, 303 Offline-Tests
  und Diff-Prüfung erfolgreich. Vier lokale Testserver benötigen erlaubte
  Loopback-Sockets; Wiederholung außerhalb dieser Sandbox-Beschränkung bestanden.

## 2026-10-14 – Optionale Anlagenberechnung lokal umgesetzt

- Andreas hat die Umsetzung freigegeben. Rollen none/pv/battery/hybrid,
  Profilbeiträge und separates Homie-Gerät sma-plant umgesetzt, standardmäßig aus.
  Die bisherigen Entwurfsfragen zu Topicnamen, Rollen und Speicher sind damit
  entschieden; keine automatische Aktivierung durch Adressen oder Rollen.
- PV-Summen totalactivepower/totaldayyield/totalyield und Batterielade-/Entladesummen
  nur bei mindestens zwei konfigurierten aktiven Beiträgen. Ein Ausfall verkleinert
  keine Summe. Beide bestehenden Hausleistungsrechnungen übernommen; negative,
  fehlende, veraltete oder zeitlich unpassende Beiträge liefern keinen neuen Wert.
- Tagesbezug/-einspeisung und Haus-kWh aus Gesamtzählerdifferenzen mit gemeinsamer
  Basis umgesetzt. Bestehendes SMAB_TIMEZONE berücksichtigt lokale Mitternacht
  und Sommerzeit. energy-balances.json liegt im bestehenden Zustandsvolume;
  atomare Checkpoints, bestätigte Veröffentlichungen, Neustart-/Lücken-/Reset-
  und Gerätewechselprüfungen schützen die Bilanz. Keine zusätzlichen Geräteabfragen.
- Offene Messfrage ausdrücklich ungelöst: Batteriezähler sind nicht als AC bestätigt,
  deshalb bleiben reale Haus-kWh unavailable/unsupported-battery-boundary.
  Synthetische bestätigte AC-Fixtures testen die Software, keine Gerätefreigabe.
  Feinere PV-Zähler bleiben offen; bestehende ganze kWh begrenzen die Genauigkeit.
- 310 Offline-Tests auf dem Host und jeweils im ARM64-/AMD64-Container bestanden,
  darunter 35 neue Anlagen-/Zustandstests. Vollständiger Linter über 162 öffentliche
  Dateien, Compose-Parität mit Overrides, Image-Ausschlüsse, Versionsprüfung und
  Diff-Hygiene erfolgreich. Testcontainer ohne Netzwerk; lokale Version
  0.3.11-dev.1+plant. Keine Veröffentlichung, Aktivierung oder Änderung bestehender
  openHAB-Regeln/Items/Links/Historien. Nächster Schritt: getrennten Build deployen
  und Werte parallel vergleichen; Teil-Tage und Neustart live prüfen.

## 2026-10-14 – Batterie-Historien für AC/DC-Prüfung inventarisiert

- Nach Anmeldung durch Andreas InfluxDB ausschließlich lesend geprüft. Die letzten
  30 Tage enthalten alte und neue Lade-/Entladeleistungen sowie Gesamtertrag,
  aber keine Messreihen der fünf benötigten neuen Vergleichsitems: Leistung,
  Batteriestrom, Batteriespannung, BatterieLadeenergie und BatterieEntladeenergie
  unter dem bestehenden smainv2battery-Präfix. Gezielte Sieben-Tage-Abfrage
  bestätigt vorhandene Leistungs-/Ertragsdaten mit Feld value; kein AC/DC-Nachweis.
- Alle fünf Items haben in openHAB aktuelle Zahlenwerte und zeigen in den
  Itemdetails InfluxDB: 0 / Not persisted. Die bestehende Iteminventur bestätigt
  ausschließlich die Geräte-Gruppe, keine Persistenzgruppe. Keine fehlenden Werte
  als Null oder als Gerätefehler interpretiert; der Bridge-Empfang funktioniert
  zum Prüfzeitpunkt, die notwendige Historie fehlt.
- Bestehende InfluxDB-Richtlinien lesend geprüft: pEveryUpdate speichert everyUpdate
  mit restoreOnStartup; weitere Gruppen haben Änderungs-/Zeitfilter und Cron.
  Offizielle openHAB-Persistenzdokumentation konsultiert. Nächster konkreter
  Schritt: diese fünf Items in eine passende Aufzeichnung aufnehmen und normale
  Lade-/Entladephasen sammeln; danach AC-Integral, Zählerdifferenzen und passende
  DC-Gegenprobe vergleichen. Keine Aufzeichnung, Itemgruppe oder Regel geändert.
- Keine Rohzeitreihen, Messzustände, Adressen oder Zugangsdaten ins Repository
  übernommen. AC/DC-Messgrenze bleibt unbestätigt; Haus-kWh nicht freigegeben.

## 2026-10-14 – Fehlende Anlagenleistung live eingegrenzt

- MQTT Explorer lesend geprüft: neue Anlage verbunden, plantstatus stale,
  PV-Tages-/Gesamterträge gültig; Netz-Tageszähler partial und Haus-kWh wegen
  unbestätigter Batterie-Messgrenze gesperrt. Andreas bestätigt im Startlog alle
  sieben Gerätequellen ready und sämtliche MQTT-Verbindungen connected.
- Einmalige direkte, ausschließlich lesende Registerprüfung mit den drei lokal
  konfigurierten aktivierten Wechselrichtern: beide PV-Wirkleistungen ungültig,
  Batterie-Wirkleistung und Lade-/Entladerichtungen dagegen gültig. Keine zusätzlichen
  Poller aktiviert, keine Einstellungen geschrieben und keine MQTT-Nachricht gesendet.
  Adressen, Identitäten, Zugangsdaten und Messstände nicht gespeichert.
- Ursache der fehlenden aktuellen W damit eingegrenzt: ungültige PV-Beiträge,
  keine fehlende Plant-Aktivierung oder MQTT-Verbindung. Gespeicherte MQTT-Nullen
  beweisen keine aktuelle Gültigkeit. Pauschale Nacht-Null aus Uhrzeit bleibt
  ausgeschlossen; ein bestätigter Zustand für Ersatzwerte wäre separat zu prüfen.
- Diagnose powerinputstatus ergänzt: blockierende logische Quelle/Property und
  Grund, einschließlich ungültig/fehlend, veraltet, Quellfehler, Units, Zeitversatz
  und negativer Hausbilanz. Die Messwert- und Gültigkeitsregeln bleiben erhalten.
  Regressionsfall mit zwei ungültigen PV-Werten nach zuvor gültigen Nullen ergänzt;
  Wiederaufnahme erst nach gültiger Messung. Live-Anzeige dieses neuen Diagnosetopics
  benötigt den aktualisierten Build; noch nicht deployed.

- Validierung des Diagnosezusatzes: 313 Tests auf Host und jeweils im ARM64-/AMD64-
  Container ohne Netzwerk bestanden; vollständiger Linter, Compose-Parität mit
  Overrides und Diff-Hygiene erfolgreich. Lokale Testversion 0.3.11-dev.2+plant.
  Keine automatische Nacht-Null ergänzt; künftige Freigabe über eindeutig belegte
  Gerätezustände bleibt eine offene Mess-/Entscheidungsfrage.

## 2026-10-14 – Tagesverbrauch Wallbox und Haus ohne Wallbox umgesetzt

- Andreas beauftragt beide kWh-Tageswerte. Neue schreibgeschützte Topics unter
  sma-plant: wallbox/dailyconsumption und house/dailyconsumptionwithoutwallbox.
  Aktivierung automatisch innerhalb der eingeschalteten Anlagenberechnung bei
  bereits separat aktivierter lokaler eCharger-API; kein neuer ENV-Schalter und
  keine weiteren Geräteabfragen. SEMP allein hat keinen geeigneten Gesamtzähler.
- Wallbox-Zählerdifferenz aus bestehendem measurements/totalenergy, nicht aus
  Sitzungsenergie. Haus ohne Wallbox mit eigener gemeinsamer Zählerbasis inklusive
  Wallbox-Abzug; keine Subtraktion unabhängig gestarteter Tageswerte. Umfang des
  vorhandenen Wallbox-Zählers bleibt maßgeblich; unbekannten Standby-Verbrauch
  nicht zusätzlich behauptet oder geschätzt.
- Wallbox-Tagesenergie unabhängig von Batterie-Messgrenze; Haus ohne Wallbox bleibt
  ebenso wie Haus-kWh bis zum AC-Nachweis gesperrt. Lokale Tagesgrenzen, DST,
  Teil-Tage, Frische, Zeitversatz, negative Bilanzen, Reset und Neustart abgesichert.
  Nur erfolgreich gespeicherte Checkpoints veröffentlichen; bestehende Netz-/Haus-
  Basen bleiben bei späterer Wallbox-Aktivierung erhalten. Zusätzliche Accounts
  benötigen beim Downgrade auf ältere Builds ein passendes Zustandsbackup.
- Validierte Geräteidentität und tatsächlich ausgewählter primärer/Ersatz-Zähler
  werden nur gehasht weitergegeben; Wechsel von Gerät, Endpunkt oder Zählerkanal
  sperrt betroffene Wallbox-Accounts statt einen Zählersprung als Verbrauch zu zählen.
- 15 neue Offline-Tests, insgesamt 328 erfolgreich auf Host sowie in ARM64-/AMD64-
  Containern ohne Netzwerk. Zusätzlich API-Identitäts-/Kanalzuordnung in bestehenden
  Protokollfixtures geprüft. Vollständiger Linter über 163 öffentliche Dateien,
  Compose-Parität mit Overrides, Vergleichsmatrix (84 Zeilen, zehn neue Ziele) und
  Diff-Hygiene bestanden. Testimages 0.3.11-dev.3+plant; keine Veröffentlichung,
  Aktivierung, Live-Geräteabfrage, openHAB-Änderung oder Migration in diesem Schritt.

## 2026-10-15 – Wallbox-Tageswert direkt am eCharger eingeordnet

- Andreas ordnet den Tagesverbrauch der Wallbox dem eCharger zu. Umsetzung:
  measurements/dailyconsumption sowie Wallbox-Tagesstatus/-Zeitpunkt unter der
  konfigurierten eCharger-Homie-ID; Haus ohne Wallbox bleibt auf der Anlage.
  Vorhandene Aktivierung über Plant und lokale API bleibt bestehen, kein neuer ENV.
- Gemeinsame Zustandsdatei und bisheriger wallbox-Account unverändert weitergenutzt;
  keine neue Tagesbasis oder Energieverschiebung durch den Topicwechsel. Alte
  eigene Anlagen-Wallbox-Topics werden über das vorhandene MQTT-Manifest bereinigt.
  Bei schon angelegten openHAB-Items nur Link ändern, Item/History erhalten.
- Abgeleiteter Tagesstatus verändert die Gerätebereitschaft des eChargers nicht:
  erster Teil-Tag bedeutet keine gestörte Wallbox. Veröffentlichung über vorhandene
  Gerätekennung/MQTT-Verbindung; keine zusätzlichen Geräteabfragen oder Schreibaktionen.
- 331 Offline-Tests auf Host und in ARM64-/AMD64-Containern ohne Netzwerk bestanden;
  18 Wallbox-Tests einschließlich drei neuer Fälle für Gerätezuordnung, Laufzeit-
  Registrierung, Bereitschaft, Topicbereinigung und erhaltene Zählerbasis.
  Vollständiger Linter über 163 Dateien, Compose-Parität mit Overrides, Vergleichs-
  matrix und Diff-Hygiene erfolgreich. Lokale Version 0.3.11-dev.4+plant.
  Offizielle openHAB-Homie-Dokumentation konsultiert. Keine Veröffentlichung,
  Installation oder Live-Änderung an MQTT/openHAB/Historien vorgenommen.

## 2026-10-15 – Vorläufige AC-Annahme für Haus-Energie auf Wunsch erlaubt

- Andreas beauftragt, eine Messgrenze zunächst anzunehmen und die Bestätigung
  offen zu lassen. Gewählt: AC. Neuer boolescher Schalter
  SMAB_PLANT_ASSUME_AC_BATTERY_ENERGY, Standard false; lokale private smab.env
  explizit auf true gesetzt. Zielsystem muss diesen Wert und den neuen Build laden.
- Bei unbestätigter Batterie-Messgrenze werden Haus-Tages-/Gesamtverbrauch und
  Tagesverbrauch ohne Wallbox vorläufig berechnet; MQTT kennzeichnet die Grenze
  als assumed-ac. Profilnachweis bleibt unverified; belegte DC-Zähler werden nicht
  übersteuert. Frische-, Reset-, Bilanz- und Tagesgrenzen-Prüfungen bleiben aktiv.
- Vorhandene Netz-/Wallbox-Basen bleiben erhalten. Neue Haus-Accounts starten bei
  Aktivierung; kein rekonstruierter Verbrauch für den vorherigen Teil-Tag.
- [x] Batterie-AC/DC-Messgrenze anhand AC-Leistung, U×I und Zählerdifferenzen
  prüfen: am 15.10.2026 für beide Zähler dieser Installation AC empirisch sehr gut
  belegt, siehe spätere Auswertung. Bisherige AC-Annahme passt zu den Daten.
- [x] Bestätigte Messgrenze in die Laufzeit-Profildeklaration übernommen. Andreas
  erlaubt anschließend ausdrücklich neue Tagesbasen statt Erhalt der alten Basen.
- [ ] AC-Build auf dem Zielhost laden und die fünf Energie-Basen mit Backup neu
  starten. Grobe PV-Zähler und vollständiger Haus-Tagesvergleich bleiben offen.
- 333 Offline-Tests und vollständiger Linter bestanden. Neue Regressionen prüfen
  Hausenergie mit/ohne Wallbox, erhaltene Netzbasis und Schutz belegter DC-Mappings.
  Keine Zielsystem-Installation, Veröffentlichung oder Änderung vorhandener Historien.

## 2026-10-15 – Berechnungs-Debugmodus und fehlende PV-Leistung untersucht

- Andreas bestätigt den 11-Topic-Abgleich: Werte vorhanden bei PV-Tages-/Gesamtertrag,
  Netz-Tagesbezug/-einspeisung, Haus-Gesamtverbrauch und Wallbox-Tagesverbrauch.
  Kein Zahlenwert bei PV-Gesamtleistung, beiden Haus-Wattwerten und beiden
  Haus-Tagesverbräuchen. Metadaten/Watt-Einheit vorhanden, soweit rückgemeldet.
- Gemeldete Diagnose: beide PV-active-power-Eingänge missing-or-invalid,
  Batterie assumed-ac, beide Haus-Tageskonten partial. Die Haus-Tageswerte warten
  auf ausreichend beobachtete Tagesgrenze; keine rückwirkende Tagesbasis erfinden.
- Neuer expliziter Debugmodus: SMAB_PLANT_DEBUG_ENABLED=false als Standard,
  SMAB_PLANT_DEBUG_INTERVAL_SECONDS=60, zusätzlich SMAB_LOG_LEVEL=DEBUG nötig.
  Periodischer Bericht mit Eingangswerten, Alter/Frische/Quellfehlern, Vorzeichen,
  Ergebnissen/Sperrgründen, Zählerbasen und getrenntem bestätigtem Speicherstand.
  Rohregister nur für vorhandene numerische Anlagenbeiträge und Status/Netzschütz
  beteiligter Wechselrichter, nach Identitätsprüfung und ohne zusätzliche Abfragen.
  Keine Identitäts-/Stringregister, Zugangsdaten, Hosts oder Hardware-Fingerprints.
- Einmaliger lesender Nachweis mit lokal konfigurierten Wechselrichtern:
  PV1/PV3 liefern für 30775 jeweils Wörter [32768, 0], also 0x80000000
  (int32 -2147483648, laut Profil ungültig). Status 30201 jeweils 307/OK;
  Netzschütz 30217 jeweils 16777213/ungültig. Storage-Ladeleistung 0 W,
  Entladeleistung 240 W. Keine MQTT-Veröffentlichung, kein Schreibbefehl.
- [ ] Dokumentierte brauchbare Zustands-/Leistungsquelle für PV-Nachtbetrieb
  untersuchen. OK-Status mit ungültigem Netzschütz-/Leistungswert rechtfertigt
  keine angenommene 0-W-Messung. Bei Produktion Eingänge und Haus-Wattwerte prüfen.
- [ ] Neuen Build/Debug-ENV auf Zielsystem laden, begrenzte Logsequenz sammeln und
  anschließend Debugmodus abschalten. Beide Haus-Tageskonten nach nächster erfasster
  Mitternacht prüfen. Batterie-AC/DC-Prüfung bleibt separat offen.
- 338 Offline-Tests und kompletter Linter bestanden. Fünf neue Tests prüfen
  fehlend versus null, Teil-Tag/Speicherstand, Aus-/INFO-/Intervall-Gates,
  Registerauswahl/Sentinel und unveränderte identitätsgeprüfte Leseabfragen.

## 2026-10-15 – Haus-Gesamtverbrauch als zusätzliches Topic entfernt

- Andreas benötigt house/totalconsumption nicht weiter. Im vorhandenen Inventar
  ist diesem neuen Bridge-Zähler kein konkretes bestehendes openHAB-Item zugeordnet;
  TotalPowerConsumption ist die bestehende Hausleistung in W. Keine erneute
  Live-Inventur behauptet. Frühere Frage nach diesem zusätzlichen kWh-Gesamtwert
  damit durch Scope-Entscheidung erledigt; zehn neue Messwert-Topics verbleiben
  in der aktuellen Einzelbatterie-Anlage.
- Topic/Discovery entfernt. Vorhandener Wert samt Metadaten wird über das
  Topic-Manifest beim neuen Build bereinigt. Haus-Tagesverbrauch und Tagesverbrauch
  ohne Wallbox bleiben bestehen; keine Items oder Historien in openHAB gelöscht.
- Zustandsformat und interne Legacy-Felder bleiben kompatibel. Bisheriger
  Anfangswert-ENV bleibt als veralteter Kompatibilitätswert erhalten; vorhandene
  Einstellung nicht ändern, damit die Fingerprints/Tagesbasen unverändert bleiben.
- 338 Offline-Tests und vollständiger Linter bestanden. Tests prüfen fehlende
  Discovery, Tages-Checkpoint/Alter/Neustart sowie Bereinigung alter MQTT-Topics
  mit unveränderter Zustandsdatei. Offizielle openHAB-Homie-Dokumentation konsultiert.
  Zielsystem-Installation und tatsächliche MQTT-Bereinigung weiterhin ausstehend.

## 2026-10-15 – Teil-Tag-Werte für sofortigen Berechnungstest

- Andreas möchte den ersten Test ohne Warten auf Mitternacht. Neuer boolescher
  Schalter SMAB_PLANT_PUBLISH_PARTIAL_DAY, Standard false. Lokal in der privaten
  smab.env explizit true gesetzt; Zielsystem benötigt neuen Build und denselben ENV.
- Neue Tageskonten halten den ersten gültigen gemeinsamen Zählervektor dauerhaft
  fest und liefern zunächst 0 kWh, danach Differenzen seit dieser Aufnahme.
  Vorhandene partial-Basen bleiben erhalten, auch beim späteren Einschalten und
  nach Neustart. Keine Zustandsdatei löschen, kein Fingerprint-/Schemawechsel.
- Gilt für berechnete Netz-/Haus-/Wallbox-Tageskonten einschließlich Haus ohne
  Wallbox. Direkte PV-Tagesertragssummen behalten ihre Geräte-Tageswerte.
  Status bleibt partial; Testwerte sind keine vollständigen Kalender-Tageswerte.
  Nach ausreichend erfasster Mitternacht automatisch normale Tagesbasis/complete.
- Fehlende Eingänge, Frische/Skew, AC-Messgrenze, Datenlücken, Reset, Zeitfehler,
  negative oder sinkende Bilanzen und dauerhafte Speicherung bleiben abgesichert.
  Abschalten sperrt Teil-Tag-Ergebnisse wieder, ohne Basen oder letzte Retained-
  Beobachtungen zu löschen. DEBUG-Bericht zeigt den aktiven Testschalter.
- 345 Offline-Tests und kompletter Linter bestanden. Sieben neue Fälle decken
  Delta/Neustart, spätere Aktivierung/Deaktivierung, Mitternachtswechsel, Fehler-
  Gates, negative/sinkende Hausbilanz, gemeinsame Wallbox-Abgrenzung sowie
  Speicherfehler/AC-Sperre ab. Zielhost- und echte Mitternachtsabnahme bleiben offen.

## 2026-10-15 – Rückmeldung zu Leistungswerten, Tageswerte weiter offen

- Andreas bestätigt Zahlenwerte für house/consumption und
  house/consumptionwithcharging sowie korrekt angezeigte 0 W für
  pv/totalactivepower. Dies ist eine Anwender-Rückmeldung; keine erneute lokale
  Registerprüfung oder vollständige physikalische Bilanzabnahme daraus ableiten.
- Haus-/Wallbox-Tagesverbrauch und Haus-Tagesverbrauch ohne Wallbox werden als
  weiterhin leer gemeldet. Aktuelle Berechnungs-Debugzeile angefragt, um wirksamen
  Teil-Tag-Schalter, Kontostatus, Eingänge und gespeicherte Tageswerte abzugleichen.
  Keine aktuelle Ursache ohne Laufzeitnachweis behauptet; nicht erneut pauschal
  auf Mitternacht verweisen, falls Teil-Tag-Testmodus tatsächlich aktiv ist.

- Erledigt im Anschluss: Gelieferte Berechnungsdiagnose bestätigt
  publishPartialDay=true, frische Eingänge und berechnete Teil-Tag-Hauswerte.
  Die zuletzt bestätigten Haus-Snapshots hatten noch dailyValue=null;
  checkpointDirty=true bei Checkpoint-Intervall 300 s. Wallbox-Tageswert war
  bereits intern verfügbar. Andreas bestätigt danach, dass die Werte erscheinen.
  Die beobachtete Verzögerung passt zum Warten auf den nächsten dauerhaften
  Checkpoint, kein weiterer Rechenfix erforderlich. Vollständiger Tagesvergleich,
  echte Mitternacht und physikalische Batterie-Messgrenze bleiben offen.

## 2026-10-15 – Batterie-Zähler anhand Lade-/Entladehistorien geprüft

- Nach erneuter Anmeldung durch Andreas InfluxDB ausschließlich lesend ausgewertet.
  Alle fünf zuvor fehlenden Messreihen sind inzwischen vorhanden. Original-
  Zähler-Endpunkte mit AC-Integral und DC-Gegenprobe U×I zeitlich abgeglichen;
  keine Lade-/Entladebefehle oder Änderungen an Persistence/Items/Historien.
- [Ergebnis und Methode](docs/BATTERY_ENERGY_BOUNDARY_2026-10-15.md): Über knapp
  sieben Stunden Entladung 1,711 kWh Zähleränderung, 1,711919 kWh AC,
  näherungsweise 1,929356 kWh DC. Über gut 18 Minuten Laden 0,106 kWh Zähler,
  0,106640 kWh AC, näherungsweise 0,092495 kWh DC. AC-Abweichungen etwa 0,054 %
  und 0,603 %, DC-Abweichungen jeweils rund 13 % in passender Gegenrichtung.
- AC-Integral zusätzlich unabhängig aus Originalzeitstempeln berechnet. DC aus
  5-s-Rekonstruktion mit vorherigen Werten; Spannungsreihe deutlich dünner als
  Strom/AC, Messfenster an Original-Zählerzeiten ausgerichtet. Nicht den älteren
  Zwischenwert eines resampleten Zählers für den Endpunktvergleich verwenden.
- Messgrenzenfrage für diese Installation damit empirisch sehr gut als AC belegt;
  bisherige AC-Annahme passt. Kein Nachweis einer Rundlauf-Effizienz, vollständiger
  Haus-Tagesgenauigkeit oder Übertragbarkeit auf jede Firmware/Modellvariante.
- Laufzeitprofil bleibt in diesem lesenden Schritt unverändert: Deklaration und
  Diagnose weiterhin unverified/assumed-ac. Profiländerung würde aktuell den
  kompletten Anlagen-Fingerprint verändern; spätere Übernahme muss Tagesbasen und
  Zustandsvolume erhalten. Keine Zustandsdatei löschen oder Historie umskalieren.
- Keine Rohzeitreihen, absoluten Zählerstände, privaten Identitäten oder Secrets
  im öffentlichen Nachweis gespeichert. Nur Dokumentation geändert; vollständiger
  Linter und Diff-Hygiene geprüft, kein erneuter Runtime-Testlauf erforderlich.

## 2026-10-15 – AC-Profil und gesicherter Neustart der Energie-Basen vorbereitet

- Auf Andreas' Wunsch zuerst sämtliche offenen öffentlichen Änderungen als
  085e118 committed, einschließlich Ressourcenanalyse und Compose-/ENV-Beispielen.
  Danach war der Arbeitsbaum sauber. Private smab.env/Referenzen ausgeschlossen.
- Andreas erlaubt neue Zählerbasen. Gebündeltes Storage-Profil auf energyBoundary=ac
  mit Messnachweis gesetzt. Diagnose nach Laden des neuen Profils ac, Rechnung
  unverändert zur bisherigen Annahme. Lokalen überflüssigen Annahme-ENV entfernt;
  Teil-Tag-Testschalter und Debug-Konfiguration erhalten. Host-Overrides abgleichen.
- Neuer expliziter Offline-Befehl --reset-energy-baselines: normalen exklusiven
  Prozess-Lock verwenden, gültige energy-balances.json in eindeutiges Backup
  umbenennen und Verzeichnis synchronisieren. Keine Netzwerk-/Gerätezugriffe,
  kein Entfernen des Zustandsvolumes, Topic-Manifests oder Befehlsjournale.
  Fehlende Datei ist ein No-op; gesperrte/ungültige/Symlink-Datei wird abgelehnt.
- Nach diesem Reset starten alle fünf Tageskonten mit aktuellen Erstwerten neu;
  im Teil-Tag-Modus zunächst 0 kWh Differenz und partial. Gerätezähler/PV-Erträge,
  Watt-Werte und vorhandene InfluxDB-Historien bleiben erhalten; heutige neue
  Tageswerte können dadurch einen Sprung nach unten zeigen.
- 350 Offline-Tests auf Host und in ARM64-/AMD64-Testcontainern ohne Netzwerk
  bestanden, außerdem vollständiger Linter und Diff-Hygiene. Fünf neue Fälle
  prüfen Profilwechsel/alle fünf Konten, erhaltene Fremd-/Backup-Dateien, Lock,
  Offline-CLI/No-op, ungültige Zustände und fehlgeschlagenes Umbenennen.
  Öffentliche Testfixtures separat read-only eingebunden, keine privaten Daten.
  Lokale Testimages 0.3.11-dev.5+ac; keine Veröffentlichung.
- Direkte Zielhost-Ausführung nicht erfolgt: SSH-Hostschlüssel für diese Verbindung
  nicht verifiziert; Terminal-App über das verfügbare UI-Werkzeug gesperrt.
  Keine Vertrauensprüfung umgangen. Konkrete Compose-Abfolge zum Prüfen, Sichern
  und Neustarten in docs/CONFIGURATION.md hinterlegt. Pi-Diagnose/Neustart und
  Erscheinen neuer Tageswerte bleiben bis zur dortigen Ausführung offen.

## 2026-10-15 – Alt/Neu-Itemmapping für späteren Kurvenvergleich

- Andreas schließt Wallbox-Items aus dem Vergleich aus; die SMA-Wallbox ist neu.
  Grafana und dessen Voraussetzungen folgen ausdrücklich erst im zweiten Schritt.
- [Lesbare Zuordnung](docs/OPENHAB_ITEM_MAPPING.md) und drei CSV-Ansichten mit
  unveränderten Itemnamen/Labels aus der Inventur vom 14.10. erstellt: 38 Paare,
  acht alte Items mit implementiertem Topic aber fehlendem neuen Itemnamen, zwei
  alte Berechnungen ohne Bridge-Ersatz und 32 ausschließlich neue erfasste Items.
  Zusätzlich ein neues Haus-ohne-Wallbox-Tagestopic ohne erfasste Itemnamen.
- Einspeisevergütung und Sieben-Tage-Durchschnitt bleiben ausdrücklich als alte
  Berechnungen ohne Bridge-Ersatz sichtbar; keine stillschweigende Funktionslücke
  verdeckt. Namenslücke und fehlende Implementierung getrennt gekennzeichnet.
- [x] Die acht tatsächlichen neuen Itemnamen/Labels der Anlagenberechnungen
  am 15.10. live über Itemdetails und Channel-Links bestätigt und ergänzt.
  Zusätzlich Haus-Tagesverbrauch ohne Wallbox erfasst: nun 46 Paare, 33 neue
  Items und zwei alte Berechnungen ohne Bridge-Ersatz. Sonstige neu angelegte
  Items außerhalb dieser gezielten Prüfung bleiben unbestätigt.
- Mengenabgleich: sämtliche erfassten Nicht-Gruppen-Items des PV-/Bridge-Bestands
  abgedeckt; externe Abhängigkeiten und Wallbox-Items bewusst ausgeschlossen.
  Keine Items, Links, Regeln oder Historien verändert.
- Validierung: CSV mit Tabellenwerkzeug eingelesen, Vollständigkeit gegen alle
  erfassten Nicht-Gruppen-Items geprüft; Linter über 171 Dateien und 350 Tests
  erfolgreich. Erster Testlauf durch Sandbox bei vier lokalen Testservern
  blockiert; Wiederholung mit Loopback-Erlaubnis vollständig erfolgreich.

- Ergänzung auf Andreas' Wunsch: [Neun Anlagen-Itemlinks](docs/plant-item-links-2026-10-15.csv)
  ausschließlich lesend aus laufendem openHAB erfasst; keine Zustände oder
  privaten Brokerkennungen gespeichert. Alle acht Namenslücken erledigt.

## 2026-10-15 – Grafana-Vergleichsdashboard vorbereitet

- Andreas beauftragt ein eigenes Dashboard im Ordner Test: ein Panel pro Alt/Neu-
  Vergleich und ausschließlich gemeinsamer Grafana-Zeitbereich oben. 46 Paare
  vorbereitet (39 numerische Zeitreihen, sieben Textzustandsverläufe). Wallbox
  bleibt ausgeschlossen. Fehlende Historien nicht mit Null auffüllen.
- Vorhandene Grafana-InfluxDB-Datenquelle und value-Feld lesend bestätigt.
  Alte inverter1Status-Messreihe liefert keine Felddefinition; neue Zustand-Reihe
  ist String. Keine Persistence-/Item-Änderung oder Historienkorrektur beauftragt.
- Lokale Importdatei unter private/generated/sma-alt-neu-grafana.json; alle
  46 Itempaare und 92 Abfragen gegen Mapping geprüft, keine Panel-Zeitoverrides.
  Zeitfenster-Mittelung für längere Bereiche; kurze Spitzen durch Hineinzoomen
  untersuchen. Aktueller Entwurf ist noch nicht als gespeichertes Dashboard bestätigt.
- Safari-Text-/Dateiimport bleibt im Ladezustand, Editor zeitweise nicht reagierend.
  Separaten Codex-Browser geöffnet; Benutzeranmeldung dort angefragt.
- [x] Nach Anmeldung Dashboard **SMA · Alt und Neu im Vergleich** im bestehenden
  Grafana-Ordner **TESTS** gespeichert (UID sma-alt-neu-vergleich). Gemeinsame
  Auswahl letzte Stunde und letzte 30 Tage geprüft; Alt blau, Neu orange gestrichelt.
  Ausgewählte reale Reihen aus Anlage, Home Manager, Dach, Batterie und Carport
  laden; keine Konsolenfehler im beobachteten Prüflauf. Nicht alle 92 Reihen
  einzeln auf Historienvollständigkeit oder Wertgleichheit abgenommen.
- Safari-Importblockade über angemeldeten Codex-Browser umgangen. Fertiges
  gespeichertes Dashboard anschließend in eigenem Safari-Tab geöffnet.
- [ ] Fehlende alte Statushistorien separat prüfen, bei Bedarf zukünftige
  Historisierung abstimmen. Kein rückwirkender Vergleich ohne gespeicherte Werte.
  Beobachtete Zähler-Offsets und Teil-Tag-Unterschiede im Dashboard erläutert.

- 15.10.2026: Auf Andreas' Wunsch alle 39 numerischen Vergleichspanels auf
  durchgezogene Linien ohne Punktmarker umgestellt, auch Neu nicht mehr gestrichelt.
  Vorhandene Messpunkte über leere Zeitfenster verbunden; Verbindungen sind
  Darstellung, keine zusätzlichen Messungen. Gespeichert und visuell geprüft.

## 2026-10-15 – Vergütung und Sieben-Tage-Durchschnitte

- Andreas bestätigt AC-Build-Deployment samt Profilabgleich, gesichertem Ledger-Reset
  und Versionsprüfung sowie vollständige Tagesabnahme inklusive Mitternacht,
  Neustart und Datenlücken als erledigt. Keine unabhängige neue Liveprüfung.
- Vergütung: gesamter PV-Gesamtertrag je aktivem PV-Wechselrichter × eigener
  ENV-Tarif, Summe ausschließlich unter sma-plant; Währung konfigurierbar, Standard €.
  Eigenverbrauch ist enthalten; eine Tarifänderung bewertet den ganzen Ertrag neu.
- Hausdurchschnitt: sieben abgeschlossene lokale Kalendertage, einmal mit und
  einmal abzüglich Wallbox; Ladetage bleiben enthalten. Fehlende/unvollständige
  Tage sind keine Nulltage. Sieben vollständige Tage müssen zunächst gesammelt werden.
- Kleine optionale Tageshistorie im bestehenden Energie-Ledger, ohne neue Basen
  oder Fingerprints. Ältere Builds benötigen beim Rückrollen eine passende alte
  Ledger-Sicherung, da sie das neue optionale Historienfeld nicht akzeptieren.
- Validierung: 359 Offline-Tests einschließlich neun neuer Statistiktests, voller
  Linter und Compose-Parität samt Overrides bestanden. Lokale Testserver außerhalb
  der Socket-Sandbox; keine Geräte-/Brokerverbindung. Keine neue Installation,
  Veröffentlichung, privaten Tarifwerte oder Änderung an openHAB/Historien.

## 2026-10-15 – Vergütung nur bei ausdrücklichem Tarif

- Auf Andreas' Auftrag Vergütungskanal nur bei mindestens einem expliziten Tarif
  eines aktivierten PV-Beitrags anbieten. ENV und optionales JSON zählen; gesetzte
  Null ist gültig. Nicht konfigurierte Wechselrichter gehen nicht in die Summe ein
  und ihre Messwerte blockieren sie nicht. Batterie-/deaktivierte Quellen aktivieren
  den Kanal nicht. Beim Entfernen aller Tarife bereinigt das vorhandene Manifest
  den alten Retained-Kanal samt Metadaten. Energie-Basen bleiben unverändert.
- Validierung: alle 363 Offline-Tests, vollständiger Linter und Compose-Parität
  einschließlich Overrides bestanden. Vier neue Regressionen prüfen fehlende,
  deaktivierte/Batterie-Tarife, unkonfigurierte Messquellen, JSON-/ENV-Priorität
  mit expliziter Null sowie Retained-Bereinigung ohne Änderung der Energie-Basen.
  Keine Installation, Veröffentlichung oder Änderung privater Tarifwerte.

## 2026-10-15 – Diagnose-Schalter vereinheitlicht

- Auf Andreas' Auftrag sämtliche optionalen Anlagen-Diagnosen unter den
  Plant-Schalter gestellt, einschließlich Tagesabdeckung, Zeitstempel,
  Eingangsprobleme und Durchschnittsabdeckung. Tagesdiagnosen der Wallbox folgen
  unabhängig dem eCharger-Schalter. Quellenstatus bleibt ausdrücklich sichtbar.
- Interne Messwerte/Berechnungen, Frische, Readiness und Energie-Ledger unverändert.
  Debug aktiviert keine MQTT-Kanäle. Bestehende Advanced-/Gerätegruppenfilter bleiben
  erhalten; als Basic eingestufte Werte wie deratingreason bleiben Basic.
- Discovery und Werte verwenden denselben Veröffentlichungsbestand. Vorherige
  optionale Retained-Werte/Metadaten werden über das vorhandene Manifest bereinigt;
  kein neues Zustandsformat, kein Reset und keine Änderung privater Konfiguration.
- Validierung: 368 Offline-Tests einschließlich fünf neuer Diagnose-/Retirement-
  Tests bestanden; vollständiger Linter und Compose-Parität samt Overrides bestanden.
  Keine Geräte-/Brokerverbindung; lokale Fake-Server außerhalb der Socket-Sandbox.
  Live-Installation und Prüfung im MQTT Explorer bleiben offen.

## 2026-10-15 – Topic-Gruppen präzisiert und Katalog erzeugt

- Andreas bestätigt die vorgeschlagene Einteilung. Sechs Abdeckungsstatus der
  Anlage und der Wallbox-Tagesstatus sind jetzt Basic; sie bleiben bei
  abgeschalteter Diagnose sichtbar. Damit ist die vorangegangene Entscheidung
  für diese sieben Statuswerte ausdrücklich verfeinert. Detaillierte Eingänge,
  Zeitpunkte, Datum und Batterie-Messgrenze bleiben Diagnose.
- Home-Manager-Änderungszähler und Anzahl per Grid Guard freigeschalteter Geräte
  von Advanced nach Diagnose verschoben. Beide Kernabfragen folgen dem Diagnose-
  Schalter unabhängig von Advanced; Identitätsprüfung bleibt verpflichtend.
- Alle gebündelten Profilwerte und Laufzeit-Properties ausdrücklich gruppiert;
  bisherige Host-Profile behalten ihre dokumentierten Standardregeln. Neue
  Deklarationen und alle vier Schalterkombinationen werden automatisch geprüft.
- [Generierter Topic-Katalog](docs/topic-catalog.csv) mit 299 Zeilen aus öffentlichen
  Profilen/Laufzeitmetadaten, einschließlich bedingter Ausgaben und alternativer
  Quellen. Keine privaten Konfigurationswerte, keine Geräteabfragen. CI bekommt
  Katalog und Werkzeug nur für Tests eingebunden, nicht im Laufzeit-Image.
- Validierung: alle 372 Offline-Tests, vollständiger Linter und Compose-Parität
  samt Overrides bestanden. Basic-Metadaten/-Werte, unabhängige Schalter und
  Retained-Bereinigung bei unverändertem Energie-Ledger geprüft. Bei den vier
  Profilen ausschließlich Gruppierungsangaben verändert; Mapping/Units unverändert.
- Keine Veröffentlichung, Installation oder Live-SMA-/MQTT-/openHAB-Änderung.
  Die verbleibende Live-Prüfung steht oben; bestehende Energie-Abnahmen bleiben.

## 2026-10-15 – Wallbox-Liveprüfung während des Ladens

- Auf Andreas' Auftrag MQTT Explorer lesend geprüft, ergänzt um zwei lokale
  API-/SEMP-Lesezyklen im Abstand von rund 60 Sekunden. Keine Befehle,
  MQTT-Veröffentlichungen, Konfigurationsänderung oder Aufzeichnungsaktivierung.
- Ladezustand und beide Quellen ready; einphasig L3 mit rund 3,0–3,3 kW.
  Phasensumme passt in beiden direkten Stichproben auf unter 0,01 W zur API-
  Gesamtleistung. Aktuelle Leistungs-/Phasen-/Gesamtenergie-Zeitstempel bestätigt.
- Sitzungsenergie steigt; ihr Zuwachs passt im dreiminütigen MQTT-Vergleich auf
  0,025 Wh zum Gesamtzähler. Zeitfenster um rund zwei Sekunden versetzt, daher
  Plausibilitätsprüfung und keine Kalibrierungsabnahme.
- Health/Event weiterhin rund 34 Tage, Modus/Autorisierung rund 86 Tage alte
  Zeitstempel. Frischefilter beibehalten. Frequenz ohne Messwert; in den API-
  Stichproben nicht enthalten. Kein Fehlerzustand daraus abgeleitet.
- Sitzungsreset, Ruheübergang und physische Zielerreichung nicht beobachtet;
  entsprechende Aufgaben bleiben offen. Frühere MQTT-Historienlücken nicht
  ungeprüft der Wallbox zuschreiben.
- [Befunde und Grenzen](docs/ECHARGER_LIVE_CHECK_2026-10-15.md).

## 2026-10-15 – Wallbox-Frequenz entfernt

- Auf Andreas' Auftrag den mangels Messwert nicht genutzten Wallbox-Frequenzkanal
  aus API-Mapping, Discovery und generiertem Katalog entfernt. Frequenzwerte der
  Wechselrichter unverändert; alter Wallbox-Wert und Metadaten werden nach neuem
  Deployment über das erhaltene Topic-Manifest bereinigt. Kein Energie-Reset nötig.
- Zwei neue Regressionen prüfen die Unterdrückung selbst bei vorhandener
  Quellfrequenz sowie Retained-Bereinigung samt Metadaten. Alle 374 Offline-Tests,
  voller Linter und Diff-Prüfung bestanden; Katalog auf 298 Einträge aktualisiert.
  Migrationszeile als ausdrücklich entfernt markiert, historische Referenz erhalten.
- Keine Live-Änderung an Geräten, MQTT oder openHAB; Installation bleibt offen.

## 2026-10-15 – Einspeisung vergleichen und Vergütung korrigieren

- Andreas stellt klar: Nur tatsächlich eingespeister Strom soll vergütet werden,
  Home Manager bevorzugt. Anschließend einheitlichen Tarif für die gesamte
  Einspeisung ausdrücklich bestätigt; keine Aufteilung nach Wechselrichtern nötig.
- Lesender Vergleich bestätigt identischen Einspeise-Rohzähler bei inv1/inv3,
  gemeinsamen Fortschritt um 1 Wh und denselben kWh-Stand am Home Manager. Eigene
  Wechselrichter-Erträge/-Leistungen sind verschieden. Netzeinspeiseleistung ist W,
  kein Energiezähler; die Netzmessungen dürfen nicht addiert werden.
- Bestehendes Anlagen-Topic pv/totalearnings nutzt jetzt nur den Energieexport
  der gewählten Netzquelle, Standard Home Manager, mal gemeinsamen Tarif. Kein
  automatischer Fallback, keine PV-Ertragsvergütung und keine doppelte Einspeisung.
- Neue ENV-Felder: PLANT_FEED_IN_TARIFF_PER_KWH und
  PLANT_FEED_IN_ENERGY_OFFSET_KWH, jeweils mit SMAB_-Präfix. Expliziter Tarif
  einschließlich Null aktiviert den Kanal, fehlender Tarif blendet ihn aus.
  Optionaler historischer Offset wird einmal vor Multiplikation angewendet;
  Rohzähler, Tagesbasen und Durchschnittshistorie bleiben unverändert.
- Alte Wechselrichtertarife werden zur Konfigurationskompatibilität akzeptiert,
  sind aber wirkungslos. Keine private Tarifübernahme oder Historienkorrektur.
- Validierung: alle 376 Offline-Tests, voller Linter, reproduzierbarer Katalog
  und Compose-Parität samt Overrides bestanden. Geprüft sind gemeinsame Tarif-
  und Offsetrechnung, explizite Null, JSON-/ENV-Vorrang, alte wirkungslose Tarife,
  ungültiger/alter Netzexport, Unabhängigkeit von PV-Verfügbarkeit, fehlende PV-
  Geräte, Retained-Bereinigung und bytegleich erhaltene Energie-Basen.
- [Lesender Quellvergleich](docs/GRID_EXPORT_COMPARISON_2026-10-15.md): keine
  Schreibbefehle, MQTT-Veröffentlichungen, privaten Konfigurationsänderungen oder
  Installation. Neuen Tarif/Offset konfigurieren und Rechnung nach Deployment
  prüfen; bisherige produktionsbasierte Geldhistorie nicht automatisch korrigieren.

## 2026-10-15 – Home-Manager-Leistungsnamen vereinheitlicht

- Andreas wünscht dieselben Begriffe wie bei den Wechselrichtern: powerdrawn
  für Netzbezug und powergridfeedin für Netzeinspeisung, beide W/Basic/read-only.
  Home Manager veröffentlicht die Namen bei UDP und Modbus identisch.
- Nur MQTT-Präsentation geändert; interne Schlüssel, Profile, Register,
  Readiness, Anlagenrechnung, Tarifrechnung und Energie-Basen bleiben unverändert.
  Kein erneuter Basen-Reset und kein Profilabgleich wegen dieser Umbenennung nötig.
- Bisherige Topics powerimport/powerexport werden über das Manifest bereinigt.
  Bestehende openHAB-Items nach Deployment auf die neuen Kanäle umlinken,
  Namen/Units/Regeln/Historien erhalten. Mappings führen neue Zielkanäle mit
  ausdrücklichem Hinweis auf noch nicht erfolgte Live-Änderung.
- Vier neue Regressionen prüfen beide Transporte, IDs/Labels/Units/Readiness,
  Unabhängigkeit anderer Quellen, unveränderte Energie-Basen und echte
  Retained-Bereinigung samt Veröffentlichung der neuen Werte. Alle 380 Offline-
  Tests, voller Linter und Compose-Parität bestanden. Generierter Katalog aktuell;
  beide Migrationsdateien behalten Zeilenzahlen und alle anderen Felder unverändert.
- Keine Profile oder privaten ENV-Werte geändert; kein Deployment und keine
  Live-Änderung an MQTT/openHAB. Umlinken und Live-Prüfung bleiben nach Installation offen.

## 2026-10-15 – Weitere Kanalnamen geprüft

- Auf Andreas' Wunsch den gesamten generierten Katalog geprüft: 298 Zeilen,
  199 unterschiedliche Suffixe; Mehrfacheinträge berücksichtigen alternative
  Transporte/Modelle und sind keine pauschalen Live-Dubletten. Katalog reproduzierbar.
- Klare Kandidaten: voltg1/2/3 → voltagel1/2/3; presbatcharge/presbattdischarge →
  batterychargepower/batterydischargepower; currentbatstatcharge → batterystateofcharge;
  currentbattemp → batterytemperature. Register, Einheiten und Bedeutungen geprüft.
- Weitere Kandidaten: dayyield → dailyyield; Wallbox-Firmware nach identity/firmware;
  batteryefficiency fachlich als Energie-Rückgabegrad benennen; Einspeisevergütung
  künftig unter grid/totalearnings statt pv/totalearnings. Haus-Leistungswerte und
  Nenn-/Grenzleistung eindeutiger benennen; Details und Folgen im Namensaudit.
- currentbatcapacity (%) nicht ungeprüft als kWh-Kapazität oder SOH auslegen.
  PV-Erzeugung, Wallbox-Verbrauch und Netzeinspeisung trotz gleicher kWh-Einheit
  nicht zusammenwerfen. Gerätestatus, Quellenstatus und Tagesabdeckung unterscheiden.
- [Namensaudit und Vorschläge](docs/TOPIC_GROUPS.md#naming-review-2026-10-15--implementation-selected).
  Prüfung zunächst ohne weitere Runtime-Änderungen. Andreas hat die konkreten
  Vorschläge anschließend beauftragt; Umsetzung siehe nachfolgenden Eintrag.

## 2026-10-15 – Energie-Offsets und neue Kanalnamen umgesetzt

- Andreas bestätigt Home Manager energyexport als Vergütungsgrundlage und bestellt
  getrennte Offsets für energyexport/energyimport. Neue ENV-Variablen:
  SMAB_HOME_MANAGER_ENERGY_EXPORT_OFFSET_KWH und
  SMAB_HOME_MANAGER_ENERGY_IMPORT_OFFSET_KWH, Standard 0, endliche signierte kWh.
- Hauptkanäle zeigen Rohzähler plus Offset, eindeutig als korrigiert beschriftet.
  Optionale Diagnosekanäle rawenergyexport/rawenergyimport zeigen Rohstände.
  Fehlende/alte/ungültige Rohwerte bleiben unverfügbar; negative korrigierte
  Gesamtstände werden nicht als Null ausgegeben.
- Vergütung nimmt nur korrigierten Home-Manager-Export, genau einmal mal Tarif.
  Alter Plant-Offset muss 0 bleiben; andernfalls klare Validierungsfehlermeldung
  vor Geräteverbindung. Alte Wechselrichtertarife bleiben wirkungslos.
- Rohbeobachtungen und Tagesdifferenzen bleiben unverändert: kein Fingerprint-
  Wechsel, keine neuen Basen und kein Verlust der Sieben-Tage-Historie.
- Konkrete Namensvorschläge einschließlich Batterie-Rückgabegrad, Firmware,
  Spannungen, Batterie-Werte, Tagesertrag, Nenn-/Grenzleistung, Hausleistung und
  grid/totalearnings als reine MQTT-Zuordnung umgesetzt. Profile unverändert.
  [Vollständige Alt-/Neu-Liste](docs/topic-renames-2026-10-15.csv). Bestehende Items
  nach Deployment umlinken und alte openHAB-Offsets nicht doppelt anwenden.
- Alle 389 Offline-Tests, vollständiger Linter, Compose-Parität und Katalogprüfung
  bestanden. Katalog: 302 Zeilen; Alt-/Neu-Liste: 20 Zuordnungen; Migrationsinventar:
  weiterhin 100 Zeilen. Keine privaten Werte eingetragen, keine Live-Änderung.

## 2026-10-15 – Sieben-Tage-Durchschnitt sofort einschließlich heute

- Andreas ändert die frühere Vorgabe: laufenden heutigen Verbrauch zusammen mit
  verfügbaren Werten der sechs Vortage mitteln. Durch die tatsächliche Anzahl
  verfügbarer Tage teilen, nicht immer durch sieben; keine Hochrechnung.
- Beide Kanäle bleiben ausschließlich unter sma-plant, mit und ohne Wallbox.
  Der Starttag zählt seit Messbeginn, unabhängig vom Schalter für die Anzeige
  partieller Tageskanäle. Ungültige/fehlende Tage nicht als null behandeln.
- Tageswerte, Basen, gespeicherte Historien und Checkpoint-Rhythmus bleiben erhalten.
  Abdeckung: complete bei sieben Tagen, partial bei einem bis sechs Tagen,
  insufficient-history ohne Wert. Live-Abnahme nach Installation bleibt offen.
- Alle 390 Offline-Tests, vollständiger Linter und Compose-Parität bestanden.
  Auf Wunsch als lokales Release v0.6.1 vorbereitet; kein Push oder Deployment.

## 2026-10-15 – Neue Items und InfluxDB-2-Historien vorbereiten

- Andreas meldet 17 verwaiste Links nach Kanalumbenennung und möchte neue Items.
  Alte Items erst nach Historienkopie und Prüfung entfernen. Screenshots inventarisiert:
  docs/influx2-item-migration-2026-10-15.csv; tatsächliche neue Namen fehlen noch.
- InfluxDB 2.x bestätigt. Offline-Generator tools/influx2_copy_item.py erzeugt
  lesende Vorschau oder explizite Flux-Kopierabfrage pro Item-Paar. Originale bleiben;
  Zeitstempel/Felder/Tags erhalten, Measurement und vorhandenes item-Tag umbenennen.
  Leere Quelle, fremdes item-Tag und belegtes Zielintervall verhindern die Kopie.
- 15 Kandidaten für gleiche Bedeutung. Frequenz ohne Nachfolger separat erhalten;
  alte PV-Ertragsvergütung nicht in die neue Einspeisevergütung kopieren.
- Offen: neue Item-Namen, tatsächliche Persistenz-Metadaten, Bucket/Organisation,
  Backup und Stichtag festlegen; Abfragen live prüfen, kopieren und kontrollieren.
  Keine InfluxDB-Verbindung, Kopie oder Item-Löschung durchgeführt.
- Anleitung: docs/INFLUX2_ITEM_MIGRATION.md. Alle 394 Offline-Tests und der
  vollständige Linter bestanden. Keine Live-Flux-Abnahme und kein Deployment.

## 2026-10-15 – Inventar und Grafana nach Kanalwechsel aktualisiert

- Andreas bestätigt Item-Erhalt durch Neuverknüpfung für Tagesertrag/Batterie/
  Hauswerte; pauschale Neuanlage und Historienkopie damit überholt. Lesende
  Live-Inventur: 159 Items im Projektumfang, 18 gezielte Link-/Persistenzprüfungen.
  Neue CSVs vom 15.10.; ursprüngliche Inventur vom 14.10. unverändert erhalten.
- Zehn der 17 gemeldeten Items behalten den Namen und benötigen keine Datenkopie.
  Neun davon live korrekt verknüpft; PVGesamttagesertrag aktuell ohne Link.
  Zwei Home-Manager-Leistungen und drei Carport-Spannungen haben tatsächlich neue
  Itemnamen; alle fünf laut openHAB noch ohne InfluxDB-Historisierung.
- Vergütung des bisherigen PV-Ertrags aktuell ohne Link, kein bestätigtes neues
  Einspeisevergütungsitem. Alte Geldhistorie nicht als Netzeinspeisevergütung nutzen.
  Frequenz bleibt ohne Nachfolger. Beides separat erhalten.
- Durchschnittsitems mit/ohne Wallbox live bestätigt, Einheit kWh/d und Persistence
  everyChange/restoreOnStartup. Grafana-Methodenvergleich erklärt die abweichende
  alte Ladetag-Ausnahme und das neue Fenster einschließlich heute.
- Bestehendes Dashboard SMA · Alt und Neu im Vergleich im Ordner TESTS gesichert
  und aktualisiert: 47 Alt/Neu-Paare plus zusätzliches Durchschnittspanel,
  95 Messreihenabfragen. Home-Manager-Abfragen auf tatsächliche neue Items gestellt;
  durchgezogene Linien ohne Punkte und gemeinsamer Zeitraum bleiben erhalten.
- Neue Panels und Hinweistexte nach Import sichtbar; im geprüften letzten Stunden-
  fenster noch keine Durchschnittsdaten. Vollständige Historien-/Wertabnahme offen.
- Automatische Prüfung blockierte das Verwerfen ungespeicherter Editoränderungen.
  Entwurf blieb offen; Update in separatem Tab durchgeführt, keine Arbeit verworfen.
- Alle 394 Offline-Tests und vollständiger Linter bestanden; Zuordnung sämtlicher
  Dashboardpaare geprüft. Keine Items, Links, Persistence-Regeln oder InfluxDB-
  Historien geändert. Kein Commit oder Push für diese Dokumentationsänderung.

## 2026-10-15 – Historisierung bestätigt, neues Vergütungsitem ergänzt

- Alle fünf neuen Home-Manager-/Carport-Items nach Andreas' Ergänzung live geprüft:
  InfluxDB everyChange/restoreOnStartup jetzt aktiv. Frühere offene Konfiguration
  damit erledigt; gespeicherte Historien und eventuelle Alt-Datenkopie separat prüfen.
- Neues smaplant_Einspeisevergutung_gesamt mit grid#totalearnings, EUR und
  Persistence bestätigt. Bisherige PV-Ertragsvergütung bleibt separat erhalten.
  Inventar: 160 Items, 20 gezielte Kanalprüfungen, 48 Alt/Neu-Paare.
- Weiter offen: smaplant_PVGesamtertrag ist zugleich mit totalyield und
  totaldailyyield verbunden; smaplant_PVGesamttagesertrag bleibt ohne Link.
  Andreas hat Korrektur freigegeben. Safari-Linkdialog reagierte nicht auf
  Itemauswahl, kein Speichern erfolgt; Andreas hängt den Tageskanal selbst um
  und meldet sich. Vor Abschluss beide Links erneut prüfen. Eventuelle Mischwerte
  in der bisherigen Gesamtertrags-Historie nicht automatisch ändern oder löschen.
- Grafana-Ergänzung vorbereitet: fehlende Historisierung nicht mehr als offen
  melden, neues Einspeisevergütungsitem vergleichen, PV-Linkkonflikt kennzeichnen.
  Originale Historien und alte Itemnamen bleiben erhalten.

- Erledigt: Andreas hat den PV-Tageskanal umgehängt. Beide Items live erneut
  geprüft: Gesamtertrag nur totalyield, Tagesertrag nur totaldailyyield; beide
  weiterhin mit everyChange/restoreOnStartup. Inventar und Zuordnung aktualisiert.
- Grafana-Folgemodell mit 48 Paaren vorbereitet; noch nicht gespeichert, weil die
  Ordnerauswahl im Import nicht reagiert. Bisheriges Dashboard bleibt erhalten.
- 394 Offline-Tests und Linter bestanden. Keine InfluxDB-Historien kopiert,
  repariert oder gelöscht; mögliche frühere Mischwerte separat prüfen.

- Erledigt nach Grafana-Neustart: Aktualisierung im bestehenden Ordner TESTS
  gespeichert. Import direkt aus dem Ordner umgeht die hängende Ordnerauswahl.
  48 Paare, neues Vergütungspanel und korrigierte PV-Hinweise live sichtbar;
  bisheriger Hinweis „noch nicht gespeichert“ damit erledigt. Historien unverändert.

## 2026-10-15 – InfluxDB-Historien kopiert, Nachprüfung offen

- Aktuelles Backup von Andreas bestätigt; Ort und Wiederherstellung nicht geprüft.
- Drei befüllte Alt-Historien vor 18:00 Uhr Ortszeit kopiert: Netzbezug 85.724,
  Einspeiseleistung 106.641, Carport L3 13.187 Messwerte. Summe 205.552.
  L1/L2 enthalten keine Quelldaten und wurden übersprungen.
- Flux-Generator nach Live-Typfehler und fehlerhafter Konstantprojektion korrigiert.
  Erfolgreiche Kopierantworten gesichert; Originale und Items nicht gelöscht.
- [ ] Unabhängige Zähl-/Wertprüfung nach Entlastung der Abfragewarteschlange
  abschließen; bisher meldet InfluxDB „queue length exceeded“. Keine Kopie blind
  wiederholen. Siehe [Ablaufnachweis](docs/INFLUX2_ITEM_MIGRATION.md).
- 394 Tests und Linter bestanden. Keine Veröffentlichung oder Commit durchgeführt.

## 2026-10-15 – PV-Nachtbetrieb und Hausleistung

- Live im MQTT Explorer: sma-plant alert, plantstatus stale; Hausleistung retained
  308 W mit letzter Veröffentlichung 20:20:45. Tagesstatus configuration-changed
  und Durchschnitt insufficient-history sind separate Befunde.
- Ursache abgeglichen: alte openHAB-Leistungsregister verwenden smalimit.js;
  Andreas hat die Transformation geliefert (negative Werte werden null). SMA-
  Leistungs-Sentinel -2147483648 wurde bisher in der Bridge verworfen.
- Bundled PV-Profile behandeln genau diesen frisch gelesenen Sentinel nun explizit
  als 0 W. Status 307 bedeutet OK, keine belastbare Standby-Erkennung. Andere
  negative Werte bleiben erhalten; Fehler, Identitätsprüfung und Frische gelten weiter.
- [ ] Nach Deployment verwendete Host-Profilkopien abgleichen (invalidAsZero am
  PV-Leistungsregister), Nacht-Hausleistung und ready live prüfen. Kein Deployment
  oder Commit in diesem Schritt. Tagesstatus configuration-changed separat prüfen.
- Prüfung: 396 Offline-Tests und vollständiger Linter bestanden; Live-Abnahme offen.

## 2026-10-15 – Weitere Ungültigwert-Fälle geprüft

- [Prüfbericht](docs/INVALID_VALUE_AUDIT.md): weitere Unterschiede zu openHAB bei
  DC-Leistung/Strom/Spannung und Wechselrichter-Netzleistungen. Aktuelle Hausleistung
  verwendet diese Zusatzkanäle nicht; Wechselrichter-Netzquelle wäre gesondert betroffen.
- Batterie-, Ertrags- und Energiezähler nicht pauschal nullen. Temperaturen dürfen
  gültig negativ sein. Retained Zahlen allein beweisen keine aktuelle Messung.
- Seiteneffekt des Nachtfixes behoben: invalidAsZero wird als reine Leistungsoption
  nicht in die Energie-Ledger-Signatur aufgenommen. Bisherige Basen und Historien
  bleiben bei ansonsten gleichem Profil erhalten. Persistierter Regressionstest
  bestätigt dies; 397 Tests und vollständiger Linter bestanden.
- [ ] Weitere bisher auf null transformierte Kanäle einzeln abnehmen; noch keine
  pauschale Änderung. Bereits vorhandenes configuration-changed separat klären.

- Ergänzte sma*-Transformationsliste mit privatem Bestand abgeglichen: Skalierungen,
  negative→0/UNDEF, Status-MAPs und Netzenergie-Offsets enthalten. Private Konstanten
  nicht übernommen. Offsets bei Bridge-Items genau einmal anwenden.
- [ ] Aktive Item-/Channel-Verwendung von sma_undef.js (0→UNDEF) feststellen;
  bestehende Things und Mapping belegen diese Zuordnung noch nicht. Status-MAP-
  Eintrag allein beweist keinen gepollten Betriebsstatus.

- Aktuellen Things-Export abgeglichen: 41 aktive Daten-Things stimmen nach
  Leerraum-Normalisierung mit den bisherigen Deklarationen überein. 17 Kanäle
  verwenden negative→0-Transformationen; zwei PV-Gesamtleistungen sind im Nachtfix
  behandelt, 15 Zusatzkanäle bleiben einzeln zu bewerten. Kein Nachweis von 15 Fehlern.
- sma_undef.js und Netzenergie-Offsetskripte sind hier nicht eingebunden. Offene
  Item-Link-/Regelprüfung bleibt erforderlich. Batterieleistungen ohne readTransform;
  kein PV-Betriebsstatusregister 30203 deklariert.

- Item-Link-Frage geklärt: Andreas bestätigt keine zusätzlichen Transformationen
  an den Links. Dortige Prüfung abgeschlossen. sma_undef.js und Netzoffsetskripte
  sind weder im aktuellen Things-Export noch an diesen Links eingebunden; bloße
  Dateipräsenz belegt keine aktive Nutzung. Regelverwendung weiterhin nicht belegt.

## 2026-10-15 – CI-Testcontainer: Migrationsinventar bereitstellen

- CI-Fehler nach c1f6062 geklärt: Inventartest benötigt die Migrations-CSV, aber
  der Testcontainer mountete bislang nur den Topic-Katalog aus docs.
- Fehlende CSV im CI-Testlauf explizit read-only eingebunden. Runtime-Image und
  Docker-Build-Kontext bleiben auf Laufzeitdateien beschränkt. Test nicht übersprungen.
- Plattformübergreifender Docker-CI-Lauf muss nach Veröffentlichung erneut bestehen.
