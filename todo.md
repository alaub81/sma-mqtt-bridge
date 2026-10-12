# TODO

Die aktuelle Abnahme steht in [docs/VALIDATION.md](docs/VALIDATION.md), die Reihenfolge kommender Meilensteine in [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md). Hier stehen aktive Aufgaben, offene Fragen und neue Tagebucheinträge. Die vollständigen bisherigen Einträge einschließlich des Codereviews bleiben im [Tagebucharchiv vom 11.10.2026](docs/archive/2026-10-11/todo.md) erhalten; frühere Aussagen sind zeitlich einzuordnen.

## Aktive Aufgaben

- [ ] Auf Andreas’ Wunsch vom 12.10.2026 die Home-Manager-Anlagenzeit (`measurements/planttime`) in openHAB als Datum/Uhrzeit darstellen. Unix-Sekunden in der Bridge unverändert erhalten; für reine Anzeige eine State-Description-Transformation verwenden, bei Zeitvergleichen/Regeln ein DateTime-Item mit geeigneter Umwandlung vorsehen. Zeitzone `Europe/Berlin` einschließlich Sommerzeit in openHAB behandeln; eine einfache Datumsformatierung eines Number-Items allein genügt nicht. Vor Umsetzung offizielle openHAB-Dokumentation konsultieren und bestehende Links/Item-Namen berücksichtigen.

- [ ] Auf Andreas’ Wunsch vom 12.10.2026 die drei Wallbox-SEMP-Steuerwerte `control/activechargingcount` (`Setpoint.PlantControl.PCC.ChrgActCnt`), `control/powersetpointmaxpercent` (`Setpoint.PlantControl.Inverter.WModCfg.WCtlComCfg.WSptMaxNom`) und `control/powersetpointminpercent` (`Setpoint.PlantControl.Inverter.WModCfg.WCtlComCfg.WSptMinNom`) genauer erklären und belegen. Für ChrgActCnt Zählumfang und Vorgabe gegenüber tatsächlichem Zustand klären; für WSptMaxNom/WSptMinNom Einheit, Normierungsbasis, Vorzeichenkonvention und Wirksamkeit klären. Verhältnis zur Home-Manager-Laderegelung und zur separaten maximalen Ladeleistung untersuchen; offizielle Dokumentation/Metadaten und lesende Beobachtungen bei natürlichen Ladezustandswechseln verwenden. Bisherige Rohwerte 0/0/-100 reichen nicht als Semantikbeleg; keine PV-/Netzanteile ableiten und keine Setter oder Live-Schreibversuche daraus freigeben.

- [x] Typ-/Leistungsgrenzen für inverter1/2 am 12.10.2026 dokumentiert, im Scan lesbar und lokal als Profil-Mappings ergänzt: `measurements/type`, `maxpower`, `setmaxpower`; Advanced-Konvention wie inverter3, Leistungsgrenzen read-only. Produktionsveröffentlichung separat offen.
- [x] Dokumentarischer Vollständigkeitsabgleich der drei Wechselrichter am 12.10.2026 durchgeführt: [Bericht](docs/MODBUS_TOPIC_AUDIT.md) und vollständige CSV-Registerliste. 491/410/360 lesbare Geräte/Register-Paare ohne Profil-Topic; Mehrfachdarstellungen und bedingte Unterstützung ausdrücklich getrennt. Vorhandene Mapping-Adressen, Typen, Längen und FIX-/TEMP-Skalierungen geprüft; keine neue Live-Abnahme.
- [x] Produktionsabhängiger Modbus-Verfügbarkeitstest am 12.10.2026 um 08:25–08:31 Europe/Berlin abgeschlossen: 1307 Leseabfragen, 872 Werte einschließlich 105 gültiger Nullwerte, 433 SMA-NaN, zwei nicht dekodierbare Strings. Keine Ablehnungen/Verbindungsfehler. [Ergebnis und Kandidaten](docs/MODBUS_AVAILABILITY_2026-10-12.md); Automation pausiert.
- [ ] Mit Andreas eine sinnvolle kleine Smart-Home-Auswahl aus den tatsächlich verfügbaren Modbus-Kandidaten treffen; Einheiten/Enums, alternative Zähler und Basic/Advanced/Diagnostics anschließend festlegen. 433 NaN und zwei nicht dekodierbare Strings aus der ersten Kandidatenliste ausgeschlossen, ursprüngliche Evidenz samt Zustandsbezug erhalten. Sunny Boy explizit für L3 abbilden: 40183 = 329, L3-Leistung/-Spannung/-Strom gültig; vorhandene L1-Topics nicht stillschweigend umdeuten. DC-Eingang B lesbar mit 0, tatsächliche Belegung offen. Schreibbefehle weiterhin separat prüfen.

### Modbus-Umsetzung aus dem Produktionsscan

Die vollständigen Einzelbefunde stehen in [der Ergebnismatrix](docs/modbus-availability-2026-10-12.csv), die fachliche Auswahlgrundlage im [Scanbericht](docs/MODBUS_AVAILABILITY_2026-10-12.md). Die folgenden Pakete sind eine vorgeschlagene Reihenfolge, keine bereits beschlossene Erweiterung aller Topics oder Kanalgruppen.

