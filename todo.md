# TODO

Die aktuelle Abnahme steht in [docs/VALIDATION.md](docs/VALIDATION.md), die Reihenfolge kommender Meilensteine in [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md). Hier stehen aktive Aufgaben, offene Fragen und neue Tagebucheinträge. Die vollständigen bisherigen Einträge einschließlich des Codereviews bleiben im [Tagebucharchiv vom 11.10.2026](docs/archive/2026-10-11/todo.md) erhalten; frühere Aussagen sind zeitlich einzuordnen.

## Aktive Aufgaben

- [ ] Release-Dokumentation aktualisieren: Änderungen und Upgrade-Hinweise zusammenstellen; README vom Vorbereitungsstand auf die tatsächlich verfügbare GHCR-Veröffentlichung umstellen. Produktionsbetrieb mit veröffentlichtem Image und Beispiel-Compose laut Andreas bereits vorhanden; keine erneute Veröffentlichung dafür erforderlich.

- [ ] Watchtower und Autoheal auf dem Zielhost einrichten: automatische Container-Updates und Neustarts bei Docker-unhealthy konfigurieren und prüfen. Persistente Zustandsdaten erhalten und Wiederanlauf ohne Befehlswiederholung sicherstellen.
- [ ] Review 4 beheben: tatsächliches Messwertalter nach vorheriger Zeitstempelklassifikation. Nachweise und Fundstellen im [archivierten Review](docs/archive/2026-10-11/todo.md#2026-10-11--repository--und-codereview); Umsetzungsschritte im Plan. Bestehende Unsicherheitssperren und retained Beobachtungen erhalten.
- [x] Review 5 am 11.10.2026 offline korrigiert: bereits abgeschlossene/späte MQTT-Disconnect-Futures abgeholt, primäre Fehler erhalten und eigenständige Disconnect-Fehler weitergegeben. Unerwartete Event-Loop-Ausnahmen lassen den vollständigen Testlauf scheitern; Ausfallzähler und Wiederverbindung weiterhin geprüft.
- [ ] Review 4 vor Umsetzung neu bewerten: erste Referenz-/Codeprüfung und drei Basistests am 11.10.2026 abgeschlossen. Zeitstempel pro Kanal und API/SEMP durch lesende Beobachtung bei unverändertem Wert und natürlichem Zustandswechsel klassifizieren; danach gezielte Umbau-Regressionsfälle und UI-Abnahme nach [Prüfmatrix](docs/VALIDATION.md#measurement-freshness-investigation-2026-10-11). Kein pauschales Ablaufverhalten für Zähler/Zustände beschließen.
- [x] Zeitstempeldiagnose auf dem Zielhost aktiviert: Andreas bestätigt die Aktivierung am 11.10.2026. Dateiinhalte sowie Ruhe-/Ladephasen und natürliche Übergänge noch auswerten.
- [ ] Zeitstempelaufzeichnung später gemeinsam mit Andreas auswerten: nach ausreichenden Beobachtungen in Ruhe-/Ladephasen und natürlichen Zustandswechseln echarger-timestamps.jsonl.1 und echarger-timestamps.jsonl aus dem Zustandsvolume in dieser Reihenfolge prüfen. Für jeden Kanal und API/SEMP getrennt klären, ob der Zeitstempel Erfassung oder letzte Änderung beschreibt; mehrdeutige Fälle offenlassen. Danach Nutzen/Risiko des Frischeumbaus neu bewerten und die gezielten Vorher-/Nachher-Tests festlegen. Termin noch offen; kein automatischer Umbau oder Löschen der Aufzeichnungen.
- [x] Review 3 am 11.10.2026 lokal korrigiert: obligatorisches Homie-Node-$type ergänzt, sprachunabhängig und stabil; delegierte Geräte teilen den Typ device. Veröffentlichung, dynamisches Retirement und Manifestbesitz offline geprüft; Andreas bestätigt am 11.10.2026 das vorhandene $type am Broker.
- [x] Review 2 am 11.10.2026 lokal korrigiert: Homie-Integer kanonisch ohne Dezimalpunkt ausgegeben, signed-64-bit-Grenzen geprüft; Bruchzahlen werden nicht gerundet. Float-Ausgabe unverändert, Leistungsgrenzen-Regression korrigiert.
- [x] Review 1 am 11.10.2026 lokal korrigiert: individuelle API-Bestätigung und Plan-Einheiten einschließlich Rücklesen abgesichert; SEMP und retained Beobachtungen erhalten. Einstellungsrücklesen und erneute Ladeplanübertragung von Andreas am 11.10.2026 erfolgreich geprüft; Pending-/Fehlereinheitenfälle bleiben offline belegt.
- [x] Review 6 am 11.10.2026 abgeschlossen: statischer CLI-Projektstatus nennt optionale Schreibfähigkeit und standardmäßig geschlossene Befehlsfreigaben; check-config bewertet tatsächliche Gates. Modulbeschreibungen für optionales Schreiben/lokales Datei-I/O präzisiert; Profilbefehle weiterhin nur für Wechselrichter gesperrt.
- [x] Clean Code/KISS Schritte 1–2 am 11.10.2026 umgesetzt: Python-Formatierung und Importordnung getrennt angewendet/geprüft, anschließend verbindlich im Linter verankert. Keine Funktionszerlegung, Setting-Migration oder Widgetänderung; weitere Vereinfachungen bleiben im Plan.
- [x] Clean Code/KISS Schritt 3 am 11.10.2026 umgesetzt: Setting-Positions-Tupel durch benannte unveränderliche Definitionen ersetzt, auch die Befehls-Allowlist verwendet diese Definitionen. Gegencheck mit vorherigem Stand identisch; keine zusätzlichen Setter oder Protokolländerungen.
- [ ] Nachtbetrieb vollständig abnehmen: Morgen-Aufwachen und Wertaktualisierung sowie Schlaf-/Ausfallunterscheidung prüfen. Abendbeobachtung am 11.10.2026 laut Andreas unauffällig.
- [ ] Mehrstündigen deterministischen Ausfalltest und Produktionsabnahme ergänzen: langsame/unvollständige Antworten, Geräte-/Broker-Ausfälle, abruptes Prozessende, Last Will, TLS, Topic-Retirement und selbstständige Erholung. Kontrollierter Stop/Start ist separat bestätigt.
- [x] Externe Überwachung und Alarmierung eingerichtet: von Andreas am 11.10.2026 bestätigt.
- [ ] Host-Neustart und Zustandswiederherstellung prüfen. Manifest, Unklarheitsjournale und Instanzsperre erhalten.
- [x] Quellenstatus bei deaktivierter optionaler Diagnose am 11.10.2026 von Andreas abgenommen: Das Widget erhält weiterhin die Verfügbarkeitswerte. Home-Manager-Startstatus und Startübersicht mit allen Quellen ready/MQTT verbunden sind ebenfalls bestätigt.
- [x] Wallbox-Gesamtladeenergie in kWh am 11.10.2026 von Andreas abgenommen: openHAB-Einheit, Skalierung und bestehende Historie erfolgreich geprüft.
- [ ] Bei Home-Manager-Modbus beide Compose-Dateien auf normales Docker-Bridge-Netzwerk umstellen und Zielhost-Verbindungen einschließlich DNS/TLS prüfen. UDP-Multicast als Alternative mit eigenen Voraussetzungen erhalten; Compose-Parität prüfen. Bis dahin Netzwerk unverändert.
- [ ] openHAB-Migration und Historien vollständig abnehmen; sämtliche 100 Ledgerzeilen, sieben noch nicht zugeordnete Itemlinks, Maps, Vorzeichen, private Offsets, Regeln, UI und Tages-/Sommerzeitgrenzen erhalten. Keine Fähigkeiten stillschweigend streichen.
- [ ] Grafana-Dashboards für den Parallelvergleich alter openHAB- und neuer Bridge-Zeitreihen erstellen: gleiche Einheiten und abgestimmte Messzeitpunkte, Abweichungen und Lücken sichtbar machen.
- [ ] Ladeziel-/Sitzungsenergie-Semantik, physische Zielerreichung und Rückwechsel prüfen. Die gemeldete 10-kWh-Planübertragung und Modusaktivierung sind keine vollständige Ladeabnahme.
- [ ] Maximale Ladeleistung physisch abnehmen und einphasiges Winterladen untersuchen. Mindeststrom-Setter nur nach eigenen Metadaten-/Einheitenbelegen ergänzen; 4 kW sind laut geprüftem Limit unzulässig, 4,5 kW plus 10 A bleibt unbestätigter Versuchskandidat. Live-Versuche nur mit ausdrücklich angeforderten Zielwerten; Home Manager bleibt Regler. [Nachweise und offene Phasenfragen](docs/ECHARGER_POWER_LIMIT.md).
- [ ] Zusätzliche Profile/Portalwerte und aktuellen Lademix nur mit bestätigten Messwerten, Einheiten, Zeitbezug und Identität ergänzen. Tagesanteile und Mindest-PV-Präferenz nicht als aktuellen Lademix veröffentlichen.
- [ ] Kleine Diagnose-/Frischeverbesserungen und ausdrückliches Portal-Leseauffrischen ohne Neustart bewerten; anschließend gezielte Funktionsvereinfachung und zusätzliche Linterregeln. Keine allgemeine Adapterplattform bauen.
- [ ] Später lhlab.wiki-Artikel aus [openHAB/openHAB.md](openHAB/openHAB.md) erstellen. Beispiel-Item-Dateien und Sitemaps bleiben auf Andreas’ Wunsch aus dem Umfang gestrichen.
- [ ] Öffentlichen Stand später nach [GitHub](https://github.com/alaub81/sma-mqtt-bridge) hochladen und GHCR-Release vorbereiten. Private Daten ausschließen, neue Release-/CI-Verknüpfung und GHCR-Installation prüfen; bestehende GitHub-CI einschließlich beider Architekturen und Sicherheitsprüfungen laut Andreas mehrfach erfolgreich; Veröffentlichung ist durch diesen Cleanup nicht beauftragt.

## Offene Fragen und geklärte Teile

Die ursprünglichen Fragen Q01–Q27 bleiben mit ihrem genauen Wortlaut und allen späteren Antworten im Archiv erhalten. Die folgende Zuordnung aktualisiert ihren Arbeitsstand, ohne offene Restfragen aus der Historie zu verlieren.

- [ ] Q02, Q15–Q19, Q27 — Vollständige Item-/Link-/Metadaten-/Regel-/UI-/Persistence-Kontinuität und Parallelvergleich. 34 Wechselrichter-Itemlinks, vier Home-Manager-Items und zehn abgeleitete Fähigkeiten sind inventarisiert; sieben weitere Itemlinks und vollständiger Audit bleiben offen.
- [ ] Q04, Q05, Q10, Q26, Q27 — Zielhost-OS, Docker/Compose, Netzwerk/VLAN, TLS-Vertrauen, Mountrechte und jeweils ausgewählter Home-Manager-Datenweg abnehmen. Modell/Firmware und direktes Modbus-Lesen sind bestätigt; daraus keine UDP-/Pi-Abnahme ableiten. Lokale API-Identität, Zeitfeld und geprüfte kWh/min-Units sind am Mac geklärt; vollständige Zeitstempelsemantik und Zielhostprüfung bleiben offen.
- [ ] Q06, Q19 — Zusätzliche modellgenaue Register/Profile nach Eingang und eigener Prüfung ergänzen. Dateierweiterbarkeit ist implementiert; ursprüngliche 41 Channels sind freigegeben. Ungeprüfte zusätzliche Listen gelten nicht als Unterstützung.
- [ ] Q07, Q21 — Herstellergrenzen für kurze 3-/5-s-Poller, Timeout, Blockgrößen und Verbindungen prüfen; aktuelle Intervalle nicht stillschweigend ändern. Vorgeschlagene beziehungsweise vorhandene Defaults ersetzen keine Zielhost-Abnahme.
- [ ] Q08 — Vorhandene Frische-/Timeout-/Health-Defaults unter Ausfallbedingungen abnehmen und betriebliche Alarmgrenzen festlegen. Prozessgesundheit und Geräte-/Brokerverfügbarkeit bleiben getrennt.
- [ ] Q09 — Verbleibende Topic-/Channel-Metadaten und Brokerrechte abnehmen. Wechselrichter-Umbenennung und Linkmigration laut Andreas am 11.10.2026 erledigt; übrige Kontinuität bleibt Teil der Migration.
- [ ] Q12, Q14 — Physische Ladeplan-/Sitzungssemantik und History-/Offset-/Vorzeichenkontinuität prüfen. Verifizierte kWh/min-Units und Offline-Bounds sind geklärt; eine bestätigte Schreibvorgabe beweist keine physische Zielerreichung.
- [ ] Q22 — Weitere Portal-Kandidaten lesend anhand echter API-Felder, Nullable-/Enum-Verhalten, Einheiten und Zeiträumen verifizieren. Keine zusätzlichen Setter daraus ableiten.
- [x] Q01 — Fünf ursprüngliche Transformationsskripte am 10.10.2026 eingegangen und geprüft; verbleibende semantische Abnahme unter Q14.
- [x] Q03, Q20 — Modell-/Firmware-/Hostidentität und Grundfreigabe der ursprünglichen 41 Channels am 10.10.2026 geklärt. Vollständiger Wertevergleich und zusätzliche Register bleiben eigenständige Aufgaben.
- [x] Q11 — Separate lokale/Portal-Zugangsvoraussetzungen und erste authentifizierte Lesetests am 10.10.2026 geklärt. Keine privaten Werte ins öffentliche Tagebuch übernehmen.
- [x] Q13 — Lesender erster Meilenstein und anschließend ausdrücklich freigegebene Wallbox-/PV-Befehle sind umgesetzt. Live-Schreibtests brauchen weiterhin eine konkrete Aufforderung; Home Manager bleibt Laderegler.
- [x] Q23–Q25 — SMAB_-Präfix, Ablage, typisierter Loader und dateibasierte Profilwahl am 10.10.2026 umgesetzt. Identitätsdeskriptoren ohne validierte Register bleiben für Polling gesperrt.

## Regeln für das Projekttagebuch

Neue Entscheidungen, Unterlagen, Ergebnisse und offene Fragen mit Datum ergänzen. Geklärte Fragen ausdrücklich mit Antwort und Datum markieren. Frühere Einträge bleiben in verlinkten, datierten Archiven erhalten; sie werden nicht nachträglich als aktuelle Anleitung umgeschrieben. Öffentliche technische Dokumente sind Englisch, Tagebucheinträge Deutsch. Private Kennungen, Adressen, Zugangsdaten und Rohantworten bleiben ausgeschlossen.

## 2026-10-11 – Benannte Setting-Definitionen und Gegencheck

- Auftrag: Format-/Importänderungen zuerst committen, danach Schritt 3 umsetzen und abschließend gegenprüfen. Lokaler Commit 6b8ae03 (style: enforce Python formatting and import ordering). Kein Push oder Deployment.
- Kleine frozen/keyword-only SettingDefinition mit id, channel, datatype, unit, mapping und format eingeführt. Einstellungen ausschließlich mit benannten Argumenten definiert; Bool-Mappings kopiert und über MappingProxyType gegen Änderung abgesichert. Keine allgemeine Metadaten-/Adapterplattform eingeführt.
- API-/SEMP-Property-Erstellung und settings_values auf benannte Felder umgestellt. LOCAL_COMMANDS hält dieselben Definitionen statt abgeleiteter Positions-Tupel; bisherige Schlüssel und Ausschlüsse für plan-energy, plan-end und stop-delay beibehalten. Bestätigung, Einheiten, Limits, kombinierter Ladeplan und Unklarheitsschutz unverändert.
- Vor Umbau unabhängigen Vergleichssnapshot aus dem alten Code erstellt: zwölf API-/elf SEMP-Definitionen, neun Befehls-Schlüssel, acht Readvarianten für Quelle/Confirmed/Pending/Units, Properties und gesamte Homie-Discovery bei vier API-/SEMP-Eigentumsvarianten sowie 156 zulässige/unzulässige Befehlseingaben. Snapshot nach Umbau bytegenau gleich; keine geänderten Zahlen-/Boolwerte, Enumreihenfolgen, Einheiten, Topics oder Fehlerentscheidungen.
- Zwei neue Tests für benannte Konstruktion und Schutz gegen nachträgliche Feld-/Mappingänderungen einschließlich Mutation des ursprünglichen Dictionaries. 66 gezielte Read-/Commandprüfungen und vollständige 203 Offline-Tests ohne unbehandelte Loop-Ausnahmen bestanden. Alle Linter über 107 öffentliche Dateien, Format-/Importchecks und Compose-Parität/Overrides erfolgreich. Abschließende Referenzsuche/Gegenprüfung bestätigt keine verbliebene Positionsauswertung dieser Definitionen.
- Keine Geräte-/Portal-/Installationsbrokerabfragen, Writes, Aktivierung oder private Änderungen. Funktionszerlegung und Widgetvereinfachung bleiben spätere unabhängige Schritte; Frischeumbau wartet weiterhin auf Beobachtungsauswertung.

## 2026-10-11 – Python-Formatierung und Importordnung

- Auftrag: die beiden risikoärmsten Clean-Code-Schritte umsetzen. Bestehende gepinnte Ruff-Version beibehalten; Formatstil explizit mit Zielbreite 100, doppelten Anführungszeichen und vier Leerzeichen festgelegt. EditorConfig abgestimmt. Keine zusätzlichen Bugbear-/Modernisierungsregeln und keine strukturellen Umbauten eingeführt.
- Zuerst 44 öffentliche Python-Dateien formatiert; AST-Vergleich aller 48 Python-Dateien ohne Positionsattribute identisch. Danach 201 Offline-Tests und vollständigen Linter erfolgreich ausgeführt. Private/ignorierte Dateien nicht formatiert.
- Danach ausschließlich Importregel I angewendet: 48 Hinweise korrigiert, Projektpakete sma_mqtt_bridge/tests ausdrücklich eingeordnet. Zweiter AST-Vergleich nur unter Normalisierung zusammenhängender Importblöcke innerhalb ihrer ursprünglichen Scopes identisch; keine andere Logikänderung. Importblöcke im Runtime/Testcode auf Kontext geprüft, keine Imports zwischen Funktionen/Bedingungen verschoben.
- Formatprüfung als read-only Ruff-format-check in tests/lint.py ergänzt; Importregel verbindlich in ruff.toml aktiviert. README enthält die passenden manuellen Korrekturbefehle. Der übliche Linter verändert weiterhin keine Dateien. Abgesehen vom neuen Linter-Prüfschritt nur Format-/Importänderungen in Python.
- Endstand erneut mit allen 201 Offline-Tests ohne unbehandelte Loop-Ausnahmen, allen Lintern über 107 öffentliche Dateien einschließlich Format-/Importprüfung und Compose-Parität/Overrides geprüft. Einheiten, Defaults, Protokolle, Writes/Gates und Daten unverändert. Kein Build, Deployment oder Gerätezugriff; Setting-Dataclass, Funktionszerlegung und Widgetvereinfachung weiterhin spätere unabhängige Schritte.

## 2026-10-11 – Update-Prüfliste seit v0.2.8 live bestätigt

- Andreas bestätigt alle fünf vorgeschlagenen Prüfungen: Start/Anzeigen, Wallbox-Einstellungsrücklesen, erneute Ladeplanübertragung, ganzzahlige MQTT-Werte/openHAB-Anzeige und MQTT-Wiederverbindung.
- Vorgelegtes Log: Startübersicht um 20:51:29 mit sieben Quellen ready und fünf MQTT-Verbindungen connected. Ausfallerkennung ab 20:58:48, alle fünf Verbindungen bis 20:59:17 selbstständig wiederhergestellt; gemeldete Ausfallzeiten 11,0–28,5 Sekunden ab jeweiliger Erkennung. Warnungen zeigen MqttCodeError/MqttError einschließlich Timeouts; keine unbehandelte Future-Ausnahme im vorgelegten Ausschnitt.
- Startübersicht und MQTT-Ausfall-/Erholung für diesen Versuch live belegt. Vollständige Ladezielerreichung, Pending-/falsche-Einheitenfälle, mehrstündige Ausfälle, Last Will und Zeitstempeldiagnose dadurch nicht pauschal abgenommen. Keine privaten Host-/Topic-Kennungen ins Tagebuch übernommen.

## 2026-10-11 – Live-Prüfung der Wallbox-Einstellungsbestätigung

- Andreas bestätigt die Live-Prüfung der Einstellungsanzeige beziehungsweise des Rücklesens nach dem Vergleich mit v0.2.8: Der neue Wert erscheint mit merklicher Verzögerung, anschließend korrekt.
- Konkrete Einstellung und Wartezeit wurden nicht genannt. Keine pauschale Abnahme aller Setter, der Plan-Einheiten oder des Pending-Übergangs daraus ableiten; Pending/Confirmed bleibt zusätzlich offline abgesichert.
- Aktuelle Abnahmematrix entsprechend ergänzt. Keine Gerätebefehle durch Codex und kein Commit oder Deployment durchgeführt.

## 2026-10-11 – Review 6: CLI-Fähigkeitsstatus und Modulbeschreibungen

- Auftrag: geprüften MQTT-Fix zuerst committen und mit dem nächsten Punkt fortfahren. Lokaler Commit 15ad548 (fix: retrieve MQTT disconnect errors and enforce strict loop checks), kein Push oder Deployment.
- Statischen --project-status korrigiert: readOnly=false beschreibt die bereits vorhandenen optionalen Schreibpfade, commandsEnabledByDefault=false stellt die geschlossenen Standard-Gates klar. Keine private Konfiguration dafür geladen, keine Adapter aktiviert und keine vollständige Live-Abnahme behauptet. --check-config behält readOnly anhand der tatsächlich validierten globalen und lokalen/Portal-Gates; keine Freigabe oder Schreiblogik verändert.
- Modulbeschreibung des CLI für optionale Writes präzisiert; config.py und Healthcheck-Kommentar unterscheiden lokale Datei-/TLS-/Profilprüfung von Geräte-/Netzwerk-I/O. Reader-Beschreibung im eCharger-Modul weiterhin korrekt, Setter liegen separat. PROFILES-Vertrag auf nicht implementierte Wechselrichter-Setter eingegrenzt, statt den gesamten Runtime als read-only zu bezeichnen.
- Vorhandener Status-Test vor Fix gezielt fehlgeschlagen. Zwei neue CLI-Regressionsfälle prüfen statische Ausgabe trotz fehlender JSON-Datei/ungültigem Installations-ENV ohne Geheimnisausgabe sowie alle vier Gate-Kombinationen jeweils für lokale und Portal-Konfiguration. Globales Gate ohne Gerätefreigabe weiterhin abgewiesen. Standard-check-config bleibt readOnly=true.
- Alle 201 Offline-Tests ohne unbehandelte MQTT-Future-Ausnahmen, vollständiger Linter über 107 öffentliche Dateien, Compose-Parität/Overrides und Diff-Hygiene bestanden. Review 6 geschlossen; von den sechs konkreten Befunden bleibt Review 4 bis zur Zeitstempelbeobachtung/Auswertung offen. Als nächster unabhängiger Stabilitätsschritt bleibt die deterministische längere Ausfall-/Wiederanlaufsimulation im Plan.

## 2026-10-11 – Review 5: MQTT-Disconnect-Futures

- Auftrag: Zeitstempeldiagnose samt späterem Auswertungs-TODO zuerst committen und mit dem nächsten Review-Punkt fortfahren. Lokaler Commit c865611 (feat: record optional echarger timestamp diagnostics), kein Push oder Deployment.
- Ursache in gepinnter aiomqtt 2.5.1 geprüft: __aexit__ kehrt bei bereits abgeschlossenem Disconnect-Future zurück, ohne dessen Ausnahme abzuholen. Beim Verlust einer nicht bestätigten Publikation blieb dadurch ein MqttCodeError unbehandelt. Bibliotheksversion unverändert.
- Vollständigen Testrunner zuerst verschärft: unerwartete Event-Loop-Ausnahmen erfasst, Standarddiagnose weiterhin ausgegeben und unerreichbare Future-Zyklen vor der Erfolgsentscheidung gesammelt. Vor Laufzeitfix reproduzierbarer Exit 1 trotz 194 bestandener Einzeltests und genau zwei unbehandelten Disconnect-Futures.
- Session-Abbau korrigiert: fertige Disconnect-Ausnahme abgeholt; ohne primären Sessionfehler weitergereicht. Primäre Publikations-/Timeout-Ausnahme bleibt erhalten. Spät eintreffende Future-Ausnahme nach fehlgeschlagenem begrenztem Abbau per Callback abgeholt; ursprünglicher Fehler war dann bereits weitergegeben. Keine Log-Unterdrückung, keine Wiederholungs-/Befehlsänderung und kein zusätzliches MQTT-DISCONNECT vor dem vorhandenen abrupten Socket-Abbruch.
- Drei neue Session-Regressionsfälle für eigenständige Fehlerweitergabe, Erhalt primärer Zeitüberschreitung und späten Disconnect. Zwei Testrunner-Selbsttests: absichtlich unbehandeltes Future lässt sonst erfolgreichen Lauf fehlschlagen, sauberer Loop bleibt erfolgreich. Bestehende reale aiomqtt/Paho-Loopbacktests zusätzlich auf weiterhin sichtbaren Ausfallzähler geprüft; Wiederverbindung, retained Werte und regulärer Disconnect unverändert erfolgreich.
- Alle 199 Offline-Tests mit Exit 0 und ohne die bisherigen Future-Ausnahmen bestanden. Vollständiger Linter über 107 öffentliche Dateien, Compose-Parität/Overrides und Diff-Hygiene bestanden. Review 5 offline geschlossen; echte Installationsausfälle/Last Will und Deployment weiterhin gesonderte Abnahme. Nächster unabhängiger Review-Punkt: CLI-Fähigkeitsstatus und Modulbeschreibungen; Frischeumbau wartet auf Beobachtungsauswertung.

## 2026-10-11 – Optionale Zeitstempeldiagnose im Zustandsvolume

- Auftrag: vor dem eigentlichen Frischeumbau eine rein beobachtende Diagnose einbauen; Dateien dürfen im Docker-Volume liegen. Drei typisierte, standardmäßig deaktivierte SMAB_ECHARGER_TIMESTAMP_DIAGNOSTICS_-Optionen für Aktivierung, Dateigrenze und Zusammenfassungsintervall samt JSON-/ENV-Vorrang ergänzt und dokumentiert.
- Bestehende API-/SEMP-Antworten genutzt; keine zusätzlichen Requests oder Setter. Feste Allowlist für Leistung, Phase-Strom/-Spannung, Energie, Fahrzeug-/Health-/Eventzustände und relevante SEMP-Setpoints. Keine Namen, Seriennummern, Zugangsdaten, Rohantworten oder ungeprüften Zeichenketten gespeichert; Werte numerisch in Protokolleinheiten, Zeitstempel normalisiert. Überalterte Werte bleiben für die Untersuchung sichtbar, Frischeprüfung/MQTT-Veröffentlichung selbst unverändert.
- Datei echarger-timestamps.jsonl mit einer rotierenden Sicherung im vorhandenen SMAB_STATE_DIR/data_smab_state-Volume, standardmäßig je 1 MiB und Modus 0600. Änderungen sofort erfasst, identische Samples nach standardmäßig 300 Sekunden zusammengefasst. Numerisch gleiches 0/0.0 zählt nicht als Wertänderung. API und SEMP bleiben getrennte Beobachtungshistorien.
- Best-Effort-Dateischreiben ohne fsync je Messung; letzte Records können bei abruptem Ausfall fehlen. Schreibfehler beeinflussen das Gerätelesen nicht, Warnung nur mit Fehlerklasse und Wiederholversuch nach Zusammenfassungsintervall. Symlinks/Spezialdateien einschließlich FIFOs abgewiesen, um weder andere Dateien zu überschreiben noch auf einem FIFO zu blockieren. Beobachtung benötigt aktivierten Reader und behauptet bei ausbleibenden Antworten keine Gerätegesundheit.
- Neun gezielte Tests für Änderung/Summary/Altersgrenze, Geheimnisfreiheit/Allowlist, Rotation/Rechte/Neustart, Datei-Fehler, Symlink/FIFO, JSON-/ENV-Vorrang und deaktivierte Quellen sowie API-/SEMP-Vergleich gleicher Requests und Rückgabewerte ergänzt. Vollständige 194 Offline-Tests, Linter über 106 öffentliche Dateien und Compose-Parität bestanden; bekannte zwei MQTT-Future-Ausnahmen bleiben offen.
- Lokalen Docker nur lesend geprüft: aktuell kein laufender Service. Kein Service gestartet, keine private ENV verändert und keine Installation kontaktiert. Diagnose deshalb noch nicht aktiv. Zielhost-Deployment/Aktivierung und natürliche Übergänge bleiben Aufgaben; anschließend mit Andreas Zeitstempelpolitik neu bewerten. Vorhandenes Volume/Manifest/Unklarheitsjournale und private Originalreferenzen erhalten.

## 2026-10-11 – Review 4: Frischeprüfung vor einem Umbau

- Auftrag: zunächst Zeitstempel und Auswirkungen prüfen, anschließend mit Andreas neu bewerten; gezieltes Testen nach einem möglichen Umbau sicherstellen. Vorherigen Homie-Fix als 3bf0446 lokal committet. In dieser Prüfung keine Laufzeit-/Geräteänderung, keine neuen Geräte-, Portal- oder Installationsbrokerabfragen und kein Push.
- Frischeverlust mit festen UTC-/monotonen Zeiten reproduziert: 179 beziehungsweise 180 Sekunden alte Messung bei 180-Sekunden-Limit zwei Sekunden nach Empfang intern noch gültig, Geräteprüfung dann ungültig. Nächste erfolgreiche Abfrage verwirft überalterten Wert; Verlängerung deshalb nicht immer eine volle zusätzliche Laufzeit.
- Originale SEMP-Referenz ausschließlich lesend ausgewertet: Leistung/Fahrzeugstatus fast gleichzeitige Stempel; Sitzungsenergie ungefähr drei Tage, Health/Event ungefähr 29 Tage und einzelne Zustände ungefähr 81 Tage älter. Frühere API-Beobachtung ebenfalls alte Sitzungs-/Health-Stempel. Das deutet auf unterschiedliche Semantik hin, beweist aber keine Kanalregel. API-JavaScript ignoriert Messzeitstempel; offizielle SMA-Schnittstellenübersicht liefert keinen kanalgenauen Vertrag dieser lokalen Antworten. Private Kennungen/Rohantworten nicht übernommen.
- Widgetabhängigkeiten bestätigt: API-ready sperrt lokale Bedienung, Messquellenstatus beeinflusst Fahrzeug-/Anschlussanzeige; aggregiertes Homie-ready kann trotz anderer veralteter Quelle erhalten bleiben. Vollständiger bestehender Regel-/Persistence-Audit bleibt offen. Home Manager bleibt Laderegler und retained Beobachtungen bleiben erhalten.
- Drei deterministische Basistests ergänzt: exakte Altersgrenzen, gültiges Null, Zeitzonenoffset, fehlende/fehlerhafte/zukünftige Zeitstempel und gemischte SEMP-Antwort mit getrennten Einstellungen. Vor einem Umbau zusätzliche zunächst fehlschlagende Ende-zu-Ende-Regressionsfälle nötig; Basistests schließen Review 4 nicht.
- Konkrete Vorher-/Nachher-Matrix in VALIDATION und Reihenfolge im Plan ergänzt: unverändert erneut empfangene alte Samples, gleiche Zahl mit neuem Stempel, Verarbeitungslatenz, Teilantworten/Fallbacks/Aliase, getrennte API-/SEMP-Verfügbarkeit, retained Werte bei Ablauf/Neustart, monotone Laufzeit und unveränderte Befehls-/Unklarheitsschutzpfade. Spätere lesende Installationserfassung mindestens zwei Frischefenster je vorhandener Ruhe-/Ladephase; keine Ladeaktion dafür auslösen. Unerklärtes stale verhindert Rollout, Rückkehr zum alten Image unter Erhalt des Zustandsvolumens vorgesehen.
- Ergebnis: gezielte Korrektur erst nach Zeitstempelklassifikation empfehlen; pauschalen Umbau derzeit nicht empfehlen. Vollständiger Linter über 104 öffentliche Dateien, alle 185 Offline-Tests und Compose-Parität/Overrides bestanden. Zwei bekannte unbehandelte MQTT-Future-Ausnahmen weiterhin offen. Keine neue Live-Abnahme behauptet.

Aktuellen Abnahmestand ausschließlich in VALIDATION.md pflegen; CONTEXT.md enthält Architekturentscheidungen, IMPLEMENTATION_PLAN.md kommende Arbeiten. Technische Verträge, Originalreferenzen und Migrationsledger nicht durch Tagebuchzusammenfassungen ersetzen.

## 2026-10-11 – Dokumente und Widgetquellen aufgeräumt

- Auftrag von Andreas: Widgetquelle vereinheitlichen und vorgeschlagene Struktur für Arbeitsdokumente direkt umsetzen; danach nächsten Schritt vorschlagen.
- README als Einstieg verkürzt; CONTEXT auf Architektur/Protokollentscheidungen begrenzt, IMPLEMENTATION_PLAN auf zukünftige Meilensteine umgestellt. VALIDATION als aktuelle Abnahmematrix mit Datum, direktem/automatisiertem/berichteten Nachweis und verbleibenden Grenzen aufgebaut. MAC_TEST als aktuelle Testanleitung bereinigt; keine alten Aktivierungsstände oder noch nicht implementierten Befehle als aktuelle Aussagen stehen lassen.
- Vorherige Fassungen von CONTEXT, IMPLEMENTATION_PLAN, VALIDATION, MAC_TEST und dem vollständigen bisherigen todo.md einschließlich Review und bereits vorhandener Tagebuchänderungen unter docs/archive/2026-10-11 erhalten. Relative Markdownlinks für den neuen Ort angepasst; Archivverzeichnis erklärt historischen Status. Keine alten BMW-Quellen oder entfernten Baseline-/Scaffold-Dokumente wiederhergestellt.
- Aktive Aufgaben und Q01–Q27 oben neu eingeordnet; offene Fragen und technische Nachweise erhalten. AGENTS.md legt die aktive Tagebuch-/Archivstruktur und eindeutige Dokumentaufgaben fest. Konfiguration, Profile, Wertekatalog, Migrationsvertrag/-ledger und technische Nachweisdokumente bleiben erhalten.
- Kanonische Garagenwidgetquelle: openHAB/yaml/widgets/echarger-comfort.yml. Native MainUI-Importdatei openHAB/sma_echarger_comfort_list.yaml wird durch tools/export_openhab_widget.py erzeugt. Export verändert ausschließlich Hülle/Einrückung, nicht UID, Props, Ausdrücke oder sichtbares Verhalten. Linter prüft erzeugte Datei auf Aktualität; beide Installationswege dokumentiert, nur eine Version je Instanz installieren.
- Die Cleanup-Änderung behebt die Dokumentationshälfte von Review 6. Laufzeitbefunde 1–5 sowie CLI-/Modulbeschreibungsteil von Review 6 bleiben offen und sind priorisiert. Keine pauschale Live-/Produktionsabnahme aus grünen Tests ableiten.
- Private Konfiguration, Originalexporte, Zustand/Manifest/Unklarheitsjournale und installierte openHAB-Definitionen unverändert. Kein Geräte-/Portal-/Brokerzugriff, Deployment, Commit, Push oder Release.
- Abschlussprüfung: vollständiger Linter über 103 öffentliche Dateien bestanden, einschließlich neuer Exportparität; alle 174 Offline-Tests und Compose-Parität einschließlich Overrides bestanden. Loopback-Testserver mit freigegebener Socket-Ausführung, keine SMA-Verbindungen. Bekannte MQTT-Future-Ausnahmen weiterhin reproduziert; Review 5 bleibt ausdrücklich offen.
- Archivintegrität für alle fünf vollständigen Ausgangsdateien nach Linkanpassung geprüft; Widget-YAML semantisch gegen kanonische Quelle und vorherige Importfassung identisch. Exportprüfung erkennt veraltete/fehlende Ausgabe und lehnt falsche Hüllen ab. 165 lokale Markdownziele einschließlich Anker auflösbar; Diff-Hygiene sauber.
- Vorgeschlagener nächster Schritt: zuerst Review 1 mit Pending-/Confirmed-Regressionen beheben, danach Homie-Integer/Node-Metadaten, tatsächliche Frische, MQTT-Abbau und CLI-Status. Anschließend mehrstündige Ausfallsimulation; neue Ladefeatures erst nach diesem Korrekturschritt.

## 2026-10-11 – Review 1: API-Bestätigung und Plan-Einheiten

- Auftrag: zuerst den geprüften Dokument-/Widget-Cleanup committen, danach den nächsten Review-Punkt umsetzen. Cleanup lokal als b147451 (docs: organize working documents and generate widget import) committed; Arbeitsverzeichnis danach sauber. Keine privaten Dateien staged, kein Push/Release.
- Review 1 korrigiert: Jeder API-Einstellungswert benötigt ausdrücklich state=Confirmed. Pending, fehlende oder ungültige Bestätigung liefert für die betroffene Property keinen neuen Wert; unabhängige bestätigte Einstellungen und Messungen bleiben lesbar. Die abgeleitete Anzeige der manuellen Ladefreigabe darf den Guard nicht umgehen. Nameplate-Identitäts-/Firmwarewerte bleiben gesondert lesbar.
- SEMP verwendet explizit seinen eigenen Lesepfad ohne API-Bestätigungsmetadaten. Bestehende Modus-/Freigabe-/Rohwerte und Epochsekunden-Konvertierung des Ladeendes erhalten; kein künstliches Confirmed-Feld ergänzt und keine zusätzlichen Schreibwege freigegeben.
- Plan-Ende im API-Pfad braucht Unit s oder den bereits für Planbefehle verifizierten EVC22-3AC-20 / 2.6.37.R-Fallback. Explizite widersprechende Units blockieren den Wert; unitlose unbekannte Firmware bleibt unavailable. Gemeinsame Unit-Auflösung auch für Planvorprüfung und Rücklesen verwendet. Passende Zahlen mit falscher Unit dürfen weder Zielmodusaktivierung noch endgültige Bestätigung auslösen; das Unklarheitsjournal bleibt erhalten.
- Regressionen zuerst gegen den alten Code ausgeführt: Pending-Veröffentlichung, widersprechende Plan-End-Units und fälschlich bestätigtes Modusrücklesen reproduziert. Fünf neue Tests prüfen alle zwölf API-Einstellungen einzeln, Planzeit-/Firmware-/Unit-Grenzen, echte API-Lesekette samt Freigabealias, Rückleseunsicherheit sowie Polling nach verlorener Schreibantwort mit retained Beobachtung und dauerhafter Wiederholungssperre. Bestehende SEMP- und Plan-Tests erweitert; API-Testmetadaten ausdrücklich als Confirmed gekennzeichnet.
- Gezielte 52 Protokoll-/Plan-/Leistungs-/Unsicherheitsprüfungen bestanden. Die neue retained-Regression bestätigt: alter Wert bei Pending erhalten; spätere bestätigte Beobachtung erlaubt, Unklarheitsjournal trotzdem erhalten und kein zweiter PUT. Weder HTTP-Erfolg noch späteres Polling löst automatisch die Befehlsunsicherheit auf.
- CONFIGURATION-Vertrag, aktuelle Abnahmematrix, zukünftigen Plan und aktive Aufgaben aktualisiert. Review 1 offline gelöst; Deployment und neue Hardwareabnahme nicht durchgeführt. Review 2–5 und CLI-/Modulbeschreibungsteil von Review 6 bleiben offen.
- Abschlussprüfung: alle 179 Offline-Tests, vollständiger Linter über 103 öffentliche Dateien einschließlich Widgetexport sowie Compose-Parität/Overrides bestanden. Zwei bekannte unbehandelte MQTT-Future-Ausnahmen weiterhin reproduziert; separater Review 5 bleibt offen. Diff-Hygiene sauber. Keine echten Geräte-/Portal-/Brokeraktionen; lokale Protokollfixtures bleiben geheimnisfrei, private Originalreferenzen unverändert.

## 2026-10-11 – Review 2: Homie-Integer und Wertebereich

- Auftrag: geprüften Review-1-Fix zuerst committen und mit dem nächsten Befund fortfahren. Lokaler Commit 3d8baf5 (fix: require confirmed echarger settings and verified plan units) enthält ausschließlich die geprüften öffentlichen Änderungen. Kein Push/Release.
- Review 2 korrigiert: Numerisch integrale Werte werden für Integer-Properties kanonisch als Dezimal-Ganzzahl ausgegeben. Decimal 4500.0 wird zu 4500, Exponent-/Plus-/führende-Null-Eingaben werden normalisiert und negatives Null zu 0. Homie-4-Grenzen -2^63 bis 2^63-1 vor der Integerkonvertierung geprüft; kein riesiger Integer aus einem ungültigen Decimal-Exponenten erzeugt. Bruchzahlen, Bool, ungültige/nonfinite Eingaben und Werte außerhalb des Bereichs bleiben unavailable; keine Rundung oder Ersatznull.
- Float-Kanäle behalten die bisherige Ausgabe, etwa 4500.0 und -0.5. Channel-IDs, Einheiten, Befehlsgrenzen und retained Werterhaltung unverändert. Vorhandenen Leistungsgrenzen-Test auf korrektes Integer-Rückleseformat 4500 korrigiert; sein API-Fixturewert 4500.0 bleibt als echte Regression erhalten.
- Zwei neue Modelltests für kanonische Ausgabe, beide exakten Bereichsgrenzen, Über-/Unterschreitung, Bruchzahlen nahe Grenzen, große Decimal-Exponenten, nonfinite Werte und Float-Abgrenzung ergänzt. SourceState darf einen außerhalb des Bereichs liegenden Wert nicht als neue Beobachtung übernehmen. Drei gezielte Tests gegen alten Code mit zwölf Fehlern reproduziert, danach 21 Modell-/Leistungsprüfungen bestanden.
- Offizielle Homie-4-Payloadspezifikation konsultiert; Konfigurationsvertrag, aktuelle Abnahmematrix, zukünftigen Plan und aktive Aufgaben aktualisiert. Review 2 offline gelöst; Zielhost-Deployment und neue Live-Abnahme bleiben separat offen. Review 3–5 und CLI-/Modulbeschreibungsteil von Review 6 weiterhin offen.
- Abschlussprüfung: vollständiger Linter über 103 öffentliche Dateien, alle 181 Offline-Tests und Compose-Parität einschließlich Overrides bestanden; Diff-Hygiene sauber. Zwei bekannte unbehandelte MQTT-Future-Ausnahmen bleiben unter Review 5 offen. Keine SMA-/Portal-/Installationsbroker-Verbindungen und keine echten Gerätebefehle; private Originale und Konfiguration unverändert.

## 2026-10-11 – Review 3: Pflichtmetadaten der Homie-Nodes

- Auftrag: geprüften Integer-Fix zuerst committen und mit dem nächsten Befund fortfahren. Lokaler Commit aff6d76 (fix: serialize Homie integers within signed 64-bit bounds); kein Push/Release.
- Review 3 korrigiert: Discovery ergänzt für jeden Node das obligatorische retained Metadatum $type. Normale und benutzerdefinierte Nodes nutzen ihre stabile interne Kennung; delegierte Home-Manager-Nodes device-<Nummer> teilen den Typ device. Typen werden nicht aus Anzeigenamen abgeleitet oder übersetzt; Slot-/Channel-IDs und Profilformat unverändert.
- Bestehenden MQTT-Metadaten-/Manifestpfad verwendet: Type wird vor ready veröffentlicht, im Topicbesitz erfasst und beim Wegfall eines Nodes als retained Topic entfernt. Kein neues Konfigurationsfeld, keine zusätzliche Modellregistrierung und keine separate Retirement-Logik eingeführt.
- Neuer Pflichtmetadatentest umfasst Geräte-, Node- und Propertyattribute für sieben bestehende Gruppen, zwei delegierte Slots und einen benutzerdefinierten Profilnode. Vor dem Fix fehlte $type in allen zehn Nodes; Sprachtest ebenfalls reproduzierbar fehlgeschlagen. Bestehende Publisher-, Übersetzungs- und dynamische Inventartests um Type-Stabilität, retained Veröffentlichung vor ready, Tombstone und Manifestprüfung erweitert.
- Gezielte 50 Laufzeit-/Übersetzungs-/Home-Manager-Modbus-Tests bestanden. Offizielle Homie-4-Spezifikation und openHAB-Homie-Dokumentation konsultiert; Konfigurationsvertrag, aktuelle Abnahmematrix, Plan und aktive Aufgaben aktualisiert. Neue echte Broker-/openHAB-Abnahme bleibt separat offen.
- Abschlussprüfung: vollständiger Linter über 103 öffentliche Dateien, alle 182 Offline-Tests und Compose-Parität einschließlich Overrides bestanden; Diff-Hygiene sauber. Zwei bekannte unbehandelte MQTT-Future-Ausnahmen bleiben unter Review 5 offen. Keine SMA-/Portal-/Installationsbroker-Verbindung oder Gerätebefehle; private Konfiguration, Referenzen und installierte openHAB-Definitionen unverändert. Review 4–5 und CLI-/Modulbeschreibungsteil von Review 6 bleiben offen.

## 2026-10-11 – Wallbox-Gesamtenergie in kWh abgenommen

- Andreas bestätigt die erfolgreiche Prüfung von openHAB-Einheit, Skalierung und bestehender Historie der Wallbox-Gesamtenergie. Der entsprechende Abnahmepunkt ist erledigt.
- Aktive Aufgaben, Abnahmematrix und Implementierungsplan abgeglichen; übrige Migrations-/Historienprüfungen bleiben eigenständig offen.

## 2026-10-11 – Verfügbarkeit ohne optionale Diagnose abgenommen

- Andreas bestätigt, dass das Widget bei ausgeschalteter optionaler Diagnose weiterhin den Quellenstatus erhält. Zielhost-Abnahme für diesen Punkt abgeschlossen.
- Aktive Aufgaben, Abnahmematrix und Implementierungsplan abgeglichen; mehrstündige Ausfälle und externe Alarmierung bleiben offen.

## 2026-10-11 – Homie-Node-Typ am Broker bestätigt

- Andreas bestätigt, dass das neue $type-Metadatum am Broker vorhanden ist. Die gezielte Live-Prüfung ist abgeschlossen; dynamisches Retirement und Manifestbesitz bleiben durch Offline-Tests belegt.

## 2026-10-11 – Zeitstempelaufzeichnung auf dem Zielhost aktiviert

- Andreas bestätigt die Aktivierung der optionalen Zeitstempelaufzeichnung auf dem Zielhost. Aktivierungsaufgabe abgeschlossen; Dateiinhalt und ausreichende Beobachtungen sind noch nicht geprüft.
- Aufzeichnungen in Ruhe-/Ladephasen und bei natürlichen Zustandswechseln sammeln und später gemeinsam auswerten. Daraus erst die kanalweise Zeitstempelpolitik ableiten; kein Frischeumbau durch die Aktivierung.

## 2026-10-11 – Externe Überwachung und Alarmierung eingerichtet

- Andreas bestätigt die Einrichtung der externen Überwachung und Alarmierung. Konkrete Überwachungswege und ausgelöste Alarmfälle wurden nicht genannt; daraus keine vollständige Ausfallabnahme ableiten.
- Host-Neustart und Zustandswiederherstellung bleiben als separate aktive Aufgabe offen.

## 2026-10-11 – App-Version mit aktuellem Release-Tag abgeglichen

- Auf Andreas’ Auftrag __version__ in ressources/sma_mqtt_bridge/__init__.py von 0.1.0 auf 0.3.1 gesetzt, passend zum neuesten lokalen Tag v0.3.1. Veraltete Read-only-Modulbeschreibung korrigiert; keine Änderung an Befehlsfreigaben.
- CLI --version meldet sma-mqtt-bridge 0.3.1. Vollständiger Linter und alle 203 Offline-Tests bestanden; für die lokalen Loopback-Testserver war Socket-Ausführung außerhalb der Sandbox erforderlich. Keine Geräteverbindung, kein Commit, Tag, Push oder Deployment. Künftige Release-Tags müssen weiter mit der App-Version abgeglichen werden.

## 2026-10-11 – Vollständige CI als Release-Voraussetzung

- Auf Andreas’ Auftrag CI via workflow_call wiederverwendbar gemacht. Der Release ruft dieselben Lint-/Test-/Compose-/amd64-/arm64-Build-, Container-Test- und Trivy-Jobs für den getaggten Stand auf und benötigt deren erfolgreichen Abschluss vor GHCR-Login/Veröffentlichung.
- packages:write ausschließlich im Veröffentlichungsjob; Validierung nur mit contents:read. CI-Concurrency um Ereignistyp ergänzt, um direkt gestartete und durch Release aufgerufene Läufe getrennt zu halten. Keine neue Veröffentlichung ausgelöst.
- GitHub-hosted Ausführung und reale Multiarch-/Scan-Ergebnisse bleiben separat offen.

## 2026-10-11 – Wiederholte erfolgreiche GitHub-CI bestätigt

- Andreas bestätigt, dass die vorhandenen GitHub-Läufe für Linter, Tests, Compose-Prüfung, amd64/arm64-Builds, Container-Tests und Sicherheitsprüfungen mehrfach erfolgreich gelaufen sind. Bisher fehlende Hosted-CI-Abnahme entsprechend korrigiert.
- Konkrete Lauf-URLs/Commitstände wurden nicht genannt. Die gerade ergänzte Release-/CI-Verknüpfung benötigt weiterhin einen eigenen GitHub-Lauf; keine pauschale Release-Veröffentlichung daraus ableiten.

## 2026-10-11 – Sicherheitsgrenze und Prüfung öffentlicher Daten

- Auf Andreas’ Auftrag Trivy in CI (beide Architekturen) und Release auf HIGH,CRITICAL mit Exit 1 erweitert. ignore-unfixed=true bleibt: behebbare hohe/kritische Schwachstellen blockieren; Befunde ohne verfügbaren Fix werden weiterhin nicht zum Gate.
- Offizielles Gitleaks 8.30.1 temporär außerhalb des Repositorys geladen, SHA-256 gegen veröffentlichte Prüfsumme verifiziert. Redaktierte Prüfung aller 107 aktuellen Git-Dateien sowie der gesamten erreichbaren Historie (--all, 46 Commits, 570 eindeutige Blobs) ohne Secret-Fund. Private ENV, Daten, Geheimnisdateien und private Referenzen in keiner erreichbaren Revision getrackt; private/README.md ist die öffentliche Ausnahme.
- Zusätzlich historische Blob-Inhalte gegen ausgewählte aktuelle private ENV-Werte abgeglichen. Acht Treffer waren ausschließlich eine harmlose Teilzeichenfolge in historischen Bibliotheksnamen, kein Konfigurationsleck. Keine privaten Werte ausgegeben; temporäre Reports nicht ins Repository übernommen. Die Prüfung ist keine Garantie für sämtliche persönlichen Daten oder unerreichbare Git-Objekte.
- Vollständiger Linter und alle 203 Offline-Tests bestanden. Neue Trivy-Ergebnisse unter der verschärften Grenze stehen erst nach dem nächsten GitHub-Lauf zur Verfügung; lokal kein Trivy installiert und Docker-Zugriff sandboxseitig gesperrt. Keine Veröffentlichung oder Historienänderung durchgeführt.

## 2026-10-11 – Release-Dokumentation als Aufgabe aufgenommen

- Andreas beauftragt, Änderungen/Upgrade-Hinweise und README-Anpassung als offenen TODO-Punkt aufzunehmen. Dokumentationsumsetzung folgt später.
- Andreas bestätigt den bestehenden Produktionsbetrieb des veröffentlichten Images mit der Beispiel-Compose-Datei. Daraus keine zusätzliche gezielte Healthcheck-/Volume-Abnahme ableiten.

## 2026-10-11 – Automatische Versionsableitung

- Auf Andreas’ Auftrag manuelle App-Versionsnummer ersetzt: saubere stabile Git-Tags melden die Release-Version; spätere Commits/getrackte Änderungen eine dev-Kennung mit Abstand, Commit und optional .dirty. Ohne Git/Build-Metadaten ehrlicher Rückfall 0.0.0+unknown.
- Docker übernimmt SMAB_BUILD_VERSION als reines Build-Argument und speichert die geprüfte Version im Paket; kein Git/private Daten im Kontext, kein Laufzeit-ENV-Override. tools/build_image.sh leitet für lokale Builds die Version automatisch ab; direkte Compose-Builds ohne Build-Argument bleiben unknown. README erklärt beide Wege.
- CI lädt die Tag-Historie, übergibt die ermittelte Version für beide Architekturen und prüft die CLI-Ausgabe. Release verwendet die stabile Tag-Version für Vorab-/Multiarch-Build und prüft die Vorab-Image-CLI vor Veröffentlichung.
- Zwei neue Regressionstests für saubere Tags, Abstand/dirty, ungültige Tags, Git-Ausfall und Image-Metadaten ohne Git. Vollständiger Linter und alle 205 Offline-Tests bestanden; Docker-Build und GitHub-Ausführung der neuen Versionskette bleiben separat zu prüfen. Kein Commit, Push oder Release ausgelöst.
