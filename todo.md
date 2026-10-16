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

- [x] 16.10.2026: Nach Andreas' Löschung der beiden Zeit-Items genau deren
  Anzeigen aus SMA-Plant entfernt: Wallbox-Energiebilanzzeit und zusätzliches
  Home-Manager-DateTime-Item. Nichtexistenz der Items vorher geprüft; Seite
  gesichert und Änderung zurückgelesen. Listenzähler Home Manager 9→8,
  Wallbox 42→41; bestehende ISO-Anlagenzeit bleibt erhalten. Browser bestätigt
  beide entfernten Anzeigen und neue Zähler. Andere Seiten unverändert.
- [x] 16.10.2026, 08:22: Drei leere Anzeigen gezielt lesend geprüft.
  Wallbox-Energiebilanzzeit: Item NULL ohne Link; zugehöriger optionaler
  Diagnosekanal fehlt im aktuellen Thing und ist in der bereinigten Konfiguration
  abgeschaltet. Home-Manager-DateTime-Hilfsitem ebenfalls NULL ohne Link;
  das verknüpfte ISO-Zeititem liefert aktuelle Werte. Wallbox-Gerätezustand ist
  korrekt verknüpft, aber beide Quellen liefern Code 307/OK mit unverändertem
  Gerätezeitstempel vom 11.09.2026. API und SEMP filtern ihn bei 180 Sekunden
  Altersgrenze; keine neuen Health-Messwerte werden veröffentlicht.
- [x] Entscheidung zu beiden unversorgten Zeit-Hilfsitems: von Andreas gelöscht,
  Anzeigen aus der Seite entfernt; vorhandene ISO-Anlagenzeit bleibt erhalten.
- [ ] Health als letzten bekannten Zustand mit Zeit-/Verfügbarkeitskennzeichnung behandeln erst nach
  Klärung seiner Änderungszeit-Semantik. Keine künstlichen Frischezeitstempel,
  keine globale Lockerung der Messwert-Altersgrenze. Noch nichts live geändert.
- [x] 16.10.2026: Nach Andreas' Item-Anlage openHAB ausschließlich lesend
  inventarisiert: elf neue Wechselrichter-Items mit jeweils passendem Channel
  gefunden (Roof sechs, Storage vier, Carport eins). Die bestehende private
  preview.csv um elf markierte Vorschläge ergänzt, nun 153 eindeutige Items.
  Vorherige 142 Zeilen bytegenau erhalten und CSV vorher gesichert.
  Vorschläge analog zu bestehenden Werten: Measurement mit Power/Voltage/Current,
  entsprechende bisherige Icons und pEveryUpdate30s. Tags, Zielgruppe und aktuelle
  InfluxDB-Regel einschließlich Zeit-/NULL-Filter gegen die Installation geprüft.
  CSV unabhängig geparst, neue Zeilen geprüft und Vorschau visuell kontrolliert.
- [x] Andreas hat die neuen CSV-Zeilen 144–154 freigegeben. Alle elf Items mit
  den geprüften Icons, Measurement/Power beziehungsweise Voltage/Current und
  pEveryUpdate30s versehen und einzeln zurückgelesen. Links, Einheiten, sonstige
  Metadaten und globale Persistence-Regeln erhalten.
- [x] SMA-Plant um genau elf Detailzeilen ergänzt: Roof sechs, Storage vier,
  Carport eins. Die drei Wertzähler zeigen jetzt 26/25/26. Vollständige
  Seitenabdeckung 147/147 SMA-Datenitems; andere Seiten und Widget-Definitionen
  unverändert. Aktuelle Item-Aufnahme, Änderungsplan, Sicherungen, Readback und
  Screenshots privat unter new-inverter-items/approved-application abgelegt.
  CSV-Zeilen als applied-confirmed markiert; vorherige 142 Zeilen erhalten.
  Aktuelles privates Inventar umfasst 153 Items (sechs Equipment-Gruppen,
  147 Datenitems). Vollständiger Linter über 200 Dateien und alle 418 Tests
  des aktuellen Arbeitsstands bestanden; Live-Readback separat geprüft.
  Erste Gesamtprüfung meldete lediglich umsortierte semantische Tags; lesender
  Vergleich ohne Reihenfolgeabhängigkeit bestätigt alle Änderungen ohne Fehler.
  Keine Schreibwiederholung, kein Item-State und kein Gerätebefehl.