- [x] M01 – Sunny-Boy-Phasenmapping am 12.10.2026 lokal erweitert: auf Andreas’ ausdrücklichen Wunsch L2 und L3 jeweils mit Leistung, Spannung und Strom. Neue Topics `measurements/powerl2`, `powerl3`, `voltg2`, `voltg3`, `currentl2`, `currentl3`; vorhandene L1-Definitionen unverändert. Keine feste L3-Modellannahme, kein automatischer Phasenwechsel. Dokumentierte L2-NaN werden nicht als Werte veröffentlicht; Basiskanal-Default wie vorhandene Phasenwerte, späterer gemeinsamer Gruppenreview bleibt offen.
- [ ] M01-Abnahme – Nach Image-Neubau/Container-Neustart sechs neue L2/L3-Discovery-Kanäle und echte L3-Werte prüfen; gegebenenfalls verwendete Host-Profilkopie ausdrücklich ergänzen. Neue openHAB-Links/Items phasenrichtig anlegen, L1-IDs/Historie erhalten. Der bisherige Scan belegt Geräte-Lesbarkeit, nicht Veröffentlichung durch den erweiterten Laufzeitbetrieb.
- [x] M02 – Typ-/Leistungsgrenzen für inverter1/2 umgesetzt: Rohmodellcode 30053, RO-Leistungsgrenzen 30231/30233, gleiche IDs/Labels/Advanced-Konvention wie Sunny Boy. Bestehende Identity-/Statusblöcke verwendet; keine Setter.
- [x] M03 – Kleine AC-Auswahl umgesetzt: Netzfrequenz aller drei Wechselrichter, Ströme Tripower L1/L2/L3 und Storage L1; Sunny Boy L2/L3 bereits in M01 ergänzt. Neue Messwerte mit bestehendem Basic-Default, fünf Sekunden für neue kleine Pollblöcke. Zusätzliche Tripower-/Storage-Phasenspannung/-leistung war nicht Teil dieses Auftrags und bleibt eine mögliche spätere Auswahl.
- [x] M04 – Storage signed AC-Gesamtleistung, Batteriestrom und Batteriespannung 30775/30843/30851 ergänzt. Vorzeichen unverändert erhalten, keine Ladezustandsableitung aus dem Vorzeichen. Bestehende Batteriemessungen und langsame Poller unverändert.
- [x] M05 – Storage-Energiezähler 31397/31401 nach ausdrücklichem Umsetzungsauftrag ergänzt: U64/FIX0, Herstellerquelle Wh, Veröffentlichung kWh mit Faktor 0.001. Gültige 0 erhalten; alter 30531/30537-kWh-Sonderfall nicht übertragen. Direkter GUI-/Verlaufsvergleich, Reset-/Zählumfang und neue MQTT-/openHAB-Abnahme bleiben separat offen.
- [ ] M06 – Scheinleistung und Leistungsfaktor nach Nutzen auswählen: 30813 sowie Varianten 30949/31221 verfügbar. Unterschiedliche PF-Konventionen klären und nur eine passende Darstellung wählen. Blindleistung modell-/phasengenau prüfen; Tripower 31497 verfügbar, Storage/Sunny Boy 30805 NaN, keine unbelegte Ersatzzuordnung.
- [ ] M07 – Betriebs-/Einspeisedauern 30521/30525 am 12.10.2026 als U64-Sekunden/Advanced umgesetzt; MQTT-/openHAB-Abnahme offen. Alternative Ertragszähler 30513/30517 und 32-Bit-Zeitdopplungen weiterhin nur nach Nutzen bewerten; bestehende ganze-kWh-Topics und Historie erhalten.
- [ ] M08 – Derating-Grund 30219 am 12.10.2026 als modellgenauer Diagnostics-Enum umgesetzt, NaN/Unbekannt bleibt unveröffentlicht. Ereignisregister 30247 weiterhin wegen NaN aus erster Auswahl ausgeschlossen; spätere natürliche Ereignisbeobachtung möglich. Live-Abnahme offen, keine Fehler absichtlich erzeugen.
- [x] M09 – Sunny-Boy-DC-Eingang B auf Andreas’ Wunsch ergänzt: Strom/Spannung/Leistung als Basis, read-only, FC04 30957/30959/30961 alle 5 s. Scan lieferte gültige 0; tatsächliche Stringbelegung bleibt offen. MQTT-/openHAB-Abnahme der Ergänzung ausstehend.
- [ ] M10 – Ausschlussliste bewahren: 433 NaN und zwei nicht dekodierbare Storage-BMS-Strings bleiben aus der ersten Kandidatenliste ausgeschlossen. Bei Bedarf später gezielt unter natürlichen Lade-/Entlade-/Ereigniszuständen prüfen; kein erneuter Vollscan automatisch geplant. Identitäts-/Netzwerkwerte, Konfigurationsbeobachtungen und Dopplungen gemeinsam nach Nutzen behandeln; aus RO/RW/WO keine automatische Schreibfreigabe ableiten.

- [ ] M02–M04-Abnahme – Neue Profilkanäle nach Image-Neubau/Neustart am Broker und mit passenden openHAB-Units prüfen. Gegebenenfalls ausgewählte Host-Profilkopien ausdrücklich erweitern. Neue Eigenschaften sind offline getestet; frühe Registerantworten allein bestätigen keine Veröffentlichung. Gemeinsamer späterer Gruppenreview bleibt offen.
- [x] Home Manager – Vollständiger lesender NSD-Verfügbarkeitscheck am 12.10.2026 um 10:28–10:29 Europe/Berlin abgeschlossen: Identität geprüft, alle 16 Unit-1/2-Eigenschaften gültig, alle 245 Zuordnungsslots gelesen. Drei zugeordnete Geräte mit je 16 delegierten Parametern geprüft: 30233 je Gerät gültig, übrige 45 Antworten SMA-NaN. Keine Ablehnung/Transportfehler, keine Writes/Login/MQTT. [Bericht](docs/HOME_MANAGER_AVAILABILITY_2026-10-12.md) und vollständige Statusmatrix; keine neuen Topics.
- [ ] Home Manager – Ursache der 45 delegierten NaN-Antworten bei Bedarf gezielt klären (Modell/Zustand/Zugriff), dokumentierte Mappings nicht pauschal als dauerhaft ununterstützt löschen. Vollständige Broker-/openHAB-/Historien- und Betriebsabnahme bleibt separat offen; kein Grid-Guard-Login oder Gerätetestschreiben automatisch durchführen.
- [x] Wallbox-API-/SEMP-Vollständigkeitsabgleich am 12.10.2026 abgeschlossen: [Bericht](docs/ECHARGER_TOPIC_AUDIT.md), vollständige Kanalmatrix und Standard-SEMP-Feldmatrix. Aktuell 85 API-Parameter, 44 API-Mess-/Setpointkanäle und 25 SEMP-Parameterkanäle lesend erfasst. 24 SEMP-Kanäle gemappt, Standort bewusst ausgeschlossen; API-Lücken und Quelleneigentum einzeln dokumentiert. Keine automatische Topic-Erweiterung oder neue Setter.

- [x] E01 – Wallbox-Phasenwirkleistung am 12.10.2026 lokal ergänzt: `measurements/powerl1`, `powerl2`, `powerl3` aus GridMs.W.phsA/B/C, Float/W/read-only. Offizielle lokale WebUI-Metadaten bestätigen unit 18 = W und SCALAR ohne Rohskalierung; fehlende Unit nur für geprüftes Modell/Firmware erlaubt, widersprüchliche Units blockieren den Wert. Vorzeichen/Bruchteile/Null unverändert; keine physische Flussrichtung aus dem Vorzeichen behauptet.
- [ ] E01-Abnahme – Nach Image-Neubau/Container-Neustart neue W-Metadaten und L1/L2/L3-Werte am Broker prüfen; bei Bedarf phasenbezogene openHAB-Number:Power-Items mit Unit W verknüpfen. Bestehende Gesamtladeleistung und Historie erhalten; neue Bridge-Veröffentlichung und physische Ladeabnahme noch offen.
- [ ] E02 – Wallbox-Schein-/Blindleistung nach Nutzen auswählen: TotVA und VA.phsA/B/C sowie TotVAr und VAr.phsA/B/C (acht Kanäle) aktuell frisch und ungemappt. Units/Skalierung/Signkonvention prüfen, Totale/Phasen sinnvoll begrenzen und Gruppen gemeinsam entscheiden.
- [ ] E03 – Wallbox-GI1/GO1 und Diagnosekanäle fachlich prüfen: GI1 frisch und ungemappt; GO1, Ereignisnummer/-beschreibung/-zähler, Leistungsbegrenzungsquelle, Firmware-/Web-/WLAN-Status teilweise nur mit altem Zeitstempel, Speedwire-Status ohne Wert. Exakte I/O-/Enum-/Zeitstempelsemantik klären; keine Altersfilter pauschal entfernen und keinen Testfehler erzeugen.
- [ ] E04 – API-only-Fallback-Abdeckung bewerten: sieben API-Mess-/Setpointkanäle werden nur vom SEMP-Adapter auf zusätzliche Topics gemappt. Bei aktiviertem SEMP abgedeckt; mit abgeschaltetem SEMP fehlen diese Zusatzmappings und der zusätzliche Health-Rohcode (Health-Text hat dagegen einen API-Fallback). Transport-/Topic-Eigentum erhalten, gezielte Ergänzung nur nach gemeinsamem Bedarf.
- [ ] E05 – Standard-SEMP-Felder bewerten: 13 nicht als Topics dekodierte Status-/EMSignalsAccepted-, Leistungs-/Zeitgrenzen-/Capability- und PowerInfo-Felder inventarisiert. AveragePower samt Intervall nicht ungeprüft als Ersatz für momentane Ladeleistung verwenden; keine SEMP-Steuerung oder konkurrierenden Regler hinzufügen.
- [ ] E06 – Zusätzliche Wallbox-Ladeparameter nach Nutzen/Units prüfen: AMinCha, Plan.DurTmm, UseEnergyMeter, AcALim, WMax/WMaxInRtg und PCC-Limits/Fallbacks. WMax nicht mit bestehendem maximalen Ladeleistungsparameter WMaxIn verwechseln. Installer-/Netzwerk-/Firmwareaktionen und Zugangsdaten ausdrücklich getrennt; editable/Confirmed allein erzeugt keinen Setter.
- [ ] E07 – Aktuelle Wallbox-Verfügbarkeitsbefunde behalten: Frequenzkanal Measurement.GridMs.Hz nicht angeboten; alternativer Gesamtenergiekanal fehlt, primärer ChaSta-Zähler verfügbar. Gesundheit/Sitzungsenergie/mehrere Ereigniscodes haben Werte, werden aber derzeit wegen Zeitstempel ausgefiltert. In bestehende Zeitstempeluntersuchung einbeziehen und später unter natürlichen Lade-/Ruheübergängen gezielt prüfen; kein neuer wiederkehrender Test geplant.

