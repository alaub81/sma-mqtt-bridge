# TODO

Die aktuelle Abnahme steht in [docs/VALIDATION.md](docs/VALIDATION.md), die Reihenfolge kommender Meilensteine in [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md). Hier stehen aktive Aufgaben, offene Fragen und neue Tagebucheinträge. Die vollständigen bisherigen Einträge einschließlich des Codereviews bleiben im [Tagebucharchiv vom 11.10.2026](docs/archive/2026-10-11/todo.md) erhalten; frühere Aussagen sind zeitlich einzuordnen.

## Aktive Aufgaben

- [ ] Review 1–5 beheben: unbestätigte API-Einstellungen, Homie-Integer und Node-Typen, tatsächliches Messwertalter sowie unaufgeräumte MQTT-Futures. Nachweise und Fundstellen im [archivierten Review](docs/archive/2026-10-11/todo.md#2026-10-11--repository--und-codereview); Umsetzungsschritte im Plan. Bestehende Unsicherheitssperren und retained Beobachtungen erhalten.
- [ ] Review 6 abschließen: CLI-Projektstatus und Modulbeschreibungen an optionale Schreibpfade beziehungsweise Datei-I/O anpassen. Aktuelle Dokumentation ist bereinigt.
- [ ] Nachtbetrieb vollständig abnehmen: Morgen-Aufwachen und Wertaktualisierung sowie Schlaf-/Ausfallunterscheidung prüfen. Abendbeobachtung am 11.10.2026 laut Andreas unauffällig.
- [ ] Mehrstündigen deterministischen Ausfalltest und Produktionsabnahme ergänzen: langsame/unvollständige Antworten, Geräte-/Broker-Ausfälle, abruptes Prozessende, Last Will, TLS, Topic-Retirement und selbstständige Erholung. Kontrollierter Stop/Start ist separat bestätigt.
- [ ] Externe Betriebsüberwachung für Prozessstillstand, Docker-unhealthy, Broker-Ausfall und dauerhaft fehlende kritische Werte einrichten; Host-Neustart und Zustandswiederherstellung prüfen. Manifest, Unklarheitsjournale und Instanzsperre erhalten.
- [ ] Aktuelles Image auf dem Zielhost prüfen: Quellenstatus bei deaktivierter optionaler Diagnose, Startübersicht und Wallbox-Gesamtladeenergie in kWh einschließlich Item-Metadaten/Persistence. Home-Manager-Startstatus wurde bereits separat bestätigt.
- [ ] Bei Home-Manager-Modbus beide Compose-Dateien auf normales Docker-Bridge-Netzwerk umstellen und Zielhost-Verbindungen einschließlich DNS/TLS prüfen. UDP-Multicast als Alternative mit eigenen Voraussetzungen erhalten; Compose-Parität prüfen. Bis dahin Netzwerk unverändert.
- [ ] openHAB-Migration und Historien vollständig abnehmen; sämtliche 100 Ledgerzeilen, sieben noch nicht zugeordnete Itemlinks, Maps, Vorzeichen, private Offsets, Regeln, UI und Tages-/Sommerzeitgrenzen erhalten. Keine Fähigkeiten stillschweigend streichen.
- [ ] Grafana-Dashboards für den Parallelvergleich alter openHAB- und neuer Bridge-Zeitreihen erstellen: gleiche Einheiten und abgestimmte Messzeitpunkte, Abweichungen und Lücken sichtbar machen.
- [ ] Ladeziel-/Sitzungsenergie-Semantik, physische Zielerreichung und Rückwechsel prüfen. Die gemeldete 10-kWh-Planübertragung und Modusaktivierung sind keine vollständige Ladeabnahme.
- [ ] Maximale Ladeleistung physisch abnehmen und einphasiges Winterladen untersuchen. Mindeststrom-Setter nur nach eigenen Metadaten-/Einheitenbelegen ergänzen; 4 kW sind laut geprüftem Limit unzulässig, 4,5 kW plus 10 A bleibt unbestätigter Versuchskandidat. Live-Versuche nur mit ausdrücklich angeforderten Zielwerten; Home Manager bleibt Regler. [Nachweise und offene Phasenfragen](docs/ECHARGER_POWER_LIMIT.md).
- [ ] Zusätzliche Profile/Portalwerte und aktuellen Lademix nur mit bestätigten Messwerten, Einheiten, Zeitbezug und Identität ergänzen. Tagesanteile und Mindest-PV-Präferenz nicht als aktuellen Lademix veröffentlichen.
- [ ] Kleine Diagnose-/Frischeverbesserungen und ausdrückliches Portal-Leseauffrischen ohne Neustart bewerten; anschließend gezielte Funktionsvereinfachung und zusätzliche Linterregeln. Keine allgemeine Adapterplattform bauen.
- [ ] Später lhlab.wiki-Artikel aus [openHAB/openHAB.md](openHAB/openHAB.md) erstellen. Beispiel-Item-Dateien und Sitemaps bleiben auf Andreas’ Wunsch aus dem Umfang gestrichen.
- [ ] Öffentlichen Stand später nach [GitHub](https://github.com/alaub81/sma-mqtt-bridge) hochladen und GHCR-Release vorbereiten. Private Daten ausschließen, Hosted CI/Sicherheitsprüfungen und beide Architekturen verifizieren; Veröffentlichung ist durch diesen Cleanup nicht beauftragt.

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