- [x] sessionValue-Anzeigefehler lokal korrigiert: sessionText erhält fünf geprüfte
  Werte vom untergeordneten Label; kein Aufruf eines gleichrangigen fn-Helfers
  innerhalb der Textfunktion. Elf lokale Prüffälle ohne fn im Funktionskontext
  bestanden. Kanonisches YAML und generierter Import stimmen überein; Bedienung,
  Schreibsperren und übrige Widgetdefinition unverändert.
- [x] Andreas hat die korrigierte eCharger-YAML nach openHAB kopiert. REST-Readback
  stimmt vollständig mit der vorbereiteten Widgetdefinition überein. Nach
  Browser-Neuladen erscheint „Letzter Messwert: 0 kWh“ statt des sessionValue-
  Fehlers; Screenshot gesichert. Keine Ladebefehle zur Prüfung gesendet.
  Frühere REST-Übernahme war wegen editable=false erfolglos und wurde nicht
  wiederholt; Installation und Prüfung sind jetzt über den Dateipfad abgeschlossen.
  Speicherung künftiger Samples bleibt von dieser Anzeigeprüfung getrennt.
- [x] 16.10.2026: Gemeldeten CI-Timeout im Retained-Messwerttest behoben:
  bisheriges 0,5-Sekunden-Limit enthielt Publisher-Start, Manifest-Sicherung und
  Timer. Test prüft jetzt gezielt die Publikationsschleife mit kontrollierter
  Zeit, zwei begrenzten Zyklen und unveränderter letzter Beobachtung; retained
  Wert 10 sowie ready→alert werden explizit geprüft. Kein Produktcode geändert.
  200 gezielte Wiederholungen und alle 406 Offline-Tests erfolgreich.
  Neuer gehosteter CI-Lauf bleibt separat; genaue Ursache der ursprünglichen
  Runner-Verzögerung nicht unabhängig nachgewiesen.
- [x] 16.10.2026: Alle aktuellen Wechselrichter-Topics abgeglichen:
  [Vergleich mit Register-/Scanbelegen](docs/INVERTER_TOPIC_PARITY_2026-10-16.md),
  vollständige Matrix mit 44 verschiedenen Runtime-Properties.
  Tripower fehlten sechs Zuordnungen für Phasenleistung/-spannung trotz
  vorhandener gültiger Register im bereits gelesenen Block. Ergänzt als
  powerl1–3 und voltagel1–3; beide PV-Profile haben jetzt dieselben 33 direkten
  Properties. Keine zusätzlichen Tripower-Abfragen.
- [x] Storage um belegte L1-Leistung/-Spannung sowie Netzbezug/-Einspeisung
  ergänzt: vier Basic-Lesewerte, zwei neue kurze Fünf-Sekunden-Blöcke und
  bestehender AC-Leistungsblock erweitert. Gültige Null beim Netzleistungsscan
  belegt keine unabhängige Hausmessung; keine neue Bilanzquelle aktiviert.
  Inaktive Storage-Phasen und reine PV-/Batteriefunktionen bleiben begründete
  Unterschiede. Weitere Registerkandidaten bleiben separat zurückgestellt.
- [x] Profiländerungen gegen Energie-Fingerprint geprüft: eng auf exakt
  erkannte gebündelte Ergänzungen begrenzte Kompatibilität erhält die bisherigen
  Basen einschließlich des vorigen Sunny-Boy-L1-Fixes. Fremde Profiländerungen
  bleiben geschützt; keine Ledger-Umschreibung oder Rücksetzung.
  Validierung: alle 406 Offline-Tests und vollständiger Linter über 198 Dateien
  bestanden; generierter Topic-Katalog aktuell. Alte Profil-Energiesignaturen
  anhand festgehaltener Prüfsummen getestet; andere Mappingänderungen bleiben
  sichtbar und die Laufzeitprofile werden nicht verändert.
- [ ] Neue Wechselrichter-Topics nach Neubau/Installation in MQTT prüfen;
  Host-Profilkopien gegebenenfalls explizit aktualisieren. Kein Deployment,
  Live-Gerätezugriff oder openHAB-/Historieneingriff erfolgt.