### Weitere aktive Aufgaben

- [ ] Wallbox `measurements/vehiclestatuscode` auf Andreas’ Wunsch vom 12.10.2026 aus ADVANCED in die Standard-/Basisgruppe übernehmen. Topic und Werte erhalten; Verfügbarkeit bei deaktivierten Advanced-Kanälen prüfen. Noch nicht implementiert.

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

## 2026-10-11 – Vier HIGH-Trivy-Befunde im Laufzeit-Image behoben

- Andreas beauftragt die Behebung des fehlgeschlagenen amd64-Scans: msgpack GHSA-6v7p-g79w-8964, setuptools CVE-2025-47273 und urllib3 CVE-2026-97687/CVE-2026-97689. Lokale Paket-/Vendor-Prüfung bestätigt: sämtliche betroffenen Versionen werden von pip 26.2.1 intern mitgeliefert; keine Bridge-Laufzeitabhängigkeit benötigt diese Pakete. Separates Installieren neuer Top-Level-Pakete würde die vendorten Kopien nicht ersetzen.
- Dockerfile prüft nach Installation pip check, entfernt danach pip und das stdlib-ensurepip samt eingebettetem pip-Wheel. Runtime-Abhängigkeiten bleiben identisch gepinnt. CI prüft auf beiden Architekturen zusätzlich das Fehlen dieser Build-Werkzeuge. README dokumentiert Paketänderungen durch Image-Neubau.
- Beide Images lokal gebaut (arm64 und amd64), CLI-Version und check-config erfolgreich, sämtliche 205 Offline-Tests im nativen arm64- und emulierten amd64-Container bestanden. Automatische Versionsübernahme beim Docker-Build dabei bestätigt.
- Offizielles Trivy 0.75.0 temporär geladen und SHA-256-Prüfsumme verifiziert. Nachscan beider Images mit severity HIGH,CRITICAL / ignore-unfixed / exit-code 1: jeweils 0 gefilterte Schwachstellen und 0 Secrets, Exit 0. Niedrigere Schweregrade und Befunde ohne Fix damit nicht pauschal ausgeschlossen. Reports außerhalb des Repositorys gespeichert.
- Vollständiger Linter und 205 Host-Offline-Tests bestanden. Kein Produktionswechsel, Gerätezugriff, Commit, Push oder Release. GitHub-Lauf und ausgerolltes Release-Image weiterhin separat prüfen.

## 2026-10-11 – Betriebsgrenzen und gezielte Ausfallprüfungen

- Auftrag: verfügbare Intervalle/Timeouts erfassen, vorhandene Tests prüfen und fehlende automatisierte Prüfungen ergänzen. Im Worktree vorhandene Build-/Release-/Versionsänderungen bleiben unberührt.
- Keine private Zielhost-Konfiguration im Worktree vorhanden. Neues lesendes Modul operational_limits gibt nach normaler Konfigurationsauflösung ausschließlich erlaubte Betriebsgrenzen aus; keine Geräte-/Brokerabfragen, Adressen, Zugangsdaten oder private Identitäten. Auf dem aktualisierten Zielhost ausführen und externe Alarmbedingungen/Wartezeiten bereitstellen.
- Drei neue Tests: geheime Konfigurationswerte nicht ausgegeben; zwölf Stunden virtuelle Teilantworten mit unabhängiger Quelle, Ablauf kritischer Werte, retained Beobachtung und Erholung; 60 wiederholte Timeouts mit begrenzten Backoff-Abständen und serieller Wiederaufnahme. Keine echte mehrstündige Last-/Ressourcenprüfung daraus ableiten.
- Ablauf und Default-Tabelle in docs/OPERATIONAL_ACCEPTANCE.md. Kein zusätzliches Logging, keine Grenzänderung, kein Live-Ausfall oder Gerätebefehl ausgeführt. Zielhost-Werte, Alarmabgleich und manuelle Geräteausfallprüfung bleiben offen.
- Abschluss: alle 206 Offline-Tests mit lokalen synthetischen Loopback-Servern bestanden. Vollständiger Linter über 112 Dateien: alle übrigen Prüfkategorien bestanden, Ruff/Formatierung scheitern an bereits vorhandenen Änderungen in version.py und test_bootstrap.py; neue Dateien Ruff-/Format-konform. Kein pauschal grüner Gesamt-Linter behauptet.

## 2026-10-12 – Fehlende Messwerte und Kanalgruppen geprüft

- Andreas meldet weiterhin fehlende inverter3-Werte für Leistung L1 und Netzspannung L1 sowie Wallbox-Gerätezustand und Frequenz. Bestehende Evidenz: Register 30777/30783 lieferten beim ersten begrenzten Lesen SMA-NaN; Tagesvergleich und tatsächliche Firmware-Unterstützung bleiben offen. Wallbox-Frequenz fehlte im geprüften Live-Inventar; Gerätezustand wurde wegen alten Quellzeitstempels ausgefiltert. Kein neuer Live-Test durchgeführt.
- Geklärt: Home-Manager-Anlagenzeit ist Register 30193 auf Unit 2, Unix-Zeit in UTC-Sekunden; keine Betriebsdauer.
- Aktuelle Advanced-/Diagnostics-Filter anhand Profile, Adapter, Runtime und Publisher vollständig inventarisiert. Quellenstatus der Messadapter bleibt bei abgeschalteter Diagnose erhalten; zusätzliche Statuswerte der Befehlsquellen werden dagegen ausgefiltert. Interne Temperatur, Wallbox-Gerätezustand und Frequenz gehören aktuell zur Basisgruppe.
- Offizielle Homie-4-Spezifikation und openHAB-Homie-Dokumentation konsultiert: kein standardisiertes Advanced-Property-Attribut für die openHAB-Anzeige. Projektfilter entfernen Discovery/Topics, statt das openHAB-Advanced-Kennzeichen zu setzen.
- Offen: Gruppen gemeinsam bereinigen; doppelte Typ-/Seriennummern und Rohwerte prüfen, Anlagenzeit sinnvoll darstellen, Frequenz-Unterstützung und Zustandszeitstempel getrennt klären. Keine Runtime-, Profil-, Konfigurations- oder Geräteänderung; deshalb keine neuen Laufzeittests.

