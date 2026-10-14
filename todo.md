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

- [ ] Veröffentlichtes **v0.3.11** durch Andreas deployen und den separat kopierten
  Recorder nach kurzem Berechtigungstest für den freiwilligen Nachtvergleich starten.
  Veröffentlichung/CI/Sicherheitsgates/ARM64/AMD64 sind abgeschlossen; daraus keine
  Zielhost-Version oder bereits laufende Aufzeichnung ableiten.
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