- [x] 16.10.2026: Fehlendes `measurements/currentl1` bei inverter3/Carport
  lokal geprüft. Im gebündelten Profil `sma-sb4-0-1av-41` fehlt die
  Property `current-l1`; der Phasenstrom-Poller liest nur 30979–30982
  für L2/L3. Auch im generierten Topic-Katalog fehlt Sunny Boy currentl1.
  Kein ENV-Schalter ist die Ursache; Laufzeit und Geräte wurden nicht geändert.
- [x] 16.10.2026: Auf Andreas' Wunsch Sunny-Boy-Phasenstrom L1 ergänzt:
  `measurements/currentl1`, Basic, lesend, A. Offizielle V16-Liste erneut
  heruntergeladen, Prüfsumme abgeglichen und 30977/S32/FIX3 bestätigt.
  Stromblock auf sechs Register ab 30977 erweitert; L2/L3-Adressen und
  Fünf-Sekunden-Intervall bleiben erhalten. Ungültiges L1 bleibt nicht verfügbar
  und blockiert ready nicht. Topic-Katalog und Regressionen aktualisiert.
  Validierung: alle 402 Offline-Tests erfolgreich; vollständiger Linter erfolgreich.
  Vier lokale Testserver waren zunächst durch die Sandbox blockiert;
  Wiederholung mit erlaubten Loopback-Ports vollständig bestanden.
- [ ] L1-Ergänzung nach Neubau/Installation in MQTT prüfen; die inaktive Phase
  kann weiterhin SMA-NaN liefern. Kein Live-Zugriff oder Deployment ausgeführt.
- [ ] Nach dem heutigen Reset den nächsten Mitternachtsübergang und Folgetag prüfen:
  Tagesstatus, Hausverbrauch mit/ohne Wallbox sowie beide Sieben-Tage-Durchschnitte.
  Heute enthält nur die seit dem Neustart gemessene Zeit. Frühere Abnahme bleibt
  gültig; dies ist die gezielte Kontrolle des neuen Resets/Fensters.
- [ ] Frühere Abweichung von Hausverbrauch ohne Wallbox untersuchen: gespeicherter
  Tageswert lag über der Bilanz aus demselben Zählersnapshot. Grobe PV-Zähler und
  monotoner Akzeptanzschutz sind zu prüfen, kein weiterer Reset als Ersatz.
- [x] Historienarbeiten einschließlich Kopienachprüfung, Altitem-Prüfung und
  Beurteilung des gemischten PV-Tages-/Gesamtertragszeitraums von Andreas als
  erledigt bestätigt. Keine erneute Kopie, Löschung oder Historienkorrektur
  ausgeführt. [Ablauf](docs/INFLUX2_ITEM_MIGRATION.md).
- [x] 15 Zusatzkanäle einzeln bewertet und nachts um 21:39 lesend geprüft:
  vier Netzleistungen gültig, neun DC-Werte nicht verfügbar, zwei Carport-L1-Werte
  auf inaktiver Phase nicht verfügbar. Nach Andreas’ anschließender Entscheidung sechs DC-Strom-/Leistungskanäle
  mit bedingter Ersatznull umgesetzt: frische AC-Leistung 0 und Zustand OK.
  Spannungen bleiben nicht verfügbar. Lokal lesend um 21:58 bestätigt;
  Installation auf Produktion einschließlich Versionsprüfung von Andreas bestätigt.
  Kein eindeutiger Standby-Code verfügbar.
  [Einzelbewertung](docs/INVALID_VALUE_AUDIT.md).
- [ ] Tagesrückkehr der neun DC-Kanäle prüfen; Umgang mit alten retained Werten
  bei einzelnen ungültigen Kanälen für openHAB/UI festlegen. Keine weiteren
  Ersatznullregeln oder automatischen Historienänderungen.

## Produktionskonfiguration

- [x] smab.env.prod liegt als private Referenz vor; keine config.json und keine
  Host-Profilkopien laut Andreas. Git-Ausschluss für smab.env.* ergänzt.
