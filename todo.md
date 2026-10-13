# TODO

Stand: **13.10.2026**. Diese Liste enthält nur verbleibende Aufgaben und offene
Fragen. Abnahmen und Nachweise stehen in [docs/VALIDATION.md](docs/VALIDATION.md),
die Reihenfolge im [Implementierungsplan](docs/IMPLEMENTATION_PLAN.md).

Die bisherigen Tagesberichte und erledigten Aufgaben bleiben im
[Snapshot vom 13.10.2026](docs/archive/2026-10-13/todo.md) erhalten. Frühere
Entscheidungen und die ursprünglichen Fragen Q01–Q27 stehen auch im
[Archiv vom 11.10.2026](docs/archive/2026-10-11/todo.md). Historische Aussagen
wie „noch offen“ beschreiben den damaligen Stand, nicht die aktuelle Aufgabenliste.

## Nächste Schritte

- [ ] Lokalen Tag **v0.3.8** bei ausdrücklichem Veröffentlichungsauftrag pushen,
  Hosted CI/Sicherheitsprüfungen und GHCR-Publikation prüfen, anschließend deployen.
  Enthält Energierückgabegrad, Derating als Basic und ISO-Anlagenzeit. Der Zielhost
  läuft auf v0.3.7; noch kein Push-/Deploymentauftrag für v0.3.8.
- [ ] Vor diesem Deployment verwendete Host-Profilkopien mit den gebündelten
  Änderungen abgleichen (M01–M04/M09 und neue Gruppierungen), Zustandsvolume und
  bestehende Links/Historien erhalten. Nur tatsächlich genutzte Overrides ändern.
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
  (E01). Passende Number:Power-Items mit W; bestehenden Gesamtzähler erhalten.
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