## 2026-10-12 – Wallbox-Fahrzeugstatuscode und SEMP-Steuerwerte

- Andreas fordert den Fahrzeugstatuscode als Standardkanal; als aktive Aufgabe aufgenommen, Runtime unverändert.
- Drei SEMP-Steuerwerte geprüft: ChrgActCnt, WSptMaxNom und WSptMinNom liegen als Rohwerte vor. Referenzsnapshot zeigt 0, 0 und -100. Exakte Zählsemantik, Normierungsbasis und Vorzeichenkonvention bleiben unbestätigt; kein PV-/Netzanteil daraus ableiten. Der Adapter veröffentlicht diese Werte als Float ohne Einheit und ohne Setter. Offizielle Websuche nach den exakten Kanalnamen ohne Ergebnis.

## 2026-10-12 – Wechselrichter-Registerabgleich vorgemerkt

- Andreas beauftragt zunächst die Aufnahme zweier TODOs: Typ-/Leistungsregister für inverter1 und inverter2 modellgenau prüfen und bestätigte Entsprechungen nachziehen; außerdem alle drei Modbus-Dokumentationen systematisch gegen die aktuellen Topics/Profile abgleichen.
- Entscheidung geklärt: `measurements/type` soll ausdrücklich erhalten bleiben. Die zuvor erwogene Bereinigung dieses Altkanals wird nicht verfolgt.
- Nur Aufgaben und Entscheidung dokumentiert; keine Registerrecherche, Profil-/Runtimeänderung, Geräteabfrage oder Tests durchgeführt.

## 2026-10-12 – SEMP-Steuersemantik als aktive Aufgabe

- Andreas möchte ChrgActCnt, WSptMaxNom und WSptMinNom näher verstehen. Eigene aktive Prüfaufgabe mit Zählsemantik, Einheit, Bezugsleistung, Vorzeichen und tatsächlicher Wirksamkeit ergänzt.
- Nur TODO ergänzt; keine neue Recherche, Geräteabfrage oder Runtimeänderung durchgeführt.

## 2026-10-12 – Anlagenzeit in openHAB darstellen

- Andreas beauftragt die TODO-Aufnahme: Unix-Sekunden der Anlagenzeit in der Bridge behalten und Datum/Uhrzeit einschließlich Europe/Berlin-/Sommerzeitdarstellung in openHAB umsetzen. Anzeige-Transformation und DateTime-Item je nach Verwendung unterscheiden.
- Nur Aufgabe dokumentiert; keine Bridge- oder openHAB-Änderung durchgeführt.

## 2026-10-12 – Vollständiger dokumentarischer Modbus-/Topic-Abgleich

- Passende offizielle V13-/V13-/V16-Archive für STP8.0-3AV-40, SBS3.7-10 und SB4.0-1AV-41 gegen die gebündelten Profile geprüft; lokale SHA-256 stimmen mit REGISTER_VALIDATION überein. Offizielle SMA- und openHAB-Modbus-Dokumentation konsultiert. Ältere -40-Liste nicht für den -41 verwendet.
- Vollständiges technisches Registerinventar in docs/modbus-topic-audit.csv: 527/450/390 eindeutige SMA-Adressen, davon 508/424/378 lesbar und 17/14/18 bereits gemappt. Somit 491/410/360 lesbare Adressen ohne Profil-Topic. 126 Storage-Quellzeilen ohne numerische SMA-Adresse in separater SunSpec-Liste erhalten. Duplikate derselben Adresse geprüft und zusammengeführt; alternative Adressen nicht zusammengezählt oder als unabhängige Sensoren behauptet.
- Alle 50 bestehenden Properties auf dokumentierte Adresse, Typ, Registerlänge und FIX-/TEMP-Skalierung geprüft. Sunny-Boy-Typ und identity/model teilen eine Adresse; deshalb 49 gemappte Adressen. Storage-kWh-Sonderfall ausdrücklich erhalten; Einheitenlücken, Enums und tatsächliche Geräteunterstützung bleiben getrennte Prüfungen.
- Konkrete Lücken: Typ-Alias/Leistungsgrenzen für inverter1/2, AC-Ströme/Frequenz/Blind-/Scheinleistung, Storage-AC-Leistung/Batteriestrom/-spannung/-energie, Sunny-Boy-DC-B, Betriebszeiten, Ereignisse und zahlreiche lesbare Konfigurationen. Modellgenaue Typ-/Leistungsregister 30053/30231/30233 dokumentiert, Profilergänzung weiterhin offen.
- Ziel geklärt: vollständige verifizierte Lese-/Konfigurationsabdeckung; Kanalgruppen werden anschließend gemeinsam entschieden. RW ist keine automatische Schreibfreigabe. WO und Zugriffssteuerung sind ausdrücklich inventarisiert; keine Geheimnisse als Telemetrie. Keine Runtime-/Profil-/Filteränderung, keine Geräte-/Brokerabfrage oder Live-Schreibaktion. Home-Manager-NSD bereits dokumentarisch vollständig; eCharger ohne passende vollständige Modbus-Liste separat gegen API/SEMP prüfen.
- Validierung: vollständiger Linter über 116 Dateien bestanden; alle 208 Offline-Tests einschließlich synthetischer Loopback-Protokollserver bestanden. Erster Sandbox-Testlauf an vier lokalen Socket-Bindungen gescheitert; vollständiger freigegebener Wiederholungslauf erfolgreich. git diff --check ohne Befund.

## 2026-10-12 – Produktionsabhängiger Modbus-Verfügbarkeitstest

- Andreas präzisiert den Umfang: zunächst alle dokumentierten lesbaren Register während PV-Produktion einmal auf tatsächliche Werte prüfen, danach eine sinnvolle Smart-Home-Auswahl treffen. Nicht sämtliche dokumentierten Adressen automatisch als Topics implementieren. Frühere Vollständigkeitsentscheidung damit für die Topic-Auswahl präzisiert; vollständiges Inventar bleibt als Prüfgrundlage erhalten.
- Sunny Boy SB4.0-1AV-41 besitzt laut offizieller SMA-Betriebsanleitung zwei unabhängige MPP-Eingänge; ob beide bei Andreas belegt sind, bleibt offen. Eingangs-B-Register werden daher geprüft, nicht als angeschlossene Hardware behauptet.
- Gegen 07:51 Europe/Berlin beide PV-Wechselrichter lesend geprüft: Modell/Firmware/Seriennummern-Gates bestanden, jeweils gültige 0 W auf Register 30775. Kein Vollscan gestartet, da beide noch nicht produzierten. Keine Writes, MQTT-Verbindungen oder Geräteänderungen.
- Privater einmaliger Prüfer und Rohresultate unter private/verification/modbus-availability-2026-10-12/ vorbereitet; nicht in Git/Docker, keine Originalreferenzen verändert. FC04-Einzelregisterlesung, 250 ms Pause, begrenzte Timeouts, einmalige Startmarkierung; WO und Zugriffssteuerung 43090 ausgelassen. Sieben synthetische NaN-/Null-/signed-/String-Klassifikationsprüfungen bestanden.
- Andreas autorisiert anschließend ausdrücklich die automatische Prüfung alle 30 Minuten ausschließlich heute und genau einen Vollscan bei positiver Leistung beider PV-Geräte. Chat-Heartbeat „Modbus-Verfügbarkeit bei PV-Produktion prüfen“ eingerichtet, Tagesende begrenzt. Bei 0 W still; Ergebnis/Fehler melden und nach dem Scan pausieren. Profilerweiterung und Gruppenentscheidung bleiben offen.