- [x] Bereinigte smab.env.clean erstellt: 136 auf 64 aktive Variablen reduziert,
  Beschreibungen aus smab.example.env übernommen. Defaults mit Loader,
  gebündelten Profilen und Compose abgeglichen; aufgelöste Konfiguration offline
  gleich, besondere Präsenz-Semantik berücksichtigt, Werte/Quoting erhalten.
- [x] Bereinigte Datei auf dem Zielhost übernommen und Start geprüft, von Andreas
  als erledigt bestätigt. Private Konstanten/Zugangsdaten bleiben
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
- [x] 16.10., 07:02:00/07:02:55: Nach Andreas’ Meldung des Ladebeginns API/SEMP
  lesend geprüft. Beide laden bei rund 10,1 kW; Sitzungsenergie wieder frisch,
  von 0,952625 auf 1,108250 kWh (API). Zuwachs zum Gesamtzähler bis auf 0,125 Wh
  gleich. Keine Einstellungen geändert; exakter Startzeitpunkt nicht erfasst.
  [Evidenz](docs/ECHARGER_LIVE_CHECK_2026-10-15.md#next-charging-interval-2026-10-16).
- [ ] Andere Reset-Auslöser, möglicher zusätzlicher Reset exakt beim Ladebeginn
  und gewünschte Publikationssemantik für letzte/aktuelle Sitzung bleiben offen.
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
- [x] Storage-Frequenz und AC-Strom L1 technisch geprüft: identitätsgeprüfte
  Direktlesungen 22:07/22:08, 50,00–50,01 Hz, 1,570–1,577 A; bei 237,66 V
  und 360 W physikalisch plausibel. Keine unabhängige Kalibrierung behauptet.
- [x] Sunny-Boy-Phasenzuordnung technisch abgeschlossen: 40183 erneut 329/L3;
  L1/L2 bleiben nicht verfügbar. Tageswerte L3/DC B bereits früher geprüft und
  von Andreas verglichen. DC B ist lesbar; physische Stringbelegung aus Software
  nicht sicher feststellbar und nur bei weiterem Bedarf vor Ort zu klären.
- [ ] Weitere natürliche Derating-Zustände prüfen; „Keine Abregelung“ bereits belegt.
  AC-Batterieenergiegrenze ist gut belegt; Resetverhalten und Rückgabegrad bleiben
  von einem unabhängig gemessenen physikalischen Wirkungsgrad zu unterscheiden.

## Ladeprüfungen und spätere Pflege

- [x] Garagenwidget, Ladezielerreichung, Rückkehr aus Zielmodus, weitere Lastpunkte
  und maximale Ladeleistung von Andreas als erledigt bestätigt. Keine neuen
  Schreibtests ausgeführt; installierte YAML-Sicherung hier nicht unabhängig geprüft.
- [ ] Winter-Einphasenbetrieb noch abnehmen gemäß
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

## openHAB-Massenpflege vorbereitet, 16.10.2026

- [x] Authentifizierten REST-Lesezugriff mit lokal hinterlegtem, Git-ignoriertem
  Token geprüft; Token weder ausgegeben noch in Vorschauen übernommen.
- [x] 142 aktuelle SMA-Items inventarisiert: sechs Equipment-Gruppen und
  136 Datenitems. 133 Datenitems haben jeweils einen Channel, drei keinen.
- [x] Private Vorschau unter `private/openhab-review-2026-10-16/` erstellt,
  einschließlich bisheriger Item-Einstellungen und Persistence-Konfiguration.
  Alle vorgeschlagenen semantischen Tags existieren in der installierten Registry.
- [x] Aktive InfluxDB-Regeln gelesen: alle SMA-Datenitems in pEveryChange, fünf
  zusätzlich in pEveryUpdate. Doppelte pEveryChange-Regeln haben unterschiedliche
  Filter; eine allgemeine NULL/UNDEF-Filterung ist daraus nicht abzuleiten.
- [ ] Vorschläge zu Icons, Messung/Berechnung/Einstellung und Speichergruppen
  prüfen. Die drei unverknüpften Items und Equipment-Standorte bleiben offen.
- [ ] Auswirkungen auf Regeln und restoreOnStartup bei Befehlsaktionen prüfen;
  die Vorschau ist keine Freigabe zur Änderung der globalen Persistence-Regeln.
- [ ] Wiederholbaren Änderungsabgleich mit Konfliktprüfung und Rücksicherung
  vorbereiten. Es wurden ausschließlich GET-Anfragen gesendet, keine Live-Änderung.

- [x] Nachtrag: Andreas hat die fünf zusätzlichen pEveryUpdate-Mitgliedschaften
  entfernt. REST-Nachprüfung bestätigt jetzt 136 SMA-Datenitems in pEveryChange
  und keines in pEveryUpdate. Private Vorschau aktualisiert, Erstaufnahme bewahrt.
- [x] Validierung: Linter vollständig bestanden; 401 Tests nach Wiederholung mit
  lokalen Netzwerkrechten bestanden. Der erste Sandbox-Lauf konnte vier lokale
  Testserver nicht öffnen; kein Produktfehler nachgewiesen.

- [x] 16.10.: Vorschau erneut gegen die laufende Installation geprüft: alle 27
  verwendeten semantischen Tags vorhanden. 16 von 17 lokalen Icon-Schreibweisen
  liefern SVG; oh:car fehlt mit HTTP 404. Die ursprüngliche Vorschau bleibt
  unverändert und ist dadurch noch nicht zur Übernahme geeignet.
- [ ] Die drei Iconify-Symbole sind von der ausgelieferten MainUI unterstützt,
  ihre Auslieferung ist aber nicht bestätigt: Haupt- und beide Ersatz-API-Hosts
  antworten aus der Prüfumgebung mit HTTP 403. Clientprüfung bleibt offen.
  Private Einzelergebnisse: installation-verification.json neben der Vorschau.

- [x] Andreas bestätigt die Vorschau mit gezielter Korrektur: Wallbox-Equipment
  erhält vorgeschlagen oh:energy statt des fehlenden oh:car. Die drei bisher
  unverknüpften Zeititems erhalten Status + Timestamp und oh:time. Die numerische
  Anlagenzeit ist laut vorhandener Anzeige ein Epoch-Zeitpunkt, keine Laufzeit.
  CSV, JSON und Existenzprüfung aktualisiert; frühere Vorschau gesichert.
  Channel-Lücken, übrige Metadaten und Live-Konfiguration bleiben unverändert.

## openHAB-Massenpflege angewendet, 16.10.2026

- [x] Andreas gibt die korrigierte Vorschau ausdrücklich zur Live-Anwendung frei.
  Frische Vorprüfung: 142 Items, 138 Änderungen, keine Konflikte.
- [x] Alle 138 Item-Definitionen einzeln geändert und direkt zurückgelesen.
  Abschlussprüfung: alle 142 Items entsprechen den freigegebenen Icons,
  semantischen Tags und Gruppen. Vier Items waren bereits passend.
- [x] Wallbox-Equipment nutzt oh:energy. Die drei freigegebenen Zeititems haben
  Status + Timestamp und oh:time. Neue Speichergruppen gemäß Vorschau: schnelle
  Messwerte pEveryUpdate30s, langsamere pEveryUpdate60s, Energiezähler
  pEveryChangeCron; übrige überwiegend pEveryChange. Die Refresh-Aktion hat keine
  Persistence-Gruppe. Vorhandene globale Persistence-Regeln wurden nicht geändert.
- [x] Vollständige vorherige Item-Einstellungen, Links, globale InfluxDB-Regeln,
  konkreter Änderungsplan und Bestätigungsprotokoll privat gesichert.
  Channel-Links, Typen, Labels, Einheiten, Widgets und sonstige Metadaten erhalten;
  kein Item-Zustand und kein Gerätebefehl geschrieben. Wiederholbarer Abgleich
  liegt privat neben Vorschau und Sicherung.
- [ ] Drei zuvor unverknüpfte Zeititems bleiben unverknüpft; Semantikpflege behebt
  keine fehlende Datenversorgung. Equipment-Standorte bleiben unverändert.
- [ ] Darstellung der Iconify-Symbole im Client noch prüfen; die bekannte
  Einschränkung der externen API-Prüfung bleibt bestehen.

## MainUI-Seite SMA-Plant erstellt, 16.10.2026

- [x] Neue native MainUI-Seite SMA-Plant mit eigenem Sidebar-Eintrag angelegt.
  Grundlage ist Andreas' eingefügte Energiemanagement-Seite mit den tatsächlich
  installierten eigenen Widgets. Die acht bisherigen Seiten und zwölf
  Widget-Definitionen wurden unverändert zurückgelesen.
- [x] Eingebunden: eigener Live-Energiefluss, Tagesübersicht, eCharger-Komfort,
  BMW i3s und BMW 530d. Bestehende Item-Zuordnungen und Ladebedienung übernommen;
  wirkungslose Demo-Parameter bei den BMW-Instanzen entfernt.
- [x] Native KPI-Karten, Tagesdiagramm für PV/Haus/Netzbezug/Wallbox, Datenquellen,
  Solcast-Prognose, Wärmepumpe, Bilanzqualität und sechs aufklappbare Gerätebereiche
  ergänzt. Alle 136 SMA-Datenitems abgedeckt; insgesamt 188 vorhandene Item-Verweise.
- [x] Desktop-Sichtprüfung mit echten Werten: Übersicht, Diagramm, Fahrzeuge und
  Geräteakkordeon funktionieren; keine Browser-Konsolenfehler im geprüften Lauf.
  Beschriftungen gekürzt, Tripower-DC A/B auf der Seite unterscheidbar gemacht
  und fehlende Werte als Strich statt als 0 angezeigt. Keine Item-Definition,
  Persistence-Regel, Regel oder eigene Widget-Definition geändert.
- [x] JSON/YAML, Ausgangsseiten, Widget-Snapshot und Screenshots privat unter
  private/sma-plant-page-2026-10-16/ gesichert. Nur neue Seite geschrieben; keine
  Lade-/Fahrzeugbefehle zum Test gesendet.
- [ ] Darstellung auf Andreas' tatsächlichen Mobil-/Tabletgeräten bei Nutzung
  bestätigen; die Seite nutzt native responsive Spalten.

- [x] Abschlussvalidierung SMA-Plant: Linter und alle 401 Tests bestanden;
  Seiten-Readback, 136/136 SMA-Abdeckung, 188 existierende Item-Verweise und
  Browserprüfung im privaten Nachweis festgehalten.

## Widget-Korrektur Ladeziel, 16.10.2026

- [x] Screenshot-Fehler zugeordnet: zwei nicht unterstützte String()-Aufrufe in
  der Rückmeldeanzeige des Ladeplans. Beide durch Textverkettung ersetzt;
  kanonisches YAML und generierte Importdatei aktualisiert. Keine Änderung an
  Schreibfreigaben, Befehlen oder Energie-/Zielzeitprüfung.
- [x] Offizielle MainUI-Ausdrucksdokumentation konsultiert. 17 lokale
  Ausdrucksfälle ohne String-Konstruktor bestanden: kWh/Wh, numerische Werte,
  ungültige Werte, abweichende Zielzeit, unklarer Status und Demo.
- [ ] Aktualisierte Widget-Definition in openHAB übernehmen und Anzeige prüfen;
  bisher nur Repository-Dateien geändert, keine Gerätebefehle gesendet.
- [x] Vollständiger Linter und 401 Regressionstests bestanden. Erster Testlauf
  durch vier lokale Server-Sandboxfehler blockiert; Wiederholung mit lokalen
  Netzwerkrechten erfolgreich. Keine neue Live-Abnahme behauptet.

## Wallbox-Ladepause und Fortsetzung, 16.10.2026

- [x] Nach Andreas’ Meldung „Ladung abgeschlossen“ um 07:09:47 und 07:10:42
  API/SEMP lesend geprüft: beide 0 W, verbunden/wartend (200112), Sitzungsenergie
  konstant 1,871625 kWh (API), Zeitstempel 07:09:02 bleibt stehen; Gesamtzähler
  frisch und konstant. Keine Ladeeinstellungen geändert.
- [x] Nachkontrolle um 07:12:24 zeigt erneute Ladung (200113), rund 1,658 kW,
  Sitzungsenergie 1,905250 kWh mit frischem Zeitstempel und wachsendem Gesamtzähler.
  Damit Ladepause/Fortsetzung belegt, kein endgültiger Abschluss. Kein Reset auf
  null zwischen den Stichproben sichtbar. Ursache und exakte Übergänge unbekannt.
- [ ] Ablauf der 180-Sekunden-Frist in dieser Pause nicht belegt, weil bei der
  Nachkontrolle bereits wieder geladen wurde. Frühere Ruhe-Evidenz bleibt gültig;
  Publikationspolitik und weitere Reset-Auslöser bleiben offen.
  [Nachweis](docs/ECHARGER_LIVE_CHECK_2026-10-15.md#reported-charging-completion-and-observed-resumption-2026-10-16).

## Wallbox nach erneutem Ladeende, 16.10.2026

- [x] Erneute Abschlussmeldung von Andreas: fünf lesende API-/SEMP-Stichproben
  07:17:05–07:20:26 über gut drei Minuten. Durchgehend 0 W, verbunden/wartend
  (200112), Gesamtzähler frisch und konstant 1501,941750 kWh. Keine weitere
  Ladefortsetzung im Beobachtungsfenster.
- [x] Sitzungsenergie roh konstant 2,002625 kWh (API) / 2,0026 kWh (SEMP),
  Zeitstempel 07:15:54.260. Bei 172 s noch frisch; bei 222 und 272 s korrekt
  stale und von beiden Lesern ausgefiltert. Damit Fristablauf nach dieser Ladung
  bestätigt; die vorherige Pause/Fortsetzung bleibt eigenständige Beobachtung.
- [x] Keine Ladeeinstellung, Laufzeitkonfiguration, MQTT-Publikation oder
  Persistence geändert; Health/Event/Modus/Autorisierung weiterhin alte Zeitstempel.
- [ ] Publikationssemantik für letzte/aktuelle Sitzung mit Andreas festlegen;
  zusätzliche Reset-Auslöser und Zustandskanal-Zeitstempel bleiben offen.
  Keine endgültige Ziel-/SOC-Abnahme und keine MQTT-/openHAB-Zustellung aus den
  Direktlesungen ableiten.
  [Evidenz](docs/ECHARGER_LIVE_CHECK_2026-10-15.md#second-reported-completion-2026-10-16).

## Sitzungsanzeige umgesetzt, 16.10.2026

- [x] Andreas stimmt der gekennzeichneten Anzeige mit erhaltenem letztem Betrag zu.
  Entscheidung umgesetzt: Laden → „Geladen“, verbunden bei 0 W → „pausiert · bisher“,
  erst bestätigtes Abstecken → „Letzte Ladung“. Zeitablauf, Reset oder Moduswechsel
  allein belegen keinen Abschluss. Damit Publikationspolitik für diese Anzeige geklärt;
  frühere offene Einträge bleiben historischer Stand.
- [x] Vier zusätzliche Basic-Lesekanäle unter session; ursprünglicher Rohkanal,
  180-Sekunden-Filter, Tagesbilanz und Schreibfreigaben bleiben erhalten. SEMP hat
  bei Aktivierung Vorrang, sonst API; keine zusätzlichen Geräteanfragen.
- [x] Betrag/Quellzeitpunkt und letzter bestätigter Sitzungsabschluss begrenzt und
  atomar im bestehenden Zustandsvolume gespeichert. Neustart meldet Zustand unbekannt;
  alte Beträge beweisen keine Live-Verbindung. Fehler beim Speichern veröffentlichen
  keinen neuen ungesicherten Betrag. Kein Rückgriff auf Secrets oder Originalexporte.
- [x] Kanonisches Widget, Importdatei, Übersetzungen, Katalog und englische Anleitung
  ergänzt. Drei neue optionale Item-Zuordnungen für Status/Betrag/Messzeitpunkt;
  bisherige Item-Namen und Historien bleiben erhalten. Alt-Konfiguration zeigt
  ausdrücklich „Letzter Messwert“. Offizielle openHAB-Dokumentation konsultiert.
- [ ] Bridge-Neubau/Installation und neue Item-Verknüpfungen/Widget-Auswahl noch offen.
  Danach natürliche Pause/Fortsetzung, Abstecken und Neustart in MQTT/openHAB abnehmen.
  Bei erstmaligem Start mit bereits abgelaufenem Rohwert wird keine Sitzung erfunden;
  Messlücken können den gespeicherten Betrag unvollständig lassen. Zustand/SOC und
  weitere Reset-Auslöser sind eigenständige Fragen. Keine Live-Änderung ausgeführt.

- [x] Abschlussvalidierung Sitzungsanzeige: alle 418 Offline-Tests und der
  vollständige Linter erfolgreich, einschließlich Compose-Parität und Topic-Katalog.
  14 lokale Widget-Ausdrucksfälle ohne String-Konstruktor bestanden. Versetzter
  Nullreset vor Absteckstatus bewahrt den positiven Betrag auch über Neustart.
  Anfangs vier lokale Testserver durch Sandbox blockiert; Abschlusslauf mit lokalen
  Netzwerkrechten vollständig grün. Keine neue Live-Abnahme behauptet.

## Neue Sitzungsitems eingebunden, 16.10.2026

- [x] Vier von Andreas angelegte session-Items live anhand ihrer Channel-Links
  identifiziert und mit Icons, semantischen Tags und Wallbox-Equipment versehen.
  Energie: Measurement/Energy, oh:energy, pEveryChangeCron; Zustand:
  Status/Info, oh:text, pEveryChange; beide Quellzeiten: Status/Timestamp,
  oh:time, pEveryChange. Bestehende kWh-Metadaten erhalten.
- [x] Alle vier Detailzeilen auf SMA-Plant ergänzt; Wallbox zählt 45 Werte.
  Zustand, gespeicherte Energie und Messzeitpunkt direkt der Widget-Instanz
  zugeordnet. Definitionen und Seite zurückgelesen; andere Seiten, Widgets,
  Channel-Links und globale Persistence unverändert. Sicherung und Nachweis
  privat unter openhab-review-2026-10-16/session-items abgelegt.
- [ ] Natürliche nächste Sitzung prüfen. Vor der Definitionspflege war Status
  waiting, Betrag/Zeiten NULL; danach auch Status NULL. Widget zeigt deshalb
  weiterhin „Letzter Messwert: 0 kWh“. Keine künstliche Zustandsaktualisierung,
  MQTT-Neupublikation oder Neustart ausgeführt. Die Konfiguration ist übernommen,
  Versorgung und Übergänge der nächsten Sitzung sind noch nicht abgenommen.
- [x] Abschlussprüfung: vollständiger Linter über 200 Dateien und alle 418 Tests
  bestanden. Vier Testserver im ersten Sandbox-Lauf blockiert; Wiederholung mit
  erlaubten lokalen Ports erfolgreich.

## Kompakte Sitzungsanzeige ohne Datum, 16.10.2026

- [x] Auf Andreas’ Wunsch den langen Stand-Zeitstempel aus der kompakten
  Garagenanzeige entfernt. Energie, Sitzungszustand und Verbindungshinweis bleiben.
  Quellzeit-Item und Prüfung auf vorhandenen Messzeitpunkt bleiben erhalten;
  Zeitstempel sind weiterhin über die bestehenden Detailansichten verfügbar.
  Kanonisches YAML und generierte Importdatei gemeinsam aktualisiert.
- [ ] Aktualisierte Widget-Definition installieren und mobile Darstellung prüfen.
  Keine Live-Änderung und kein Gerätebefehl ausgeführt.
- [x] Validierung: vollständiger Linter, alle 418 Offline-Tests und sechs lokale
  Ausdrucksfälle bestanden; fehlende Quellzeit führt weiterhin zur Altwertanzeige.

## Getrennte Konfigurations- und State-Mounts, 16.10.2026

- [x] Beide Compose-Dateien binden den unveränderten Hostordner schreibgeschützt
  nach /data/sma-mqtt-bridge/config ein; JSON-, Profil- und Übersetzungsdefaults
  folgen diesem Pfad. State-Ziel und benanntes Volume bleiben unverändert.
- [x] Upgrade-Hinweise für explizite Datei-/Zertifikat-/Passwortpfade ergänzt.
  Keine privaten Dateien oder laufenden Container verändert.
- [ ] Installation mit aktualisiertem Image und Compose neu erstellen und
  tatsächliche Mounts prüfen; keine State-Migration oder Baseline-Rücksetzung.
- [x] Validierung: vollständiger Linter (200 Dateien), 418 Offline-Tests und
  Compose-Parität samt Overrides erfolgreich. Vier zunächst durch die Sandbox
  blockierte Loopback-Tests liefen mit erlaubten lokalen Testports erfolgreich.