## 2026-10-12 – Einmaliger Produktionsscan abgeschlossen

- Autorisierter Heartbeat meldet vor dem Scan PV-Produktion: Tripower 203 W, Sunny Boy 52 W. Scan 08:25–08:31 Europe/Berlin, danach weiterhin positive Leistung auf beiden Geräten. Modell/Firmware/Seriennummern-Gates für alle drei Geräte bestanden. Einmalige Startmarkierung erhalten; Automation nach Abschluss pausiert.
- Alle 1367 Geräte/Register-Paare erfasst: 1307 FC04-Leseabfragen, 57 WO und dreimal Zugriffssteuerung 43090 bewusst ausgelassen. Tripower 457 nutzbare Rohantworten/50 NaN; Storage 218/203 NaN/zwei nicht dekodierbare Strings; Sunny Boy 197/180 NaN. Insgesamt 105 gültige Nullwerte enthalten. Keine Modbus-Ablehnung, Transportfehler oder ungetesteten Zeilen. Keine Writes, MQTT-Verbindungen, Profil-/Runtime-/openHAB-Änderungen.
- Sunny-Boy-L1-Lücken geklärt: Phaseinstellung 40183 liefert 329, laut passender V16-Liste L3. L3-Register 30781/30787/30981 liefern Leistung/Spannung/Strom; jeweilige L1/L2-Adressen NaN. Künftige Mappings müssen die L3-Zuordnung ausdrücklich behandeln; bestehende L1-IDs und Historie erhalten, nicht umdeuten.
- Sunny-Boy-Eingang A liefert Werte, Eingang B 30957/30959/30961 jeweils gültige 0. Aus diesem Snapshot keine physische Stringbelegung ableiten. Storage-Batteriestrom/-spannung, Lade-/Entladeenergie, Frequenz aller drei Geräte und zahlreiche weitere sinnvolle Kandidaten vorhanden.
- Öffentliche vollständige Ergebnismatrix und englischer Bericht in docs/ gespeichert, ausschließlich technische Metadaten/Verfügbarkeit; private Rohwerte bleiben ignoriert. 433 NaN und zwei String-Dekodierungslücken aus der ersten Topic-Kandidatenliste ausgeschlossen, aber nicht als in allen Betriebszuständen dauerhaft ununterstützt behauptet. 872 verfügbare Rohantworten sind keine Empfehlung für 872 Topics. Gruppen und konkrete kleine Auswahl gemeinsam offen.
- Abschlussvalidierung: vollständiger Linter über 118 Dateien bestanden, alle 208 Offline-Tests bestanden, git diff --check ohne Befund. Öffentliche Matrix auf 1367 eindeutige Schlüssel, richtige Ergebniszählung, NaN-Ausschluss und Erhalt gültiger Nullwerte geprüft. Keine neue Profil-/Setter-/openHAB-Abnahme daraus abgeleitet.

## 2026-10-12 – Umsetzungspakete aus dem Scan konkretisiert

- Andreas fragt nach Startreihenfolge, offenen Umsetzungsfragen und expliziter Battery-Abdeckung. Bestätigt: inverter2 / SBS3.7-10 wurde vollständig mitgeprüft, 423 Leseabfragen und 218 Antworten ohne NaN einschließlich 26 Nullwerten; 203 NaN und zwei String-Dekodierungslücken. Die PV-Produktion war nur Startbedingung für den gemeinsamen Scan.
- Scanbefunde in zehn einzelne aktive Pakete M01–M10 überführt und vollständige Ergebnismatrix verlinkt. Vorschlag: erst Sunny-Boy-Phasenmapping und gewünschte Typ-/Grenzkanäle, danach kleine AC-/Batteriemesswertauswahl; Energie-/PF-/Diagnosefragen separat. Gruppen und Umfang neuer Topics gemeinsam entscheiden.
- Offene Umsetzungsfragen ausdrücklich erhalten: installationsabhängige Phase ohne feste Modell-L3-Annahme, konkrete neue Topics/Linkmigration, Batterie-Energieeinheiten, PF-Konventionen, Stringbelegung B und Zustandsspezifik ausgeschlossener Werte. Keine Profil-/Runtime-/Geräteänderung für diese Priorisierung durchgeführt.

## 2026-10-12 – Sunny-Boy-L2-/L3-Kanäle umgesetzt

- Andreas beauftragt M01 einschließlich L2-Erweiterung. Sechs dateibasierte RO-Mappings für Leistung/Spannung/Strom ergänzt; keine L1-Änderung oder modellabhängige Adapterlogik. Nicht verfügbare Phasen bleiben ohne neuen Messwert, letzte retained Beobachtung gegebenenfalls erhalten.
- Leistung/Spannung nutzen unverändert den bisherigen 3-Sekunden-Block; L2/L3-Strom erhält einen kleinen FC04-Block mit vier Registern im 5-Sekunden-Takt. Readiness weiterhin über Status; optional abgeschaltete Advanced-/Diagnostics-Filter entfernen die neuen Basismesswerte nicht. Deutsche/englische Labels ergänzt.
- Alle alten Properties/Poller gegen unabhängigen Vorher-Snapshot identisch; sechs neue Mappings auf Adresse, Typ, Länge, Skalierung und Unit gegen offizielle Inventardaten geprüft. Gezielte 19 Profil-/Phasen-/Übersetzungstests bestanden. Vollständiger Linter über 119 Dateien und alle 211 Offline-Tests bestanden; git diff --check ohne Befund. Keine Geräteabfrage, Deployment-, MQTT-/openHAB- oder Live-Abnahme für diese Änderung durchgeführt.
- Separate Compose-Paritätsprüfung bestanden: beide Standalone-Dateien mit identischen Laufzeiteinstellungen und geprüften Overrides.

## 2026-10-12 – M02–M04 und Abgrenzung Home Manager/Wallbox

- Andreas beauftragt Typ/Leistungsgrenzen für inverter1/2 sowie Frequenz/verfügbare Phasenströme und Storage-AC-/Batteriestrom/-spannung. 16 weitere dateibasierte RO-Mappings umgesetzt; vorhandene Definitionen/Poller unverändert. Typ/Grenzen wie Sunny Boy Advanced, Messwerte Basic-Default. Keine neue ENV, Adapterlogik, Setter oder Geräteschreibaktion.
- Quellen-/Scanabgleich aller neuen Adressen erfolgreich; signierte Werte erhalten, Null gültig, NaN verworfen. Gezielte 34 Profil-/Erweiterungs-/Phasen-/Übersetzungs-/Home-Manager-Tests sowie alle 214 Offline-Tests bestanden. Vollständiger Linter über 120 Dateien, separate Compose-Parität und git diff --check bestanden.
- Home-Manager-NSD-Profil/Testbestand geprüft: 16 feste Eigenschaften plus 245 Zuordnungsslots und 16 delegierte Templates decken bekannte lesbare Dokumenteinträge ab; vollständiger Live-Verfügbarkeitscheck bleibt offen. Wallbox nutzt API/SEMP/Portal; keine passende vollständige Modbus-Liste in den vorhandenen Quellen. Separate aktive Aufgaben ergänzt, keine zusätzlichen Geräteabfragen dafür vorgenommen.

## 2026-10-12 – Markdown-Tabellenlint korrigiert

- Gemeldete MD060-Fehler in drei Modbus-Dokumenten behoben: vier Tabellen-Trennzeilen auf den kompakten Stil angepasst (`--:` statt `---:`). Rechtsausrichtung und Tabelleninhalte erhalten.
- Vollständiger Linter über 120 Dateien und alle 214 Offline-Tests bestanden. Erster Testlauf durch vier sandboxseitig gesperrte Loopback-Bindungen fehlgeschlagen; freigegebener Wiederholungslauf erfolgreich. `git diff --check` ohne Befund.

## 2026-10-12 – Systematischer Wallbox-API-/SEMP-Topic-Abgleich

- Andreas beauftragt den vollständigen Abgleich der angebotenen API-/SEMP-Kanäle gegen Topics. Originale Referenzkataloge und tatsächliche Runtime-Definitionen einschließlich Fallbacks, Kanalfilter, Quelleneigentum und bestehender Befehls-Allowlist geprüft. Aktueller einmaliger Abruf beider aktivierter lokaler Leser mit bestehenden TLS-/Identitäts-Gates erfolgreich; kein Portalabruf, MQTT oder Geräteschreibzugriff. Nur bereinigte Metadaten/Verfügbarkeitskategorien gespeichert, keine authentifizierten Rohantworten/Tokens.
- Aktuell 85 API-Parameter (Namensbestand wie Referenz, alle Confirmed), 44 API-Mess-/Setpointkanäle, 25 SEMP-Parameter und 19 Standard-SEMP-Feldpfade. API: zwölf direkte Parameter-Mappings, Firmware-Fallback, OutPhs via SEMP, zwei Identitäts-Gates, sieben bewusste Standort-/Zugangsausschlüsse und 62 sonstige ungemappte Parameter. SEMP: sämtliche 24 nicht privaten Kanäle mit Mapping; bei API an werden acht Einstellungskanäle von API statt SEMP bereitgestellt.
- API-Messbestand: sieben direkte/ vier Basis-Fallback-/ sieben nur via SEMP gemappte und 26 ungemappte Kanäle. Zwölf ungemappte Kanäle mit derzeit akzeptiertem Zeitstempel: drei Phasenwirkleistungen, vier Scheinleistungswerte, vier Blindleistungswerte und GI1. Weitere 14 nicht frisch akzeptiert (13 mit Wert/nicht akzeptierter Zeitangabe, einer ohne Wert); nicht pauschal dauerhaft ausschließen. Antwort enthält keine expliziten Messunits.
- Vorhandene Frequenz-Property ohne angebotenen API-Kanal bestätigt; alternative TotWhIn-Quelle fehlt, primäre ChaSta-Gesamtenergie vorhanden. Bestehende Session-/Health-/Ereignis-Lücken bleiben Zeitstempel-/Semantikfragen. Reader liefert 19/20 API- und 11/18 SEMP-Ausgabeschlüssel mit Wert; keine Broker-/physische Ladeabnahme daraus ableiten.
- 13 Standard-SEMP-Status-/Capability-/Grenz-/PowerInfo-Felder noch ohne Topic-Mapping; Identitätsprüfung/Privatfelder separat inventarisiert. Kein pauschaler Modbus-Fähigkeitsausschluss aus fehlender Registerliste. Befunde in E01–E07 als aktive Folgepakete aufgenommen; keine Runtime-, Topic-, Filter- oder Setteränderung für den Audit.
- Abschlussvalidierung: vollständiger Linter über 123 Dateien und alle 214 Offline-Tests bestanden; git diff --check ohne Befund. 156 eindeutige Kanalmatrixzeilen (154 aktuell angebotene Einträge plus zwei konfigurierte, nicht angebotene Quellen), zwölf frische ungemappte API-Einträge, 19 Standardfelder und Redaktion bewusster Ausschlüsse zusätzlich geprüft. Keine neuen Topics oder Setter implementiert.

## 2026-10-12 – Wallbox-Phasenwirkleistung ergänzt

- Andreas gibt die vorgeschlagene nächste Ergänzung frei. Offizielle WebUI-Assets geprüft: drei GridMs.W.phs*-Kanäle SCALAR, unit 18 laut Wörterbuch W, Formatter nutzt Number(value) ohne Rohmultiplikator. Quellenhashes im Auditbericht; keine Originaldateien verändert oder ganze Assets veröffentlicht.
- Drei zusätzliche API-Messwerte `powerl1`/`powerl2`/`powerl3` Float/W ohne Setter ergänzt. Weiterhin nur bestehende Katalog-/Live-Requests, keine zusätzliche Abfrage. API bleibt Eigentümer auch mit SEMP; bestehende Gesamtladeleistung unverändert, keine Summenersatzberechnung. Basis-Default wie vorhandene API-Phasenmesswerte; Readiness unverändert.
- Messunit explizit W oder ohne Unit nur EVC22-3AC-20 / 2.6.37.R; Unit-Konflikte und unbekannte Firmware ohne Unit bleiben unavailable. Negative, gebrochene und echte Nullwerte unverändert, NaN/missing/stale nicht veröffentlicht. Keine Setter, Phasensteuerung, Geräteschreibaktion oder MQTT-/openHAB-Änderung.
- Gezielte 37 Protokoll-/Phasen-/Filtertests und alle 217 Offline-Tests bestanden. Vollständiger Linter über 124 Dateien, separate Compose-Parität und git diff --check bestanden. Vorheriger lesender Audit belegt angebotene Kanäle, nicht die Veröffentlichung durch die neue Bridge. E02–E07 bleiben offen.

## 2026-10-12 – Vorab-Commit und vollständiger Home-Manager-Lesetest

- Auf Andreas’ Wunsch zuerst den gesamten vorherigen Stand lokal als `1828a35` committet (Wallbox-Kanalaudit/Phasenwirkleistung), private Daten ausgeschlossen; kein Push. Danach erst Home-Manager-Check gestartet.
- Modbus-TCP und Advanced-Inventar waren lokal explizit aktiviert; keine ENV-/Adapteraktivierung geändert. Home-Manager-Modell/Klasse/Hersteller/beide Serienregister vor Anlagen-/Tabellenabfragen verifiziert. Alle 16 festen Eigenschaften gültig, darunter drei echte Nullwerte. Alle 245 Zuordnungsslots in neun Blöcken gelesen, drei gültig zugeordnete Geräte komplett mit je 16 Parametern gelesen.
- Delegiert jeweils nur 30233 gültig, 45 übrige Werte SMA-NaN. Keine Modbus-Ablehnung, unbekannten Enums, Verbindungsfehler oder ungetesteten Profileinträge. Ursache der NaN offen; kein zusätzlicher Controller, keine Grid-Guard-Anmeldung, Geräteeinstellung, MQTT oder openHAB geändert. Öffentliche Ergebnismatrix enthält ausschließlich technische Metadaten/Status, keine Werte oder privaten Identitäten.
- Alle 25 in diesem Arbeitsabschnitt neu ergänzten Topics zur Advanced-/Basis-Auswahl zusammengestellt und gegen den früheren Profilstand/aktuellen API-Reader geprüft. Sechs bisher Advanced, 19 bisher Basis. Checkboxen markieren Gruppenwahl, nicht Aufgabenabnahme; noch keine Gruppenänderung vorgenommen.

- Abschlussprüfung: alle 217 Offline-Tests, vollständiger Linter über 126 Dateien und git diff --check bestanden; 64 eindeutige Unit/Register-Beobachtungen und 25 eindeutige Geräte/Topic-Auswahleinträge geprüft.

## 2026-10-12 – Deploy-Vorbereitung und Release-Auftrag

- Advanced-/Basis-Auswahl bestätigt: sechs Typ-/Leistungsgrenzen Advanced, 19 neue Messwerte Basis; entspricht der Implementierung.
- Alle 217 Offline-Tests auf dem Host und im lokalen Container ohne Netzwerk bestanden; vollständiger Linter und Compose-Parität bestanden. Container-Konfiguration ohne aktivierte Quellen, unprivilegierter Benutzer und Entfernung der Build-Installer geprüft.
- „Bauen“ zunächst als lokalen Docker-Build interpretiert und ausgeführt. Andreas stellt klar: Stand committen, taggen und GitHub bauen lassen. Lokales Image ist nicht die gewünschte Deploy-Quelle; Release-Workflow prüft beide Zielarchitekturen und Security-Gates vor GHCR-Publikation.
- Nächster freier Patch-Tag nach lokalem und entferntem v0.3.2 ist v0.3.3. Deploy-Prüfliste in docs/MAC_TEST.md ergänzt: 25 neue Topics, Gruppen/Units, PV-/Batterie-/Ladebetrieb, Home-Manager-NaN, bestehende Historie und Neustart. Live-Abnahme bleibt offen.

## Auswahl der 25 neu ergänzten Topics

Diese Auswahl betrifft die seit Commit `b8b5915` in diesem Arbeitsabschnitt ergänzten Messkanäle; vorhandene ältere Topics sind nicht Teil der Liste. Der Home-Manager-Check fügt keine neuen Topics hinzu. Alle aufgeführten Eigenschaften sind read-only.

`[x]` bedeutet Advanced, `[ ]` bedeutet Basis. Andreas hat diese Auswahl am 12.10.2026 bestätigt: T01–T03 und T08–T10 bleiben Advanced, die übrigen 19 Messwerte bleiben Basis. Die Implementierung entspricht bereits dieser Entscheidung; keine Codeänderung erforderlich. Die Auswahl ist keine Live-Abnahme-Markierung.

Topic-Suffixe werden unter `homie/<konfigurierte Homie-ID>/` veröffentlicht. Die IDs bleiben als Referenz für spätere Änderungswünsche erhalten.

### inverter1 – Tripower

- [x] T01 – `measurements/type` – Gerätetyp
- [x] T02 – `measurements/maxpower` – Nennwirkleistung WMaxOutRtg (W)
- [x] T03 – `measurements/setmaxpower` – Eingestellte Wirkleistungsgrenze (W)
- [ ] T04 – `measurements/frequency` – Netzfrequenz (Hz)
- [ ] T05 – `measurements/currentl1` – Netzstrom Phase L1 (A)
- [ ] T06 – `measurements/currentl2` – Netzstrom Phase L2 (A)
- [ ] T07 – `measurements/currentl3` – Netzstrom Phase L3 (A)

### inverter2 – Storage

- [x] T08 – `measurements/type` – Gerätetyp
- [x] T09 – `measurements/maxpower` – Nennwirkleistung WMaxOutRtg (W)
- [x] T10 – `measurements/setmaxpower` – Eingestellte Wirkleistungsgrenze (W)
- [ ] T11 – `measurements/frequency` – Netzfrequenz (Hz)
- [ ] T12 – `measurements/currentl1` – Netzstrom Phase L1 (A)
- [ ] T13 – `measurements/activepower` – Leistung (W)
- [ ] T14 – `measurements/batterycurrent` – Batteriestrom (A)
- [ ] T15 – `measurements/batteryvoltage` – Batteriespannung (V)

### inverter3 – Sunny Boy

- [ ] T16 – `measurements/powerl2` – Leistung Phase L2 (W)
- [ ] T17 – `measurements/voltg2` – Netzspannung Phase L2 (V)
- [ ] T18 – `measurements/currentl2` – Netzstrom Phase L2 (A)
- [ ] T19 – `measurements/powerl3` – Leistung Phase L3 (W)
- [ ] T20 – `measurements/voltg3` – Netzspannung Phase L3 (V)
- [ ] T21 – `measurements/currentl3` – Netzstrom Phase L3 (A)
- [ ] T22 – `measurements/frequency` – Netzfrequenz (Hz)

### Wallbox

- [ ] T23 – `measurements/powerl1` – Leistung Phase L1 (W)
- [ ] T24 – `measurements/powerl2` – Leistung Phase L2 (W)
- [ ] T25 – `measurements/powerl3` – Leistung Phase L3 (W)

## 2026-10-12 – Markdown-CI-Korrektur

- MD060-Fehler in den Tabellen des eCharger-Audits und Home-Manager-Verfügbarkeitsberichts behoben: rechtsbündige Trennzellen auf den konfigurierten kompakten Stil gekürzt. Inhalte unverändert.
- Validierung: vollständiger Linter über 126 Dateien einschließlich Markdown und alle 217 Offline-Tests bestanden. Vier lokale MQTT-Testserver benötigten einen Lauf außerhalb der Sandbox; keine Live-Geräteverbindung. `git diff --check` bestanden.

## 2026-10-12 – Kurze Fahrzeugstatusanzeige im Garagenwidget

- Anschlusszeile zeigt bei bereiter Messquelle jetzt „Gesperrt“ und „Ladefehler“ statt „Anschluss unbekannt“. Unbekannte Zustände/nicht bereite Quelle zeigen kurz „Status unbekannt“. Bestehende Anschlussanzeigen und orange Farbe bleiben erhalten; keine Behauptung einer Kabelverbindung aus einer Sperre.
- Kanonische YAML und nativer MainUI-Export aktualisiert. Offizielle openHAB-Dokumentation für Widget-Ausdrücke konsultiert.
- Validierung: Linter über 126 Dateien, Exportparität und alle 217 Offline-Tests bestanden. Vier lokale MQTT-Testserver benötigten Ausführung außerhalb der Sandbox. Keine Geräteaktion oder Installation geändert; tatsächliche iPhone-Anzeige nach Übernahme noch offen. Bedeutung des kurzzeitigen Fahrzeugstatus „Gesperrt“ bleibt ohne gleichzeitige Rohcode-/Freigabebeobachtung offen.

## 2026-10-12 – Sunny-Boy-DC-Eingang B vervollständigt

- Andreas möchte beide dokumentierten MPP-Eingänge abbilden, unabhängig von momentaner Belegung. Drei Basis-Topics `measurements/currentbinput`, `voltagebinput`, `powerbinput` ergänzt; bestehende A-Kanäle unverändert.
- Register 30957/30959/30961: S32, Skalen 0.001 A / 0.01 V / 1 W, eigener FC04-Block mit sechs Registern alle 5 s. Gültige Null bleibt Messwert; SMA-NaN bleibt unveröffentlicht und beeinflusst die Readiness nicht. Keine physische Belegung behauptet.
- Diese Ergänzung erfolgt nach Tag v0.3.3 und ist darin noch nicht enthalten. Die bestätigte frühere 25er-Auswahl bleibt erhalten; folgende zusätzliche Auswahl ergänzt sie als Basis:

- [ ] T26 – inverter3 `measurements/currentbinput` – DC-Strom Eingang B (A), Basis
- [ ] T27 – inverter3 `measurements/voltagebinput` – DC-Spannung Eingang B (V), Basis
- [ ] T28 – inverter3 `measurements/powerbinput` – DC-Leistung Eingang B (W), Basis

- Prüfung nach Ergänzung: alle 217 Offline-Tests, vollständiger Linter über 126 Dateien, Compose-Parität und git diff --check bestanden.

- Andreas beauftragt Commit, neuen Release-Tag v0.3.4 und Push. Der Tag umfasst die DC-B-Ergänzung sowie den bereits committeten aktuellen Projektstand; Build/Scans/Publikation erfolgen im vorhandenen GitHub-Release-Workflow.

## 2026-10-12 – Neue Topics in MQTT Explorer geprüft

- Andreas meldet v0.3.4 online/healthy. Direkte rein lesende UI-Prüfung der 28 Ergänzungen: alle 22 Basis-Kanäle angekündigt, Einheiten/Datentypen/read-only/retained-Metadaten korrekt. 19 Zahlenwerte, drei Sunny-Boy-L2-Kanäle erwartbar nur Metadaten. L3 aktualisiert sich; DC-B liefert gültige Nullen. Kein NaN-Payload sichtbar.
- Sechs Advanced-Topics für Typ/Leistungsgrenzen bei inverter1/2 fehlen in den angekündigten Properties; passt zu deaktivierter Advanced-Gruppe. Andreas bestätigt beide Advanced-Schalter ausgeschaltet: Fehlen ist erwartbar, Frage gelöst. Keine Konfiguration geändert. Veröffentlichung bei aktiver Gruppe noch nicht geprüft.
- Alle vier geprüften Geräte ready. Storage liefert auch vorzeichenbehaftete AC-/Batteriewerte. Wallbox-Phasenleistung float/W mit Zahlenwerten/History vorhanden, aktuell wartend ohne Ladeleistung: Skalierung unter Last weiterhin prüfen. MQTT-Beobachtung ersetzt keinen gleichzeitigen SMA-/openHAB-Vergleich oder vollständige Neustart-Abnahme.
- Neue offene Beschriftungsfrage: DC-Eingang A/B haben derzeit gleiche Anzeigenamen; Topic-IDs eindeutig, sinnvoll wären phasenspezifische bzw. eingangsspezifische Beschriftungen. Keine Publish-/Delete-/Set-Aktion ausgeführt, private Rohwerte/IDs nicht in öffentliche Dokumentation übernommen.

## 2026-10-12 – DC-Anzeigenamen A/B vereinheitlicht

- Auf Andreas’ Freigabe Sunny Boy und Tripower mit eindeutigen DC-Strom-/Spannungs-/Leistungsnamen für Eingang A und B versehen. Deutsch: „DC-Strom Eingang A/B“, „DC-Spannung Eingang A/B“, „DC-Leistung Eingang A/B“; englische Profilnamen und Wörterbücher entsprechend ergänzt.
- Gegenprüfung: ausschließlich sechs Namen je Profil geändert, alle anderen Profilfelder identisch. Topic-IDs, Werte, Einheiten, Register und Pollintervalle erhalten; keine neue Quelle oder Gerätekonfiguration. Generische Übersetzungen für bestehende eigene Profile bleiben verfügbar.
- Neue Labels benötigen einen späteren Build/Deploy und frische Homie-$name-Metadaten; bei eigenen Profil-/Übersetzungsdateien entsprechend nachziehen. Live-Anzeige noch nicht geprüft.

- Validierung: alle 217 Offline-Tests, kompletter Linter über 126 Dateien und git diff --check bestanden. Discovery-Vergleich beider Modelle in Deutsch/Englisch: gleiche Topic-Menge, ausschließlich sechs DC-$name-Werte je Gerät geändert.

## 2026-10-12 – Weitere Kanäle umgesetzt

- Andreas beauftragt die bisher vorgeschlagenen Batterieenergie-/Betriebszeit-/Diagnosekanäle. Elf read-only-Ergänzungen: Storage-Lade-/Entladeenergie kWh (Basis), Betriebs-/Einspeisezeit aller drei Geräte in s (Advanced), Derating-Grund aller drei Geräte als Enum (Diagnostics). Andreas bestätigt die Aufteilung: Energie Basis, Zeiten Advanced, Derating Diagnostics. Gruppenfrage gelöst; Implementierung entspricht der Entscheidung.
- Quelle Energie Wh, Faktor 0.001; keine Übertragung des alten Storage-Ertrags-Sonderfalls. U64-Zero und Präzision erhalten, NaN nicht als Wert. Zeiten aus vorhandenen Yield-Blöcken, Derating aus vorhandenen Status-Blöcken; bestehende Intervalle/Mappings vollständig erhalten. Storage zusätzlich ein 8-Register-FC04-Block alle 60 s.
- Modellgenaue Derating-Codes aus V13/V16, Status-NaN 16777213 und U32-NaN ausgefiltert, unbekannte Codes unverfügbar. Alle neuen Eigenschaften optional für Readiness; keine Setter, Gerätekonfiguration oder Live-Brokeränderung.
- Gerätescan belegt Lesbarkeit; GUI-/Verlaufsvergleich von Energie/Zeiten einschließlich Reset-/Zählumfang und spätere MQTT-/openHAB-Abnahme offen. Alternativerträge, Schein-/Blindleistung und aktuell ungültige Ereignisregister bleiben außerhalb dieser Ergänzung.

- Endprüfung: alle 221 Offline-Tests, vollständiger Linter über 127 Dateien, Compose-Parität und git diff --check bestanden. Neuer Umfang: zwei Energie-, sechs Zeit- und drei Derating-Kanäle; noch kein Commit/Tag/Deploy.

## 12.10.2026 – Markdown-Lint-Parität

- Ursache geklärt: lokal war pymarkdownlnt 0.9.39 installiert, CI verwendet den Pin 0.9.40. Der gemeinsame Lint-Aufruf prüfte bisher keine installierten Versionen.
- Zwei MD060-Tabellentrenner korrigiert (`---:` → `--:` für den kompakten Stil); lokale Lint-Abhängigkeiten aktualisiert. Versionsprüfung gegen die Python-Pins ergänzt, damit veraltete Umgebungen mit Aktualisierungshinweis scheitern. README beschreibt die Aktualisierung.
- Validierung: ursprüngliche zwei Fehler mit 0.9.40 reproduziert; simulierte veraltete Version wird mit Exit 1 abgewiesen. Vollständiger Lint über 127 Dateien und alle 221 Offline-Tests bestanden (lokale Testserver außerhalb der Sandbox). Neuer gehosteter CI-Lauf bleibt offen.
