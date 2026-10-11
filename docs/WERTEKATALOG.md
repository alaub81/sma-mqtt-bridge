# SMA-Wertekatalog für die MQTT-Bridge

> Current MQTT node/property IDs remove hyphens at the publication boundary. Internal profile and
> readiness keys keep their spelling; historical examples below may use the former IDs. See
> [compact IDs and display translations](CONFIGURATION.md#display-language-and-compact-channel-ids).

Stand: 2026-10-10. Arbeitskatalog auf ausdrücklichen Wunsch mit deutschen Beschreibungen.

Diese Datei sammelt alle in den vorliegenden Quellen identifizierten Messwerte, Einstellungen und Befehle sowie weitere dokumentierte Kandidaten. Sie ist die gemeinsame Grundlage für die spätere Implementierung und wird bei neuen Unterlagen oder Geräteantworten ergänzt. Das erste Python-Lesegrundgerüst einschließlich Homie ist implementiert und offline geprüft. **Kein Topic gilt damit als an der Installation abgenommen.** Die drei Wechselrichterprofile bleiben `identity-only` und für Abfragen gesperrt.

Der vollständige Registerumfang ist derzeit nur für eine Sunny-Boy-Baureihe dokumentiert. Tripower und Sunny Boy Storage erhalten erst nach Modell- und Firmwareabgleich eigene vollständige Registerprofile. Eine allgemeine SMA-Adresse oder eine ähnliche Gerätebezeichnung beweist keine Unterstützung auf einem bestimmten Gerät.

## Inhalt

- [Nachweis und Topic-Regeln](#nachweis-und-topic-regeln)
- [Quellen und Gerätezuordnung](#quellen-und-gerätezuordnung)
- [Wechselrichter: bestehende 41 Channels](#wechselrichter-bestehende-41-channels)
- [Wechselrichter: vollständige Sunny-Boy-Registerliste](#wechselrichter-vollständige-sunny-boy-registerliste)
- [SunSpec-Zuordnungen](#sunspec-zuordnungen)
- [Home Manager: lokale Zählerwerte](#home-manager-lokale-zählerwerte)
- [Home Manager: Modbus für Netzsystemdienstleistungen](#home-manager-modbus-für-netzsystemdienstleistungen)
- [eCharger: Bedienparameter und Messwerte](#echarger-bedienparameter-und-messwerte)
- [eCharger: vollständiger Parameterbestand](#echarger-vollständiger-parameterbestand)
- [eCharger: SEMP](#echarger-semp)
- [ennexOS: bestätigte Felder und weitere Kandidaten](#ennexos-bestätigte-felder-und-weitere-kandidaten)
- [Erhalt der bestehenden openHAB-Funktionen](#erhalt-der-bestehenden-openhab-funktionen)
- [Berechnete Werte und Diagnose](#berechnete-werte-und-diagnose)
- [Offene Prüfungen und Pflege](#offene-prüfungen-und-pflege)

## Nachweis und Topic-Regeln

| Kennzeichen | Bedeutung |
| --- | --- |
| B | In einer gelieferten Konfiguration oder Geräteantwort vorhanden; Originalwert und individuelle Funktion sind noch nicht zwingend live geprüft. |
| D | In einer passenden Herstellerunterlage beschrieben; Unterstützung und Firmware am tatsächlichen Gerät noch prüfen. |
| R | Verhalten im funktionierenden openHAB-Referenzpaket beschrieben; noch nicht in Python portiert. |
| K | Kandidat aus Portaloberfläche, anderer Modellunterlage oder Protokollreferenz; API, Einheit oder Gerätezuordnung noch offen. |
| A | Berechneter Wert oder von der Bridge erzeugte Diagnose. |
| X | Inventarisiert, aber kein reguläres MQTT-Topic vorgesehen, etwa Geheimnisse, Kontoverwaltung oder reine Schreibregister ohne bestätigte Befehlsfreigabe. |

`RO` heißt nur lesen, `RW` in der Quelle lesen und schreiben, `W`/`WO` nur schreiben. **Ein dokumentiertes `RW` oder API-`editable=true` ist keine automatische Freigabe für Homie `/set`.** Bestätigte Wallbox-Bedienparameter werden separat aufgeführt. Netzschutz, Anlagensteuerung, Kommunikation, Firmwarepflege und Zugangsdaten gehören nicht zur allgemeinen Befehlsliste.

Die letzte Spalte jeder Wertetabelle enthält das geplante Zustands-Topic. Topic-IDs sind englisch und bestehen aus Kleinbuchstaben, Ziffern und Bindestrichen. Die bestehenden Vorschläge für `sma-inverter1`, `sma-inverter2`, `sma-inverter3`, `sma-home-manager` und `sma-echarger` unter `homie/` bleiben erhalten. Sie werden erst nach Geräteabgleich verbindlich.

Der erste Praxistest ist auf dem Mac vorgesehen. Die 41 vorhandenen Wechselrichterkanäle und 19 Poller sind jetzt auch im [maschinenlesbaren Things-Inventar](../reference/inverter-things-inventory.json) erfasst, ohne private Adressen oder Gerätefreigabe. Zusätzliche validierte Profile aus einem anderen Chat liegen nicht vor; Profile werden aus diesen Zuordnungen und passenden SMA-Unterlagen erarbeitet. Modell-/Firmware-/Seriennummern-Abfragen, Rohunits, NaN/Sentinels und Byte-/Wortreihenfolge bleiben zu prüfen. Lokale Wallbox-Bedienbefehle sind der nächste Funktionsschritt neben der Leseabnahme; im Python-Runtime sind sie weiterhin gesperrt.

`homie/sma-echarger/settings/charge-mode` berichtet zum Beispiel den rückgelesenen Modus. Erst nach implementierter Freigabe nimmt `homie/sma-echarger/settings/charge-mode/set` einen **nicht retained** gesendeten Befehl entgegen. Die Metadaten liegen unter `.../$datatype`, `.../$unit`, `.../$format`, `.../$settable` und `.../$retained`. Ein Zahlen-Payload enthält die Zahl; die Einheit steht in `$unit`. `—` bedeutet keine physikalische Einheit, `offen` bedeutet noch ungeklärt. Ein Bool verwendet `true`/`false`. Zeitangaben als MQTT-String verwenden ISO 8601 mit Zeitzone; Homie 4 besitzt keinen eigenen DateTime-Datentyp.

Zusatzregister erhalten vorläufig ein eindeutiges Topic `homie/sma-inverter3/registers/r<Adresse>`. Das ist ein Reservevorschlag für Werte außerhalb der bisherigen Channels, kein Auftrag, alle Register standardmäßig zu pollen. Bereits gemappte Register verwenden das vorhandene `measurements`-Topic. Parallelrepräsentationen eines Zählers in Wh, kWh, MWh oder 32/64 Bit werden nicht addiert. Ein späterer Adapter wählt eine kanonische Quelle.

Ungültige oder veraltete Werte werden nicht als 0 veröffentlicht. Rohcode, Status, Zeitstempel und Quelle bleiben unterscheidbar. Eine Portal-Einstellung ist kein lokal gemessener Istwert. Keine Seriennummern, Anlagenkennungen, IP-Adressen, Kontodaten, Passwörter oder Tokens werden als Beispielwerte in diese Datei kopiert.

Registertypen und Quelleneinheiten in den Tabellen beschreiben die **Eingangsdekodierung**, nicht automatisch den Homie-Payload. Bestätigte String-Items für Status/Netzrelais/Batteriestatus benötigen die vorhandene `sma.map`-Textsemantik am bestehenden Zustands-Topic oder ein ausdrücklich erhaltenes openHAB-Linkprofil. Für Rohcodes zusätzliche `status-code`, `grid-contactor-code` bzw. `battery-status-code` unter `measurements` vorsehen; dadurch keine bestehende String-Property mit Zahlen überschreiben. Bei Energie-Items die deklarierte Zielunit gesondert von Rohunit und Skalierung abgleichen.

Referenzen: [Homie 4](https://homieiot.github.io/specification/spec-core-v4_0_0/), [offizielles openHAB-Homie-Binding](https://www.openhab.org/addons/bindings/homie/).

## Quellen und Gerätezuordnung

Die Dokumentablagen für Dach und Carport/Wallbox enthalten dieselben 13 PDF-Inhalte, per SHA-256 verglichen. Auch die deutschen Register-HTMLs und ZIP-Pakete sind jeweils bytegleich. Sprachvarianten werden nicht als zusätzliche Fähigkeiten gezählt. Firmwaredateien wurden weder ausgeführt noch auf ein Gerät geladen.

| ID | Datei oder Quelle | Auswertung und Geltung |
| --- | --- | --- |
| S01 | `MODBUS-HTML_SB30-50-1AV-40_V10/README.pdf` und `modbuslist_de.html` | Liste 1.0 für SB3.0/3.6/4.0/5.0-1AV-40, Firmwarepaket 01.03.24.R; 198 SMA-Register, davon 84 RO, 106 RW und 8 W. Nicht das Profil aller drei Wechselrichter. |
| S02 | `SMA-Modbus-general-TI-de-10.pdf`, englische Fassung daneben | Allgemeine SMA-/SunSpec-Adressierung, Formate, NaN, Zugriff und Zeitverhalten; keine zusätzliche gerätespezifische Registerliste. |
| S03 | `HM-20-Modbus-NSD-TI-de-12.pdf` | Home-Manager-Modbus-Server ab Softwarepaket 2.10; Unit 1, Unit 2 und delegierte Wechselrichter-Parameter. |
| S04 | `EDMx-Modbus-TI-de-16.pdf` | SMA Data Manager L/M/M Lite, nicht Home Manager. Anlagen-, Batterie-, Sensor- und Netzanalysatorwerte dürfen daraus nicht auf den Home Manager übertragen werden. Kein Data Manager ist bisher Teil des Auftrags. |
| S05 | `HM-20-BE-de-23.pdf` | Betrieb, Zähler, Zeitfenster, Tarif, Verbraucherplanung, Rechte, Prognose und Direktkommunikation; behandelt das ältere Sunny Portal. ennexOS-Abgleich erforderlich. |
| S06 | `HM-20-DS-de-50.pdf` | Technische Mess- und Kommunikationsdaten; kein vollständiges API-/Registerschema. |
| S07 | `SMASmartHome-Compatibility-HM-20-TI-de-17.pdf` | Kompatibilität ab HM-Firmware 2.15.6.R, SEMP/EEBus/Schaltgeräte; kein Nachweis aller Messkanäle eines unterstützten Geräts. |
| S08 | `EVC22-3AC-20-BE-de-10.pdf`, `eCharger-DS-en-21.pdf` | eCharger-Bedienung, Lademodi, Phasenumschaltung, Autorisierung, Hardwaredaten; keine vollständige lokale API-/Modbus-Liste. |
| S09 | `READ_ME_EVC22-3AC-20_V2.01.42.R_DE.pdf`, englische Fassung daneben | Historische Firmwarehinweise 2.01.42.R; am bekannten eCharger ist 2.6.37.R dokumentiert. Keine Rückstufung oder Aktualisierung vorgenommen. |
| S10 | `SB30-60-DS-de-61.pdf` | Datenblatt der SB3.0–6.0-1AV-41-Baureihe; **abweichend von -40 in S01**. Datenblatt allein erweitert kein Modbus-Profil. |
| P01 | `private/things/sma.things`, `sma-sunnyboy.things`, `private/transform/` | 41 aktive Daten-Things, 19 Poller; alle lesen FC04, Port 502 und Unit 3. Die fünf JS-Transforms sind eingegangen; M01 ergänzt 34 Itemlinks, sieben bleiben offen. |
| P02 | `private/reference/sma/parameter-catalog.json` | 85 lokale eCharger-Metadaten, inklusive Editierbarkeit, Optionen und teilweise Grenzen; Einheiten fehlen in diesem verkürzten Export. |
| P03 | `private/reference/sma/sma-echarger-params.xml`, `sma-echarger-semp.xml` | 25 SEMP-Parameter sowie SEMP-Geräteeigenschaften und Status. |
| P04 | Lokales eCharger-openHAB-Paket v2.1 | 11 Bedienparameter, Live-Messwertzuordnung, sichere Schreib-/Rückleselogik, Items und Transformationen. |
| P05 | ennexOS-openHAB-Paket v1.0.2 | Normaler Portal-Login mit PKCE, eCharger-Eigenschaften, Mindest-PV-Anteil, Rechte und Rücklesen. |
| W01 | [Offizielle SMA-Modbus-Seite](https://www.sma.de/produkte/produktfeatures-schnittstellen/modbus-protokoll-schnittstelle) | Ergänzende Hinweise zu Modellabhängigkeit, Verbindungslimits und alten/neuen AC-Stromregistern. |
| W02 | [Offizielles openHAB-Energy-Meter-Binding](https://www.openhab.org/addons/bindings/smaenergymeter/) | 16 Standard-Channels für Bezug/Einspeisung insgesamt und L1–L3; UDP 9522, Multicast 239.12.255.254. |
| W03 | [SMA-EM-Protokolldecoder](https://github.com/datenschuft/SMA-EM/blob/master/speedwiredecoder.py) | Ergänzende Implementierungsreferenz für weitere OBIS-Kanäle; keine Herstellerzusage für das vorhandene Gerät. Code wurde nicht in die Bridge kopiert. |
| W04 | [Aktuelle offizielle Home-Manager-ennexOS-Anleitung](https://manuals.sma.de/HM-20-ennexOS/de-DE/index.html) | Portal-Funktionen und Einstellungen; UI-Verfügbarkeit beweist noch keinen verwendbaren oder schreibbaren Web-API-Endpunkt. |
| U01 | Angemeldete ennexOS-Oberfläche, lesend geprüft am 2026-10-10 | Geräteverwaltung, Firmware, Dashboard, Wallboxeigenschaften, Energiemanagement, Tarife und Kommunikationsansicht. Keine Geräteeinstellung verändert; keine Tokens oder privaten Kennungen übernommen. |
| U02 | Sichtbare CSV-Parameterexporte der fünf aktuellen Portalgeräte, 2026-10-10 | 458 Parameterzeilen: Home Manager 55, Tripower 109, Storage 164, Sunny Boy 108, eCharger 22. Nur technische Metadaten übernommen; Exportwerte und private Kopfdaten bleiben außerhalb des Repositorys. |
| M01 | Parallel eingegangenes MainUI-Inventar in `docs/MIGRATION.md` und `docs/migration-coverage.csv` | 34 verknüpfte Wechselrichter-Items, vier Home-Manager-Items und zehn abgeleitete Fähigkeiten; 100 Ledgerzeilen. Vollständiger Regel-/Persistence-/UI-Abgleich und Skalierung bleiben offen. |

Originaldateien liegen ausschließlich unter `private/wechselrichter_dokumentationen/` bzw. `private/reference/` und bleiben unverändert. Die öffentlichen Dokumente enthalten technische Metadaten und eigene Beschreibungen, keine kompletten PDF-Kopien.

| Geräte-ID | Bisheriger Bestand und Portalabgleich U01 | Noch zu bestätigen |
| --- | --- | --- |
| `sma-inverter1` | Kommentar „Tripower 8“, 14 Channels; Portal STP8.0-3AV-40, Firmware 4.10.10.R | Modbus-Host/Identität abgleichen; passendes vollständiges Profil fehlt. |
| `sma-inverter2` | Kommentar „Sunny Boy Storage 3.7“, 11 Channels; Portal SBS3.7-10, Firmware 4.07.31.R | Modbus-Host/Identität abgleichen; passendes Speicherprofil fehlt. |
| `sma-inverter3` | Kommentar „Sunny Boy 3.0“, 16 Channels; Portal **SB4.0-1AV-41**, Firmware 4.10.10.R | Modbus-Host/Identität abgleichen; **S01 ist -40 und noch nicht passend bestätigt**. |
| `sma-home-manager` | Home Manager 2, Firmware 2.19.1.R | Zähleranschlusspunkt, tatsächliche UDP-Telegramme und NSD-Zugriff prüfen. |
| `sma-echarger` | EVC22-3AC-20, Firmware 2.06.37.R; auch als 2.6.37.R notiert | Aktuelle Metadaten und Live-Kanäle für alle zusätzlichen Werte. |

Die aktuelle Portal-Anlagenansicht enthält diese fünf Geräte. Eine zweite Anlagenansicht enthält denselben SBS3.7-10 mit derselben privat verglichenen Identität, zeigt jedoch keine Live-Daten. Daraus wird kein zweites Speichergerät und kein zweiter Home Manager abgeleitet. Der Kommentar „Sunny Boy 3.0“ wird als historische Bezeichnung erhalten; eine endgültige Topic-/Hostzuordnung erfordert den lokalen Identitätsabgleich.

## Wechselrichter: bestehende 41 Channels

Quelle P01/M01; Topics entsprechen dem bisherigen Migrationsledger. Einheit und Format aus S01 gelten nur für dessen Baureihe und bleiben bei **allen drei Geräten Kandidaten**, bis die passenden Profile vorliegen. Die Alt-Dekodierung wird ausdrücklich erhalten: `int32` bei den ersten beiden Geräten, beim dritten eine Mischung. Beispielsweise dokumentiert S01 30771 als S32/FIX2, obwohl „Spannung“ keine Garantie für U32 ist. Die fünf `smalimit*.js` sind gelesen. M01 identifiziert 34 Item-Verknüpfungen; bei sieben Channels des dritten Geräts wurde kein Item gefunden. Explizite Item-Einheiten werden separat gezeigt, da sie keine Register-Rohunit oder Skalierung beweisen. „Set_Max_Power“ ist im Export ein RO-Channel.

### inverter1

| Alt-Channel | Bestehendes Item | Register | Alt-Typ | Quellenformat | Quellenunit (Kandidat) | Item-Unit laut M01 | Zugriff | Kurzbeschreibung | Nachweis | MQTT-Topic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `status` | `inverter1Status` | 30201 | int32 | TAGLIST (S01; Kandidat) | — | nicht ausdrücklich gesetzt | RO | Zustand | B; S01 anderes Modell; Profil offen | `homie/sma-inverter1/measurements/status` |
| `Grid_Contactor` | `inverter1GridContactor` | 30217 | int32 | TAGLIST (S01; Kandidat) | — | nicht ausdrücklich gesetzt | RO | Netzrelais/-schütz | B; S01 anderes Modell; Profil offen | `homie/sma-inverter1/measurements/grid-contactor` |
| `PowerDrawn` | `inverter1PowerDrawn` | 30865 | int32 | FIX0 (S01; Kandidat) | W | W | RO | Leistung Netzbezug | B; S01 anderes Modell; Profil offen | `homie/sma-inverter1/measurements/power-drawn` |
| `PowerGridFeedIn` | `inverter1PowerGridFeedIn` | 30867 | int32 | FIX0 (S01; Kandidat) | W | W | RO | Leistung Netzeinspeisung | B; S01 anderes Modell; Profil offen | `homie/sma-inverter1/measurements/power-grid-feed-in` |
| `Day_Yield` | `inverter1DailyYield` | 30537 | int32 | FIX0 (S01; Kandidat) | kWh | kWh | RO | Tagesertrag | B; S01 anderes Modell; Profil offen | `homie/sma-inverter1/measurements/day-yield` |
| `Total_Yield` | `inverter1TotalYield` | 30531 | int32 | FIX0 (S01; Kandidat) | kWh | kWh | RO | Gesamtertrag | B; S01 anderes Modell; Profil offen | `homie/sma-inverter1/measurements/total-yield` |
| `currentA_input` | `inverter1DC1Cur_input` | 30769 | int32 | FIX3 (S01; Kandidat) | A | A | RO | DC Strom Eingang A | B; S01 anderes Modell; Profil offen | `homie/sma-inverter1/measurements/current-a-input` |
| `voltageA_input` | `inverter1DC1Volt_input` | 30771 | int32 | FIX2 (S01; Kandidat) | V | V | RO | DC Spannung Eingang A | B; S01 anderes Modell; Profil offen | `homie/sma-inverter1/measurements/voltage-a-input` |
| `powerA_input` | `inverter1PowerA` | 30773 | int32 | FIX0 (S01; Kandidat) | W | W | RO | DC Leistung Eingang A | B; S01 anderes Modell; Profil offen | `homie/sma-inverter1/measurements/power-a-input` |
| `active_power` | `inverter1ActivePower` | 30775 | int32 | FIX0 (S01; Kandidat) | W | W | RO | Leistung | B; S01 anderes Modell; Profil offen | `homie/sma-inverter1/measurements/active-power` |
| `currentB_input` | `inverter1DC2Cur_input` | 30957 | int32 | FIX3 (S01; Kandidat) | A | A | RO | DC Strom Eingang B | B; S01 anderes Modell; Profil offen | `homie/sma-inverter1/measurements/current-b-input` |
| `voltageB_input` | `inverter1DC2Volt_input` | 30959 | int32 | FIX2 (S01; Kandidat) | V | V | RO | DC Spannung Eingang B | B; S01 anderes Modell; Profil offen | `homie/sma-inverter1/measurements/voltage-b-input` |
| `powerB_input` | `inverter1PowerB` | 30961 | int32 | FIX0 (S01; Kandidat) | W | W | RO | DC Leistung Eingang B | B; S01 anderes Modell; Profil offen | `homie/sma-inverter1/measurements/power-b-input` |
| `InternalTemperature` | `inverter1InternalTemperature` | 34113 | int32 | TEMP (S01; Kandidat) | °C | °C | RO | Innentemperatur | B; S01 anderes Modell; Profil offen | `homie/sma-inverter1/measurements/internal-temperature` |

### inverter2

| Alt-Channel | Bestehendes Item | Register | Alt-Typ | Quellenformat | Quellenunit (Kandidat) | Item-Unit laut M01 | Zugriff | Kurzbeschreibung | Nachweis | MQTT-Topic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `status` | `inverter2Status` | 30201 | int32 | TAGLIST (S01; Kandidat) | — | nicht ausdrücklich gesetzt | RO | Zustand | B; S01 anderes Modell; Profil offen | `homie/sma-inverter2/measurements/status` |
| `Grid_Contactor` | `inverter2GridRelay` | 30217 | int32 | TAGLIST (S01; Kandidat) | — | nicht ausdrücklich gesetzt | RO | Netzrelais/-schütz | B; S01 anderes Modell; Profil offen | `homie/sma-inverter2/measurements/grid-contactor` |
| `Day_Yield` | `inverter2DayYield` | 30537 | int32 | FIX0 (S01; Kandidat) | kWh | kWh | RO | Tagesertrag | B; S01 anderes Modell; Profil offen | `homie/sma-inverter2/measurements/day-yield` |
| `Total_Yield` | `inverter2TotalYield` | 30531 | int32 | FIX0 (S01; Kandidat) | kWh | kWh | RO | Gesamtertrag | B; S01 anderes Modell; Profil offen | `homie/sma-inverter2/measurements/total-yield` |
| `CurrentBatStatCharge` | `inverter2BatStateCharge` | 30845 | int32 | offen | % | % | RO | Batterieladezustand laut Bestandsname; SBS-Profil und Bezug auf nutzbare Kapazität prüfen. | B; Profil fehlt | `homie/sma-inverter2/measurements/current-bat-stat-charge` |
| `CurrentBatcapacity` | `inverter2BatCapacity` | 30847 | int32 | offen | offen | % | RO | Im Bestand als Batteriekapazität bezeichnet; Bedeutung und Einheit sind ohne SBS-Profil offen. | B; Profil fehlt | `homie/sma-inverter2/measurements/current-batcapacity` |
| `CurrentBatTemp` | `inverter2BatTemp` | 30849 | int32 | offen | °C? | °C | RO | Im Bestand als Batterietemperatur bezeichnet; Einheit und TEMP-Skalierung bestätigen. | B; Profil fehlt | `homie/sma-inverter2/measurements/current-bat-temp` |
| `BatteryStatus` | `inverter2BatteryStatus` | 30955 | int32 | offen | —? | nicht ausdrücklich gesetzt | RO | Im Bestand als Batteriestatus bezeichnet; Enum und Bedeutung bestätigen. | B; Profil fehlt | `homie/sma-inverter2/measurements/battery-status` |
| `PresBatCharge` | `inverter2PreBatCharge` | 31393 | int32 | offen | W? | W | RO | Im Bestand als Batterieladeleistung bezeichnet; Richtung, Typ und Einheit bestätigen. | B; Profil fehlt | `homie/sma-inverter2/measurements/pres-bat-charge` |
| `PresBattDischarge` | `inverter2PreBatDischarge` | 31395 | int32 | offen | W? | W | RO | Im Bestand als Batterieentladeleistung bezeichnet; Richtung, Typ und Einheit bestätigen. | B; Profil fehlt | `homie/sma-inverter2/measurements/pres-batt-discharge` |
| `InternalTemperature` | `inverter2InternalTemperature` | 34113 | int32 | TEMP (S01; Kandidat) | °C | °C | RO | Innentemperatur | B; S01 anderes Modell; Profil offen | `homie/sma-inverter2/measurements/internal-temperature` |

### inverter3

| Alt-Channel | Bestehendes Item | Register | Alt-Typ | Quellenformat | Quellenunit (Kandidat) | Item-Unit laut M01 | Zugriff | Kurzbeschreibung | Nachweis | MQTT-Topic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `type` | noch nicht gefunden | 30053 | uint32 | TAGLIST (S01; Kandidat) | — | Item noch offen | RO | Gerätetyp | B; S01 anderes Modell; Profil offen | `homie/sma-inverter3/measurements/type` |
| `status` | `inverter3Status` | 30201 | uint32 | TAGLIST (S01; Kandidat) | — | nicht ausdrücklich gesetzt | RO | Zustand | B; S01 anderes Modell; Profil offen | `homie/sma-inverter3/measurements/status` |
| `Grid_Contactor` | `inverter3GridContactor` | 30217 | uint32 | TAGLIST (S01; Kandidat) | — | nicht ausdrücklich gesetzt | RO | Netzrelais/-schütz | B; S01 anderes Modell; Profil offen | `homie/sma-inverter3/measurements/grid-contactor` |
| `Max_Power` | noch nicht gefunden | 30231 | uint32 | FIX0 (S01; Kandidat) | W | Item noch offen | RO | Maximale Gerätewirkleistung | B; S01 anderes Modell; Profil offen | `homie/sma-inverter3/measurements/max-power` |
| `Set_Max_Power` | noch nicht gefunden | 30233 | uint32 | FIX0 (S01; Kandidat) | W | Item noch offen | RO | Eingestellte Wirkleistungsgrenze | B; S01 anderes Modell; Profil offen | `homie/sma-inverter3/measurements/set-max-power` |
| `PowerDrawn` | noch nicht gefunden | 30865 | int32 | FIX0 (S01; Kandidat) | W | Item noch offen | RO | Leistung Netzbezug | B; S01 anderes Modell; Profil offen | `homie/sma-inverter3/measurements/power-drawn` |
| `PowerGridFeedIn` | noch nicht gefunden | 30867 | int32 | FIX0 (S01; Kandidat) | W | Item noch offen | RO | Leistung Netzeinspeisung | B; S01 anderes Modell; Profil offen | `homie/sma-inverter3/measurements/power-grid-feed-in` |
| `Day_Yield` | `inverter3DailyYield` | 30537 | uint32 | FIX0 (S01; Kandidat) | kWh | nicht ausdrücklich gesetzt | RO | Tagesertrag | B; S01 anderes Modell; Profil offen | `homie/sma-inverter3/measurements/day-yield` |
| `Total_Yield` | `inverter3TotalYield` | 30531 | uint32 | FIX0 (S01; Kandidat) | kWh | nicht ausdrücklich gesetzt | RO | Gesamtertrag | B; S01 anderes Modell; Profil offen | `homie/sma-inverter3/measurements/total-yield` |
| `currentA_input` | `inverter3DC1Cur_input` | 30769 | int32 | FIX3 (S01; Kandidat) | A | nicht ausdrücklich gesetzt | RO | DC Strom Eingang A | B; S01 anderes Modell; Profil offen | `homie/sma-inverter3/measurements/current-a-input` |
| `voltageA_input` | `inverter3DC1Volt_input` | 30771 | int32 | FIX2 (S01; Kandidat) | V | nicht ausdrücklich gesetzt | RO | DC Spannung Eingang A | B; S01 anderes Modell; Profil offen | `homie/sma-inverter3/measurements/voltage-a-input` |
| `powerA_input` | `inverter3PowerA` | 30773 | int32 | FIX0 (S01; Kandidat) | W | nicht ausdrücklich gesetzt | RO | DC Leistung Eingang A | B; S01 anderes Modell; Profil offen | `homie/sma-inverter3/measurements/power-a-input` |
| `active_power` | `inverter3ActivePower` | 30775 | int32 | FIX0 (S01; Kandidat) | W | nicht ausdrücklich gesetzt | RO | Leistung | B; S01 anderes Modell; Profil offen | `homie/sma-inverter3/measurements/active-power` |
| `power_L1` | noch nicht gefunden | 30777 | int32 | offen | W? | Item noch offen | RO | Im Bestand als Phasenleistung L1 bezeichnet; in S01 nicht aufgeführt. | B; Profil fehlt | `homie/sma-inverter3/measurements/power-l1` |
| `volt_G1` | noch nicht gefunden | 30783 | uint32 | FIX2 (S01; Kandidat) | V | Item noch offen | RO | Netzspannung Phase L1 | B; S01 anderes Modell; Profil offen | `homie/sma-inverter3/measurements/volt-g1` |
| `InternalTemperature` | `inverter3InternalTemperature` | 34113 | int32 | TEMP (S01; Kandidat) | °C | nicht ausdrücklich gesetzt | RO | Innentemperatur | B; S01 anderes Modell; Profil offen | `homie/sma-inverter3/measurements/internal-temperature` |

## Wechselrichter: vollständige Sunny-Boy-Registerliste

**Alle 198 Einträge aus S01**, nach Funktionsgruppe. Zugriff, Registerbreite, Typ, Format, Einheit, Wertebereich und Grid-Guard-Kennzeichnung stammen aus der Liste 1.0. `GG` bedeutet ein Grid-Guard-Symbol in der Quelle. Alle Einträge sind D; tatsächliche Modell-/Firmwareunterstützung bleibt offen. Ein Topic bei RW ist vorerst ausschließlich ein **lesender Zustand**. Bei W sowie privaten Identitäts-/Netzwerkdaten steht X ohne reguläres Topic.

`FIXn`: Rohwert / 10ⁿ. `TEMP`: eine Nachkommastelle in der angegebenen Einheit. `Dauer`: Einheit der jeweiligen Zeile, nicht grundsätzlich Sekunden. `TAGLIST`: Zahlencode, keine Skalierung. `FW`/`REV`: versionsspezifisch dekodieren. S32-NaN: `0x80000000`, U32-NaN: `0xffffffff`, Status-NaN: `0x00fffffd`, U64-NaN: `0xffffffffffffffff`; vor der Skalierung erkennen.

SMA-Registeradressen aus S01/P01 unverändert verwenden; nur die **SunSpec-Adressspalte** hat laut S02 den Offset −1. Bytes und Mehrwortwerte im SMA-Profil sind Big Endian. U64 stets vollständig in vier 16-Bit-Registern lesen. Für bestehende Poller FC04 erhalten; FC03 ist ebenfalls beschrieben, aber kein Grund zur stillen Umstellung.

S02 empfiehlt mindestens 10 s Abstand und gleichzeitig höchstens fünf Parameter/Messwerte je Wechselrichter; vorhandene 3-s-Poller müssen vor dem Livebetrieb gegen aktuelle Modellunterlagen geprüft werden. Dokumentierte Modbus-Reaktionszeit 5–10 s bedeutet, dass unmittelbar nach einer Änderung ein alter Wert möglich ist. Dauerhaft gespeicherte RW-Parameter nicht zyklisch schreiben. Protokollierte Anlagensteuerobjekte sind gesondert zu behandeln; die Bridge übernimmt keine zusätzliche Laderegelung.

### Benutzeroberfläche, Zeit und Identität

| Register | SMA-Objekt | Typ / Format | Unit | Quellenzugriff | Bereich / Optionen | Kurzbeschreibung | MQTT-Topic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 30051 | `Nameplate.MainModel` | 2 × 16 Bit; U32/TAGLIST | — | RO | Codes: 8001: Solar-Wechselrichter (DevClss1) | Geräteklasse | `homie/sma-inverter3/registers/r30051` |
| 30053 | `Nameplate.Model` | 2 × 16 Bit; U32/TAGLIST | — | RO | Codes: 9319: Sunny Boy 3.0 (SB3.0-1AV-40) 9320: Sunny Boy 3.6 (SB3.6-1AV-40) 9321: Sunny Boy 4.0 (SB4.0-1AV-40) 9322: Sunny Boy 5.0 (SB5.0-1AV-40) | Gerätetyp | `homie/sma-inverter3/measurements/type` |
| 30057 | `Nameplate.SerNum` | 2 × 16 Bit; U32/RAW | — | RO | 0 bis 4294967294 | Seriennummer | X: kein reguläres Topic |
| 30059 | `Nameplate.PkgRev` | 2 × 16 Bit; U32/FW | — | RO | 0 bis 4294967294 | Softwarepaket | `homie/sma-inverter3/registers/r30059` |
| 40003 | `DtTm.TmZn` | 2 × 16 Bit; U32/TAGLIST | — | RW | Codes: 9499: (UTC-AUTO) Automatisch über SMA Protokoll (TmZnTmSvr) | Zeitzone | `homie/sma-inverter3/registers/r40003` |
| 40005 | `DtTm.DlSvIsOn` | 2 × 16 Bit; U32/TAGLIST | — | RW | Codes: 1129: Ja (Yes) 1130: Nein (No) | Automatische Sommer-/Winterzeitumstellung eingeschaltet | `homie/sma-inverter3/registers/r40005` |
| 40013 | `CntrySettings.Lang` | 2 × 16 Bit; U32/TAGLIST | — | RW | Codes: 777: Deutsch (LangDE) 778: English (LangEN) 779: Italiano (LangIT) 780: Español (LangES) 781: Français (LangFR) 782: Ελληνικά (LangEL) 783: 한국어 (LangKO) 784: Česky (LangCS) 785: Português (LangPT) 786: Nederlands (LangNL) 798: Polski (LangPL) 801: ภาษาไทย (LangTH) | Sprache der Oberfläche | `homie/sma-inverter3/registers/r40013` |
| 40063 | `Nameplate.CmpMain.SwRev` | 2 × 16 Bit; U32/FW | — | RO | 0 bis 4294967294 | Firmware-Version des Hauptprozessors | `homie/sma-inverter3/registers/r40063` |
| 40067 | `Nameplate.SerNum` | 2 × 16 Bit; U32/RAW | — | RO | 0 bis 4294967294 | Seriennummer | X: kein reguläres Topic |
| 40497 | `Nameplate.MacId` | 16 × 16 Bit; STR32/UTF8 | — | RO | nicht angegeben | MAC-Adresse; private Netzwerkidentität. | X: kein reguläres Topic |
| 40631 | `Nameplate.Location` | 12 × 16 Bit; STR32/UTF8 | — | RW | nicht angegeben | Gerätename bzw. Standortbezeichnung. | X: kein reguläres Topic |
| 40789 | `Nameplate.ComRev` | 2 × 16 Bit; U32/REV | — | RO | 0 bis 4294967294 | Kommunikationsversion | `homie/sma-inverter3/registers/r40789` |

### DC-Messung und Temperaturen

| Register | SMA-Objekt | Typ / Format | Unit | Quellenzugriff | Bereich / Optionen | Kurzbeschreibung | MQTT-Topic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 30769 | `DcMs.Amp` | 2 × 16 Bit; S32/FIX3 | A | RO | nicht angegeben | DC Strom Eingang (Eingang A) | `homie/sma-inverter3/measurements/current-a-input` |
| 30771 | `DcMs.Vol` | 2 × 16 Bit; S32/FIX2 | V | RO | nicht angegeben | DC Spannung Eingang (Eingang A) | `homie/sma-inverter3/measurements/voltage-a-input` |
| 30773 | `DcMs.Watt` | 2 × 16 Bit; S32/FIX0 | W | RO | nicht angegeben | DC Leistung Eingang (Eingang A) | `homie/sma-inverter3/measurements/power-a-input` |
| 30953 | `Coolsys.Cab.TmpVal` | 2 × 16 Bit; S32/TEMP | °C | RO | nicht angegeben | Innentemperatur | `homie/sma-inverter3/registers/r30953` |
| 30957 | `DcMs.Amp` | 2 × 16 Bit; S32/FIX3 | A | RO | nicht angegeben | DC Strom Eingang (Eingang B) | `homie/sma-inverter3/registers/r30957` |
| 30959 | `DcMs.Vol` | 2 × 16 Bit; S32/FIX2 | V | RO | nicht angegeben | DC Spannung Eingang (Eingang B) | `homie/sma-inverter3/registers/r30959` |
| 30961 | `DcMs.Watt` | 2 × 16 Bit; S32/FIX0 | W | RO | nicht angegeben | DC Leistung Eingang (Eingang B) | `homie/sma-inverter3/registers/r30961` |
| 34109 | `Coolsys.Hs1.TmpVal` | 2 × 16 Bit; S32/TEMP | °C | RO | nicht angegeben | Kühlkörpertemperatur | `homie/sma-inverter3/registers/r34109` |
| 34113 | `Coolsys.Cab.TmpVal` | 2 × 16 Bit; S32/TEMP | °C | RO | nicht angegeben | Innentemperatur | `homie/sma-inverter3/measurements/internal-temperature` |

### AC-Messung

| Register | SMA-Objekt | Typ / Format | Unit | Quellenzugriff | Bereich / Optionen | Kurzbeschreibung | MQTT-Topic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 30775 | `GridMs.TotW` | 2 × 16 Bit; S32/FIX0 | W | RO | nicht angegeben | Leistung | `homie/sma-inverter3/measurements/active-power` |
| 30783 | `GridMs.PhV.phsA` | 2 × 16 Bit; U32/FIX2 | V | RO | nicht angegeben | Netzspannung Phase L1 | `homie/sma-inverter3/measurements/volt-g1` |
| 30785 | `GridMs.PhV.phsB` | 2 × 16 Bit; U32/FIX2 | V | RO | nicht angegeben | Netzspannung Phase L2 | `homie/sma-inverter3/registers/r30785` |
| 30787 | `GridMs.PhV.phsC` | 2 × 16 Bit; U32/FIX2 | V | RO | nicht angegeben | Netzspannung Phase L3 | `homie/sma-inverter3/registers/r30787` |
| 30803 | `GridMs.Hz` | 2 × 16 Bit; U32/FIX2 | Hz | RO | nicht angegeben | Netzfrequenz | `homie/sma-inverter3/registers/r30803` |
| 30805 | `GridMs.TotVAr` | 2 × 16 Bit; S32/FIX0 | VAr | RO | nicht angegeben | Blindleistung | `homie/sma-inverter3/registers/r30805` |
| 30813 | `GridMs.TotVA` | 2 × 16 Bit; S32/FIX0 | VA | RO | nicht angegeben | Scheinleistung | `homie/sma-inverter3/registers/r30813` |
| 30823 | `GridMs.TotPFExt` | 2 × 16 Bit; U32/TAGLIST | — | RO | Codes: 1041: Übererregt (OvExt) 1042: Untererregt (UnExt) | Erregungsart des cos Phi | `homie/sma-inverter3/registers/r30823` |
| 30949 | `GridMs.TotPFPrc` | 2 × 16 Bit; U32/FIX3 | — | RO | nicht angegeben | Verschiebungsfaktor | `homie/sma-inverter3/registers/r30949` |
| 30977 | `GridMs.A.phsA` | 2 × 16 Bit; S32/FIX3 | A | RO | nicht angegeben | Netzstrom Phase L1 | `homie/sma-inverter3/registers/r30977` |
| 30979 | `GridMs.A.phsB` | 2 × 16 Bit; S32/FIX3 | A | RO | nicht angegeben | Netzstrom Phase L2 | `homie/sma-inverter3/registers/r30979` |
| 30981 | `GridMs.A.phsC` | 2 × 16 Bit; S32/FIX3 | A | RO | nicht angegeben | Netzstrom Phase L3 | `homie/sma-inverter3/registers/r30981` |

### Ertrag, Zähler und Betriebszeiten

| Register | SMA-Objekt | Typ / Format | Unit | Quellenzugriff | Bereich / Optionen | Kurzbeschreibung | MQTT-Topic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 30513 | `Metering.TotWhOut` | 4 × 16 Bit; U64/FIX0 | Wh | RO | nicht angegeben | Gesamtertrag | `homie/sma-inverter3/registers/r30513` |
| 30517 | `Metering.DyWhOut` | 4 × 16 Bit; U64/FIX0 | Wh | RO | nicht angegeben | Tagesertrag | `homie/sma-inverter3/registers/r30517` |
| 30521 | `Metering.TotOpTms` | 4 × 16 Bit; U64/Dauer | s | RO | nicht angegeben | Betriebszeit | `homie/sma-inverter3/registers/r30521` |
| 30525 | `Metering.TotFeedTms` | 4 × 16 Bit; U64/Dauer | s | RO | nicht angegeben | Einspeisezeit | `homie/sma-inverter3/registers/r30525` |
| 30529 | `Metering.TotWhOut` | 2 × 16 Bit; U32/FIX0 | Wh | RO | nicht angegeben | Gesamtertrag | `homie/sma-inverter3/registers/r30529` |
| 30531 | `Metering.TotWhOut` | 2 × 16 Bit; U32/FIX0 | kWh | RO | nicht angegeben | Gesamtertrag | `homie/sma-inverter3/measurements/total-yield` |
| 30533 | `Metering.TotWhOut` | 2 × 16 Bit; U32/FIX0 | MWh | RO | nicht angegeben | Gesamtertrag | `homie/sma-inverter3/registers/r30533` |
| 30535 | `Metering.DyWhOut` | 2 × 16 Bit; U32/FIX0 | Wh | RO | nicht angegeben | Tagesertrag | `homie/sma-inverter3/registers/r30535` |
| 30537 | `Metering.DyWhOut` | 2 × 16 Bit; U32/FIX0 | kWh | RO | nicht angegeben | Tagesertrag | `homie/sma-inverter3/measurements/day-yield` |
| 30539 | `Metering.DyWhOut` | 2 × 16 Bit; U32/FIX0 | MWh | RO | nicht angegeben | Tagesertrag | `homie/sma-inverter3/registers/r30539` |
| 30541 | `Metering.TotOpTms` | 2 × 16 Bit; U32/Dauer | s | RO | nicht angegeben | Betriebszeit | `homie/sma-inverter3/registers/r30541` |
| 30543 | `Metering.TotFeedTms` | 2 × 16 Bit; U32/Dauer | s | RO | nicht angegeben | Einspeisezeit | `homie/sma-inverter3/registers/r30543` |
| 30581 | `Metering.GridMs.TotWhIn` | 2 × 16 Bit; U32/FIX0 | Wh | RO | nicht angegeben | Zählerstand Netzbezugs-Zähler | `homie/sma-inverter3/registers/r30581` |
| 30583 | `Metering.GridMs.TotWhOut` | 2 × 16 Bit; U32/FIX0 | Wh | RO | nicht angegeben | Zählerstand Netzeinspeise-Zähler | `homie/sma-inverter3/registers/r30583` |
| 30865 | `Metering.GridMs.TotWIn` | 2 × 16 Bit; S32/FIX0 | W | RO | nicht angegeben | Leistung Netzbezug | `homie/sma-inverter3/measurements/power-drawn` |
| 30867 | `Metering.GridMs.TotWOut` | 2 × 16 Bit; S32/FIX0 | W | RO | nicht angegeben | Leistung Netzeinspeisung | `homie/sma-inverter3/measurements/power-grid-feed-in` |
| 41171 | `Metering.TotkWhOutSet` | 2 × 16 Bit; U32/FIX0 | kWh | RW | 0 kWh bis 4000000 kWh | Setze Gesamtertrag | `homie/sma-inverter3/registers/r41171` |
| 41173 | `Metering.TotOpTmhSet` | 2 × 16 Bit; U32/Dauer | h | RW | 0 h bis 440000 h | Setze Gesamte Betriebszeit am Netzanschlusspunkt | `homie/sma-inverter3/registers/r41173` |

### Zustand und Isolation

| Register | SMA-Objekt | Typ / Format | Unit | Quellenzugriff | Bereich / Optionen | Kurzbeschreibung | MQTT-Topic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 30199 | `Operation.RmgTms` | 2 × 16 Bit; U32/Dauer | s | RO | 0 s bis 1600 s | Wartezeit bis Einspeisung | `homie/sma-inverter3/registers/r30199` |
| 30201 | `Operation.Health` | 2 × 16 Bit; U32/TAGLIST | — | RO | Codes: 35: Fehler (Alm) 303: Aus (Off) 307: Ok (Ok) 455: Warnung (Wrn) | Zustand | `homie/sma-inverter3/measurements/status` |
| 30203 | `Operation.HealthStt.Ok` | 2 × 16 Bit; U32/FIX0 | W | RO | 0 W bis 1 W | Nennleistung im Zustand Ok | `homie/sma-inverter3/registers/r30203` |
| 30205 | `Operation.HealthStt.Wrn` | 2 × 16 Bit; U32/FIX0 | W | RO | 0 W bis 1 W | Nennleistung im Zustand Warnung | `homie/sma-inverter3/registers/r30205` |
| 30207 | `Operation.HealthStt.Alm` | 2 × 16 Bit; U32/FIX0 | W | RO | 0 W bis 1 W | Nennleistung im Zustand Fehler | `homie/sma-inverter3/registers/r30207` |
| 30211 | `Operation.Evt.Prio` | 2 × 16 Bit; U32/TAGLIST | — | RO | Codes: 336: Hersteller kontaktieren (PrioA) 337: Installateur kontaktieren (PrioC) 338: ungültig (PrioIna) 887: keine (NonePrio) | Empfohlene Aktion | `homie/sma-inverter3/registers/r30211` |
| 30213 | `Operation.Evt.Msg` | 2 × 16 Bit; U32/TAGLIST | — | RO | Codes: 886: keine (NoneMsg) | Meldung | `homie/sma-inverter3/registers/r30213` |
| 30215 | `Operation.Evt.Dsc` | 2 × 16 Bit; U32/TAGLIST | — | RO | Codes: 885: keine (NoneDsc) | Fehlerbehebungsmaßnahme | `homie/sma-inverter3/registers/r30215` |
| 30217 | `Operation.GriSwStt` | 2 × 16 Bit; U32/TAGLIST | — | RO | Codes: 51: Geschlossen (Cls) 311: Offen (Opn) 16777213: Information liegt nicht vor (NaNStt) | Netzrelais/-schütz | `homie/sma-inverter3/measurements/grid-contactor` |
| 30225 | `Isolation.LeakRis` | 2 × 16 Bit; U32/FIX0 | Ohm | RO | nicht angegeben | Isolationswiderstand | `homie/sma-inverter3/registers/r30225` |
| 30247 | `Operation.Evt.EvtNo` | 2 × 16 Bit; U32/FIX0 | — | RO | nicht angegeben | Aktuelle Ereignisnummer für Hersteller | `homie/sma-inverter3/registers/r30247` |
| 30559 | `Operation.EvtCntUsr` | 2 × 16 Bit; U32/FIX0 | — | RO | nicht angegeben | Anzahl Ereignisse für Benutzer | `homie/sma-inverter3/registers/r30559` |
| 30561 | `Operation.EvtCntIstl` | 2 × 16 Bit; U32/FIX0 | — | RO | nicht angegeben | Anzahl Ereignisse für Installateur | `homie/sma-inverter3/registers/r30561` |
| 30563 | `Operation.EvtCntSvc` | 2 × 16 Bit; U32/FIX0 | — | RO | nicht angegeben | Anzahl Ereignisse für Service | `homie/sma-inverter3/registers/r30563` |
| 30599 | `Operation.GriSwCnt` | 2 × 16 Bit; U32/FIX0 | — | RO | nicht angegeben | Anzahl Netzzuschaltungen | `homie/sma-inverter3/registers/r30599` |
| 31085 | `Operation.HealthStt.Ok` | 2 × 16 Bit; U32/FIX0 | W | RO | 0 W bis 1 W | Nennleistung im Zustand Ok | `homie/sma-inverter3/registers/r31085` |
| 31247 | `Isolation.FltA` | 2 × 16 Bit; S32/FIX3 | A | RO | nicht angegeben | Fehlerstrom | `homie/sma-inverter3/registers/r31247` |
| 35377 | `Operation.EvtCntUsr` | 4 × 16 Bit; U64/FIX0 | — | RO | nicht angegeben | Anzahl Ereignisse für Benutzer | `homie/sma-inverter3/registers/r35377` |
| 35381 | `Operation.EvtCntIstl` | 4 × 16 Bit; U64/FIX0 | — | RO | nicht angegeben | Anzahl Ereignisse für Installateur | `homie/sma-inverter3/registers/r35381` |
| 35385 | `Operation.EvtCntSvc` | 4 × 16 Bit; U64/FIX0 | — | RO | nicht angegeben | Anzahl Ereignisse für Service | `homie/sma-inverter3/registers/r35385` |
| 40009 | `Operation.OpMod` | 2 × 16 Bit; U32/TAGLIST | — | RW | Codes: 295: MPP (Mpp) 381: Stopp (Stop) 443: Konstantspannung (VolDCConst) | Betriebszustand | `homie/sma-inverter3/registers/r40009` |

### Netzschutz und Ländernorm

| Register | SMA-Objekt | Typ / Format | Unit | Quellenzugriff | Bereich / Optionen | Kurzbeschreibung | MQTT-Topic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 40109 | `GridGuard.Cntry` | 2 × 16 Bit; U32/TAGLIST | — | RO | Codes: 27: Sondereinstellung (Adj) 306: Inselbetrieb 60 Hz (OFF-Grid60) 313: Inselbetrieb 50 Hz (OFF-Grid50) 333: PPC (PPC) 438: VDE0126-1-1 (VDE0126-1-1) 1199: PPDS (PPDS) 7504: SI4777-2 (SI4777-2) 7510: VDE-AR-N4105 (VDE-AR-N4105) 7513: VDE-AR-N4105-MP (VDE-AR-N4105-MP) 7514: VDE-AR-N4105-HP (VDE-AR-N4105-HP) 7517: CEI 0-21 intern (CEI0-21Int) 7523: C10/11/2012 (C10/11/2012) 7525: G83/2 (G83/2) 7527: VFR2014 (VFR2014) 7528: G59/3 (G59/3) 7530: MEA2013 (MEA2013) 7531: PEA2013 (PEA2013) 7532: EN50438:2013 (EN50438_2013) 7533: NEN-EN50438:2013 (NEN-EN50438_13) 7536: Default (DftEN) 7539: RD1699/413 (RD1699/413) 7549: AS4777.2_2015 (AS4777.2_2015) 7550: NRS97-2-1 (NRS97-2-1) 7551: NT_Ley20571 (NT_Ley2057) 7565: ABNT NBR 16149:2013 (ABNT_NBR_16149_2013) 7566: IE-EN50438:2013 (IE-EN50438_2013) 7567: DEWA 2016 intern (DEWA_2016_intern) 16777213: Information liegt nicht vor (NaNStt) | Eingestellte Ländernorm | `homie/sma-inverter3/registers/r40109` |
| 40133 | `GridGuard.Cntry.VRtg` | 2 × 16 Bit; U32/FIX0 | V | RW; GG | 100 V bis 280 V | Netz-Nennspannung | `homie/sma-inverter3/registers/r40133` |
| 40135 | `GridGuard.Cntry.HzRtg` | 2 × 16 Bit; U32/FIX2 | Hz | RW; GG | 44 Hz bis 65 Hz | Nennfrequenz | `homie/sma-inverter3/registers/r40135` |
| 40428 | `GridGuard.Cntry.FrqCtl.hhLim` | 2 × 16 Bit; U32/FIX2 | Hz | RW; GG | 50 Hz bis 65 Hz | Frequenzüberwachung mittlere Maximalschwelle | `homie/sma-inverter3/registers/r40428` |
| 40430 | `GridGuard.Cntry.FrqCtl.hhLimTmms` | 2 × 16 Bit; U32/FIX0 | ms | RW; GG | 20 ms bis 720000 ms | Frequenzüberwachung mittlere Maximalschwelle Auslösezeit | `homie/sma-inverter3/registers/r40430` |
| 40432 | `GridGuard.Cntry.FrqCtl.hLim` | 2 × 16 Bit; U32/FIX2 | Hz | RW; GG | 50 Hz bis 65 Hz | Frequenzüberwachung untere Maximalschwelle | `homie/sma-inverter3/registers/r40432` |
| 40434 | `GridGuard.Cntry.FrqCtl.hLimTmms` | 2 × 16 Bit; U32/FIX0 | ms | RW; GG | 0 ms bis 720000 ms | Frequenzüberwachung untere Maximalschwelle Auslösezeit | `homie/sma-inverter3/registers/r40434` |
| 40436 | `GridGuard.Cntry.FrqCtl.lLim` | 2 × 16 Bit; U32/FIX2 | Hz | RW; GG | 45 Hz bis 60 Hz | Frequenzüberwachung obere Minimalschwelle | `homie/sma-inverter3/registers/r40436` |
| 40438 | `GridGuard.Cntry.FrqCtl.lLimTmms` | 2 × 16 Bit; U32/FIX0 | ms | RW; GG | 0 ms bis 720000 ms | Frequenzüberwachung obere Minimalschwelle Auslösezeit | `homie/sma-inverter3/registers/r40438` |
| 40440 | `GridGuard.Cntry.FrqCtl.llLim` | 2 × 16 Bit; U32/FIX2 | Hz | RW; GG | 45 Hz bis 65 Hz | Frequenzüberwachung mittlere Minimalschwelle | `homie/sma-inverter3/registers/r40440` |
| 40442 | `GridGuard.Cntry.FrqCtl.llLimTmms` | 2 × 16 Bit; U32/FIX0 | ms | RW; GG | 20 ms bis 720000 ms | Frequenzüberwachung mittlere Minimalschwelle Auslösezeit | `homie/sma-inverter3/registers/r40442` |
| 40448 | `GridGuard.Cntry.VolCtl.hhLim` | 2 × 16 Bit; U32/FIX2 | V | RW; GG | 100 V bis 300 V | Spannungsüberwachung mittlere Maximalschwelle | `homie/sma-inverter3/registers/r40448` |
| 40450 | `GridGuard.Cntry.VolCtl.hhLimTmms` | 2 × 16 Bit; U32/FIX0 | ms | RW; GG | 0 ms bis 720000 ms | Spannungsüberwachung mittlere Maximalschwelle Auslösezeit | `homie/sma-inverter3/registers/r40450` |
| 40452 | `GridGuard.Cntry.VolCtl.hLim` | 2 × 16 Bit; U32/FIX2 | V | RW; GG | 100 V bis 295 V | Spannungsüberwachung untere Maximalschwelle | `homie/sma-inverter3/registers/r40452` |
| 40456 | `GridGuard.Cntry.VolCtl.hLimTmms` | 2 × 16 Bit; U32/FIX0 | ms | RW; GG | 0 ms bis 720000 ms | Spannungsüberwachung untere Maximalschwelle Auslösezeit | `homie/sma-inverter3/registers/r40456` |
| 40458 | `GridGuard.Cntry.VolCtl.lLim` | 2 × 16 Bit; U32/FIX2 | V | RW; GG | 45 V bis 230 V | Spannungsüberwachung obere Minimalschwelle | `homie/sma-inverter3/registers/r40458` |
| 40462 | `GridGuard.Cntry.VolCtl.lLimTmms` | 2 × 16 Bit; U32/FIX0 | ms | RW; GG | 0 ms bis 720000 ms | Spannungsüberwachung obere Minimalschwelle Auslösezeit | `homie/sma-inverter3/registers/r40462` |
| 40464 | `GridGuard.Cntry.VolCtl.llLim` | 2 × 16 Bit; U32/FIX2 | V | RW; GG | 0 V bis 230 V | Spannungsüberwachung mittlere Minimalschwelle | `homie/sma-inverter3/registers/r40464` |
| 40466 | `GridGuard.Cntry.VolCtl.llLimTmms` | 2 × 16 Bit; U32/FIX0 | ms | RW; GG | 0 ms bis 720000 ms | Spannungsüberwachung mittlere Minimalschwelle Auslösezeit | `homie/sma-inverter3/registers/r40466` |
| 40470 | `GridGuard.Cntry.Aid.Stt` | 2 × 16 Bit; U32/TAGLIST | — | RW; GG | Codes: 303: Aus (Off) 308: Ein (On) | Status der Inselnetzerkennung | `homie/sma-inverter3/registers/r40470` |
| 41111 | `GridGuard.Cntry.VolCtl.MinEff` | 2 × 16 Bit; U32/FIX2 | V | RW; GG | 45 V bis 230 V | Spannungsüberwachung untere Minimalschwelle als Effektivwert | `homie/sma-inverter3/registers/r41111` |
| 41113 | `GridGuard.Cntry.VolCtl.MinEffTmms` | 2 × 16 Bit; U32/FIX0 | ms | RW; GG | 20 ms bis 720000 ms | Spannungsüberwachung untere Minimalschwelle als Effektivwert Auslösezeit | `homie/sma-inverter3/registers/r41113` |
| 41115 | `GridGuard.Cntry.VolCtl.MaxEff` | 2 × 16 Bit; U32/FIX2 | V | RW; GG | 240 V bis 300 V | Spannungsüberwachung obere Maximalschwelle als Effektivwert | `homie/sma-inverter3/registers/r41115` |
| 41117 | `GridGuard.Cntry.VolCtl.MaxEffTmms` | 2 × 16 Bit; U32/FIX0 | ms | RW; GG | 20 ms bis 720000 ms | Spannungsüberwachung obere Maximalschwelle als Effektivwert Auslösezeit | `homie/sma-inverter3/registers/r41117` |
| 41121 | `GridGuard.CntrySet` | 2 × 16 Bit; U32/FUNKTION_SEC | — | RW; GG | nicht angegeben | Setze Ländernorm | X: kein reguläres Topic |
| 41123 | `GridGuard.Cntry.VolCtl.ReconMin` | 2 × 16 Bit; U32/FIX2 | V | RW; GG | 45 V bis 240 V | Min. Spannung zur Wiederzuschaltung | `homie/sma-inverter3/registers/r41123` |
| 41125 | `GridGuard.Cntry.VolCtl.ReconMax` | 2 × 16 Bit; U32/FIX2 | V | RW; GG | 100 V bis 295 V | Max. Spannung zur Wiederzuschaltung | `homie/sma-inverter3/registers/r41125` |
| 41127 | `GridGuard.Cntry.FrqCtl.ReconMin` | 2 × 16 Bit; U32/FIX2 | Hz | RW; GG | 44 Hz bis 60 Hz | Untere Frequenz für Wiederzuschaltung | `homie/sma-inverter3/registers/r41127` |
| 41129 | `GridGuard.Cntry.FrqCtl.ReconMax` | 2 × 16 Bit; U32/FIX2 | Hz | RW; GG | 50 Hz bis 65 Hz | Obere Frequenz für Wiederzuschaltung | `homie/sma-inverter3/registers/r41129` |
| 41169 | `GridGuard.Cntry.LeakRisMin` | 2 × 16 Bit; U32/FIX0 | Ohm | RW; GG | 50000 Ω bis 3000000 Ω | Minimaler Isolationswiderstand | `homie/sma-inverter3/registers/r41169` |

### Wechselrichterregelung und Kennlinien

| Register | SMA-Objekt | Typ / Format | Unit | Quellenzugriff | Bereich / Optionen | Kurzbeschreibung | MQTT-Topic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 30231 | `Inverter.WLim` | 2 × 16 Bit; U32/FIX0 | W | RO | 0 W bis 5050 W | Maximale Gerätewirkleistung | `homie/sma-inverter3/measurements/max-power` |
| 30233 | `Inverter.WMax` | 2 × 16 Bit; U32/FIX0 | W | RO | 0 W bis 5050 W | Eingestellte Wirkleistungsgrenze | `homie/sma-inverter3/measurements/set-max-power` |
| 30825 | `Inverter.VArModCfg.VArMod` | 2 × 16 Bit; U32/TAGLIST | — | RO; GG | Codes: 303: Aus (Off) 1070: Blindleistung Q, direkte Vorgabe (VArCnstNom) 1072: Blindleistung Q, Vorgabe durch Anlagensteuerung (VArCtlCom) 1074: cos Phi, direkte Vorgabe (PFCnst) 1075: cos Phi, Vorgabe durch Anlagensteuerung (PFCtlCom) 1076: cos Phi(P)-Kennlinie (PFCtlW) 2269: Blindleistung-Kennlinienmodus (CrvMod) 2270: cos Phi- oder Q-Vorgabe durch Anlagensteuerung (VArPFCtlCom) | Betriebsart der statischen Spannungshaltung, Konfiguration der statischen Spannungshaltung | `homie/sma-inverter3/registers/r30825` |
| 30829 | `Inverter.VArModCfg.VArCnstCfg.VArNom` | 2 × 16 Bit; S32/FIX1 | % | RO; GG | -60 % bis 60 % | Blindleistungssollwert in % | `homie/sma-inverter3/registers/r30829` |
| 30831 | `Inverter.VArModCfg.PFCnstCfg.PF` | 2 × 16 Bit; S32/FIX2 | — | RO; GG | 0.8 bis 1.0 | Sollwert des cos Phi, Konfiguration des cos Phi, direkte Vorgabe | `homie/sma-inverter3/registers/r30831` |
| 30833 | `Inverter.VArModCfg.PFCnstCfg.PFExt` | 2 × 16 Bit; U32/TAGLIST | — | RO; GG | Codes: 1041: Übererregt (OvExt) 1042: Untererregt (UnExt) | Erregungsart des cos Phi, Konfiguration des cos Phi, direkte Vorgabe | `homie/sma-inverter3/registers/r30833` |
| 30835 | `Inverter.WModCfg.WMod` | 2 × 16 Bit; U32/TAGLIST | — | RO; GG | Codes: 303: Aus (Off) 1077: Wirkleistungsbegrenzung P in W (WCnst) 1078: Wirkleistungsbegrenzung P in % Pmax (WCnstNom) 1079: Wirkleistungsbegrenzung P durch Anlagensteuerung (WCtlCom) | Betriebsart des Einspeisemanagements | `homie/sma-inverter3/registers/r30835` |
| 30837 | `Inverter.WModCfg.WCnstCfg.W` | 2 × 16 Bit; U32/FIX0 | W | RO; GG | 0 W bis 5050 W | Wirkleistungsbegrenzung in W | `homie/sma-inverter3/registers/r30837` |
| 30839 | `Inverter.WModCfg.WCnstCfg.WNom` | 2 × 16 Bit; U32/FIX0 | % | RO; GG | 0 % bis 100 % | Wirkleistungsbegrenzung in % | `homie/sma-inverter3/registers/r30839` |
| 30975 | `Inverter.DclVol` | 2 × 16 Bit; S32/FIX2 | V | RO | nicht angegeben | Zwischenkreisspannung | `homie/sma-inverter3/registers/r30975` |
| 40015 | `Inverter.VArModCfg.VArCtlComCfg.VArNom` | 1 × 16 Bit; S16/FIX1 | % | W | nicht angegeben | Normierte Blindleistungsbegrenzung durch Anlagensteuerung | X: kein reguläres Topic |
| 40016 | `Inverter.WModCfg.WCtlComCfg.WNom` | 1 × 16 Bit; S16/FIX0 | % | W | nicht angegeben | Normierte Wirkleistungsbegrenzung durch Anlagensteuerung | X: kein reguläres Topic |
| 40018 | `Inverter.FstStop` | 2 × 16 Bit; U32/TAGLIST | — | W | Codes: 381: Stopp (Stop) 1467: Start (Str) | Schnellabschaltung | X: kein reguläres Topic |
| 40022 | `Inverter.VArModCfg.VArCtlComCfg.VArNomPrc` | 1 × 16 Bit; S16/FIX2 | % | W | -60 % bis 60 % | Normierte Blindleistungsbegrenzung durch Anlagensteuerung | X: kein reguläres Topic |
| 40023 | `Inverter.WModCfg.WCtlComCfg.WNomPrc` | 1 × 16 Bit; S16/FIX2 | % | W | 0 % bis 100 % | Normierte Wirkleistungsbegrenzung durch Anlagensteuerung | X: kein reguläres Topic |
| 40024 | `Inverter.VArModCfg.PFCtlComCfg.PF` | 1 × 16 Bit; U16/FIX4 | — | W | nicht angegeben | Verschiebungsfaktor durch Anlagensteuerung | X: kein reguläres Topic |
| 40025 | `Inverter.VArModCfg.PFCtlComCfg.PFExt` | 2 × 16 Bit; U32/TAGLIST | — | W | Codes: nicht angegeben | Erregungsart durch Anlagensteuerung | X: kein reguläres Topic |
| 40183 | `Inverter.OutPhs` | 2 × 16 Bit; U32/TAGLIST | — | RW | Codes: 325: Phase L1 (phsA) 327: Phase L2 (phsB) 329: Phase L3 (phsC) | Phasenzuordnung | `homie/sma-inverter3/registers/r40183` |
| 40185 | `Inverter.VALim` | 2 × 16 Bit; U32/FIX0 | VA | RO | 0 VA bis 5050 VA | Maximale Gerätescheinleistung | `homie/sma-inverter3/registers/r40185` |
| 40195 | `Inverter.VAMax` | 2 × 16 Bit; U32/FIX0 | VA | RW | 0 VA bis 5050 VA | Eingestellte Scheinleistungsgrenze | `homie/sma-inverter3/registers/r40195` |
| 40200 | `Inverter.VArModCfg.VArMod` | 2 × 16 Bit; U32/TAGLIST | — | RW; GG | Codes: 303: Aus (Off) 1070: Blindleistung Q, direkte Vorgabe (VArCnstNom) 1072: Blindleistung Q, Vorgabe durch Anlagensteuerung (VArCtlCom) 1074: cos Phi, direkte Vorgabe (PFCnst) 1075: cos Phi, Vorgabe durch Anlagensteuerung (PFCtlCom) 1076: cos Phi(P)-Kennlinie (PFCtlW) 2269: Blindleistung-Kennlinienmodus (CrvMod) 2270: cos Phi- oder Q-Vorgabe durch Anlagensteuerung (VArPFCtlCom) | Betriebsart der statischen Spannungshaltung, Konfiguration der statischen Spannungshaltung | `homie/sma-inverter3/registers/r40200` |
| 40204 | `Inverter.VArModCfg.VArCnstCfg.VArNom` | 2 × 16 Bit; S32/FIX1 | % | RW; GG | -60 % bis 60 % | Blindleistungssollwert in % | `homie/sma-inverter3/registers/r40204` |
| 40206 | `Inverter.VArModCfg.PFCnstCfg.PF` | 2 × 16 Bit; S32/FIX2 | — | RW; GG | 0.8 bis 1.0 | Sollwert des cos Phi, Konfiguration des cos Phi, direkte Vorgabe | `homie/sma-inverter3/registers/r40206` |
| 40208 | `Inverter.VArModCfg.PFCnstCfg.PFExt` | 2 × 16 Bit; U32/TAGLIST | — | RW; GG | Codes: 1041: Übererregt (OvExt) 1042: Untererregt (UnExt) | Erregungsart des cos Phi, Konfiguration des cos Phi, direkte Vorgabe | `homie/sma-inverter3/registers/r40208` |
| 40210 | `Inverter.WModCfg.WMod` | 2 × 16 Bit; U32/TAGLIST | — | RW; GG | Codes: 303: Aus (Off) 1077: Wirkleistungsbegrenzung P in W (WCnst) 1078: Wirkleistungsbegrenzung P in % Pmax (WCnstNom) 1079: Wirkleistungsbegrenzung P durch Anlagensteuerung (WCtlCom) | Betriebsart des Einspeisemanagements | `homie/sma-inverter3/registers/r40210` |
| 40212 | `Inverter.WModCfg.WCnstCfg.W` | 2 × 16 Bit; U32/FIX0 | W | RW; GG | 0 W bis 5050 W | Wirkleistungsbegrenzung in W | `homie/sma-inverter3/registers/r40212` |
| 40214 | `Inverter.WModCfg.WCnstCfg.WNom` | 2 × 16 Bit; U32/FIX0 | % | RW; GG | 0 % bis 100 % | Wirkleistungsbegrenzung in % | `homie/sma-inverter3/registers/r40214` |
| 40216 | `Inverter.WCtlHzModCfg.WCtlHzMod` | 2 × 16 Bit; U32/TAGLIST | — | RW; GG | Codes: 303: Aus (Off) 1132: Linearer Gradient der Momentanleistung (WCtlHz) | Betriebsart der Wirkleistungsreduktion bei Überfrequenz P(f) | `homie/sma-inverter3/registers/r40216` |
| 40218 | `Inverter.WCtlHzModCfg.WCtlHzCfg.HzStr` | 2 × 16 Bit; U32/FIX2 | Hz | RW; GG | 45 Hz bis 65 Hz | Abstand der Startfrequenz zur Netzfrequenz, Konfiguration des linearen Gradienten der Momentanleistung | `homie/sma-inverter3/registers/r40218` |
| 40220 | `Inverter.WCtlHzModCfg.WCtlHzCfg.HzStop` | 2 × 16 Bit; U32/FIX2 | Hz | RW; GG | 45 Hz bis 65 Hz | Abstand der Rücksetzfrequenz zur Netzfrequenz, Konfiguration des linearen Gradienten der Momentanleistung | `homie/sma-inverter3/registers/r40220` |
| 40222 | `Inverter.VArModCfg.PFCtlWCfg.PFStr` | 2 × 16 Bit; U32/FIX2 | — | RW; GG | 0.8 bis 1.0 | cos Phi des Startpunktes, Konfiguration der cos Phi(P)-Kennlinie | `homie/sma-inverter3/registers/r40222` |
| 40224 | `Inverter.VArModCfg.PFCtlWCfg.PFExtStr` | 2 × 16 Bit; U32/TAGLIST | — | RW; GG | Codes: 1041: Übererregt (OvExt) 1042: Untererregt (UnExt) | Erregungsart des Startpunktes, Konfiguration der cos Phi(P)-Kennlinie | `homie/sma-inverter3/registers/r40224` |
| 40226 | `Inverter.VArModCfg.PFCtlWCfg.PFStop` | 2 × 16 Bit; U32/FIX2 | — | RW; GG | 0.8 bis 1.0 | cos Phi des Endpunktes, Konfiguration der cos Phi(P)-Kennlinie | `homie/sma-inverter3/registers/r40226` |
| 40228 | `Inverter.VArModCfg.PFCtlWCfg.PFExtStop` | 2 × 16 Bit; U32/TAGLIST | — | RW; GG | Codes: 1041: Übererregt (OvExt) 1042: Untererregt (UnExt) | Erregungsart des Endpunktes, Konfiguration der cos Phi(P)-Kennlinie | `homie/sma-inverter3/registers/r40228` |
| 40230 | `Inverter.VArModCfg.PFCtlWCfg.WNomStr` | 2 × 16 Bit; U32/FIX0 | % | RW; GG | 0 % bis 100 % | Wirkleistung des Startpunktes, Konfiguration der cos Phi(P)-Kennlinie | `homie/sma-inverter3/registers/r40230` |
| 40232 | `Inverter.VArModCfg.PFCtlWCfg.WNomStop` | 2 × 16 Bit; U32/FIX0 | % | RW; GG | 0 % bis 100 % | Wirkleistung des Endpunktes, Konfiguration der cos Phi(P)-Kennlinie | `homie/sma-inverter3/registers/r40232` |
| 40238 | `Inverter.WCtlHzModCfg.WCtlHzCfg.WGra` | 2 × 16 Bit; U32/FIX0 | % | RW; GG | 1 % bis 100 % | Wirkleistungsgradient, Konfiguration des linearen Gradienten der Momentanleistung | `homie/sma-inverter3/registers/r40238` |
| 40240 | `Inverter.WCtlHzModCfg.WCtlHzCfg.HystEna` | 2 × 16 Bit; U32/TAGLIST | — | RW; GG | Codes: 303: Aus (Off) 308: Ein (On) | Aktivierung der Schleppzeigerfunktion, Konfiguration des linearen Gradienten der Momentanleistung | `homie/sma-inverter3/registers/r40240` |
| 40242 | `Inverter.WCtlHzModCfg.WCtlHzCfg.HzStopWGra` | 2 × 16 Bit; U32/FIX0 | % | RW; GG | 1 % bis 10000 % | Wirkleistungsgradient nach Rücksetzfrequenz, Konfiguration des linearen Gradienten der Momentanleistung | `homie/sma-inverter3/registers/r40242` |
| 40484 | `Inverter.WGraEna` | 2 × 16 Bit; U32/TAGLIST | — | RW; GG | Codes: 303: Aus (Off) 308: Ein (On) | Aktivierung des Wirkleistungsgradienten | `homie/sma-inverter3/registers/r40484` |
| 40915 | `Inverter.WMax` | 2 × 16 Bit; U32/FIX0 | W | RW | 0 W bis 5050 W | Eingestellte Wirkleistungsgrenze | `homie/sma-inverter3/registers/r40915` |
| 40999 | `Inverter.VArModCfg.PFCtlComCfg.PFEEI` | 2 × 16 Bit; S32/FIX4 | — | W | 80 bis 100 | Sollwert cos(Phi) gemäß EEI-Konvention | X: kein reguläres Topic |
| 41017 | `Inverter.UtilCrvCfg.Crv.CrvTms` | 2 × 16 Bit; U32/FIX1 | s | RW; GG | 0 s bis 60 s | Einstellzeit des Kennlinienarbeitspunktes, Konf. der Netzintegrationskennlinie 1 | `homie/sma-inverter3/registers/r41017` |
| 41023 | `Inverter.UtilCrvCfg.Crv.NumPt` | 2 × 16 Bit; U32/FIX0 | — | RW; GG | 4 bis 4 | Anzahl zu verwendender Punkte, Konfiguration der Netzintegrationskennlinie 1 | `homie/sma-inverter3/registers/r41023` |
| 41025 | `Inverter.UtilCrvCfg.Crv.XRef` | 2 × 16 Bit; U32/TAGLIST | — | RW; GG | Codes: 1976: Spannung in Prozent von Un (XRefVNom) | X-Achsen-Referenz, Konf. der Netzintegrationskennlinie 1 | `homie/sma-inverter3/registers/r41025` |
| 41027 | `Inverter.UtilCrvCfg.Crv.YRef` | 2 × 16 Bit; U32/TAGLIST | — | RW; GG | Codes: 1977: Var in Prozent von Pmax (YRefVarNom) | Y-Achsen-Referenz, Konf. der Netzintegrationskennlinie 1 | `homie/sma-inverter3/registers/r41027` |
| 41029 | `Inverter.UtilCrvCfg.Crv.XVal1` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | 50 bis 150 | X-Wert 1, Konfiguration der Netzintegrationskennlinie 1 | `homie/sma-inverter3/registers/r41029` |
| 41031 | `Inverter.UtilCrvCfg.Crv.YVal1` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | -60 bis 60 | Y-Wert 1, Konfiguration der Netzintegrationskennlinie 1 | `homie/sma-inverter3/registers/r41031` |
| 41033 | `Inverter.UtilCrvCfg.Crv.XVal2` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | 50 bis 150 | X-Wert 2, Konfiguration der Netzintegrationskennlinie 1 | `homie/sma-inverter3/registers/r41033` |
| 41035 | `Inverter.UtilCrvCfg.Crv.YVal2` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | -60 bis 60 | Y-Wert 2, Konfiguration der Netzintegrationskennlinie 1 | `homie/sma-inverter3/registers/r41035` |
| 41037 | `Inverter.UtilCrvCfg.Crv.XVal3` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | 50 bis 150 | X-Wert 3, Konfiguration der Netzintegrationskennlinie 1 | `homie/sma-inverter3/registers/r41037` |
| 41039 | `Inverter.UtilCrvCfg.Crv.YVal3` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | -60 bis 60 | Y-Wert 3, Konfiguration der Netzintegrationskennlinie 1 | `homie/sma-inverter3/registers/r41039` |
| 41041 | `Inverter.UtilCrvCfg.Crv.XVal4` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | 50 bis 150 | X-Wert 4, Konfiguration der Netzintegrationskennlinie 1 | `homie/sma-inverter3/registers/r41041` |
| 41043 | `Inverter.UtilCrvCfg.Crv.YVal4` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | -60 bis 60 | Y-Wert 4, Konfiguration der Netzintegrationskennlinie 1 | `homie/sma-inverter3/registers/r41043` |
| 41061 | `Inverter.UtilCrvCfg.CrvModCfg2.CrvNum` | 2 × 16 Bit; U32/FIX0 | — | RW; GG | 2 bis 2 | 2. Kennliniennummer, Konfiguration des Kennlinienmodus | `homie/sma-inverter3/registers/r41061` |
| 41063 | `Inverter.UtilCrvCfg.CrvModCfg2.CrvEna` | 2 × 16 Bit; U32/TAGLIST | — | RW; GG | Codes: 303: Aus (Off) 308: Ein (On) | 2. Aktivierung der Kennlinie, Konfiguration des Kennlinienmodus | `homie/sma-inverter3/registers/r41063` |
| 41065 | `Inverter.UtilCrvCfg.Crv2.CrvTms` | 2 × 16 Bit; U32/FIX1 | s | RW; GG | 0 s bis 60 s | Einstellzeit des Kennlinienarbeitspunktes, Konfiguration der Netzintegrationskennlinie 2 | `homie/sma-inverter3/registers/r41065` |
| 41071 | `Inverter.UtilCrvCfg.Crv2.NumPt` | 2 × 16 Bit; U32/FIX0 | — | RW; GG | 4 bis 4 | Anzahl zu verwendender Punkte, Konfiguration der Netzintegrationskennlinie 2 | `homie/sma-inverter3/registers/r41071` |
| 41073 | `Inverter.UtilCrvCfg.Crv2.XRef` | 2 × 16 Bit; U32/TAGLIST | — | RW; GG | Codes: 1976: Spannung in Prozent von Un (XRefVNom) | Eingangseinheit, Konfiguration der Netzintegrationskennlinie 2 | `homie/sma-inverter3/registers/r41073` |
| 41075 | `Inverter.UtilCrvCfg.Crv2.YRef` | 2 × 16 Bit; U32/TAGLIST | — | RW; GG | Codes: 1978: Watt in Prozent von Pmax (YRefWNom) | Ausgangsreferenz, Konfiguration der Netzintegrationskennlinie 2 | `homie/sma-inverter3/registers/r41075` |
| 41077 | `Inverter.UtilCrvCfg.Crv2.XVal1` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | 50 bis 150 | X-Wert 1, Konfiguration der Netzintegrationskennlinie 2 | `homie/sma-inverter3/registers/r41077` |
| 41079 | `Inverter.UtilCrvCfg.Crv2.YVal1` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | 0 bis 100 | Y-Wert 1, Konfiguration der Netzintegrationskennlinie 2 | `homie/sma-inverter3/registers/r41079` |
| 41081 | `Inverter.UtilCrvCfg.Crv2.XVal2` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | 50 bis 150 | X-Wert 2, Konfiguration der Netzintegrationskennlinie 2 | `homie/sma-inverter3/registers/r41081` |
| 41083 | `Inverter.UtilCrvCfg.Crv2.YVal2` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | 0 bis 100 | Y-Wert 2, Konfiguration der Netzintegrationskennlinie 2 | `homie/sma-inverter3/registers/r41083` |
| 41085 | `Inverter.UtilCrvCfg.Crv2.XVal3` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | 50 bis 150 | X-Wert 3, Konfiguration der Netzintegrationskennlinie 2 | `homie/sma-inverter3/registers/r41085` |
| 41087 | `Inverter.UtilCrvCfg.Crv2.YVal3` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | 0 bis 100 | Y-Wert 3, Konfiguration der Netzintegrationskennlinie 2 | `homie/sma-inverter3/registers/r41087` |
| 41089 | `Inverter.UtilCrvCfg.Crv2.XVal4` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | 50 bis 150 | X-Wert 4, Konfiguration der Netzintegrationskennlinie 2 | `homie/sma-inverter3/registers/r41089` |
| 41091 | `Inverter.UtilCrvCfg.Crv2.YVal4` | 2 × 16 Bit; S32/FIX3 | — | RW; GG | 0 bis 100 | Y-Wert 4, Konfiguration der Netzintegrationskennlinie 2 | `homie/sma-inverter3/registers/r41091` |
| 41193 | `Inverter.CtlComCfg.WCtlCom.CtlComMssMod` | 2 × 16 Bit; U32/TAGLIST | — | RW | Codes: 2506: Werte beibehalten (UsStp) 2507: Verwendung Fallback-Einstellung (UsFlb) | Betriebsart für ausbleibende Wirkleistungsbegrenzung | `homie/sma-inverter3/registers/r41193` |
| 41195 | `Inverter.CtlComCfg.WCtlCom.TmsOut` | 2 × 16 Bit; U32/Dauer | s | RW | 1 s bis 86400 s | Timeout für ausbleibende Wirkleistungsbegrenzung | `homie/sma-inverter3/registers/r41195` |
| 41197 | `Inverter.CtlComCfg.WCtlCom.FlbWNom` | 2 × 16 Bit; U32/FIX2 | % | RW | 0 % bis 100 % | Fallback Wirkleistungsbegrenzung P in % von WMax für ausbleibende Wirkleistungsbegrenzung | `homie/sma-inverter3/registers/r41197` |
| 41219 | `Inverter.CtlComCfg.VArCtlCom.CtlComMssMod` | 2 × 16 Bit; U32/TAGLIST | — | RW | Codes: 2506: Werte beibehalten (UsStp) 2507: Verwendung Fallback-Einstellung (UsFlb) | Betriebsart für ausbleibende Blindleistungsregelung | `homie/sma-inverter3/registers/r41219` |
| 41221 | `Inverter.CtlComCfg.VArCtlCom.TmsOut` | 2 × 16 Bit; U32/Dauer | s | RW | 1 s bis 86400 s | Timeout für ausbleibende Blindleistungsregelung | `homie/sma-inverter3/registers/r41221` |
| 41223 | `Inverter.CtlComCfg.VArCtlCom.FlbVArNom` | 2 × 16 Bit; S32/FIX2 | % | RW | -50 % bis 50 % | Fallback Blindleistung Q in % von WMax für ausbleibende Blindleistungsregelung | `homie/sma-inverter3/registers/r41223` |
| 41225 | `Inverter.CtlComCfg.PFCtlCom.CtlComMssMod` | 2 × 16 Bit; U32/TAGLIST | — | RW | Codes: 2506: Werte beibehalten (UsStp) 2507: Verwendung Fallback-Einstellung (UsFlb) | Betriebsart für ausbleibende cos Phi-Vorgabe | `homie/sma-inverter3/registers/r41225` |
| 41227 | `Inverter.CtlComCfg.PFCtlCom.TmsOut` | 2 × 16 Bit; U32/Dauer | s | RW | 1 s bis 86400 s | Timeout für ausbleibende cos Phi-Vorgabe | `homie/sma-inverter3/registers/r41227` |
| 41229 | `Inverter.CtlComCfg.PFCtlCom.FlbPF` | 2 × 16 Bit; S32/FIX4 | — | RW | 0.8 bis 1 | Fallback cos Phi für ausbleibende cos Phi-Vorgabe | `homie/sma-inverter3/registers/r41229` |
| 41253 | `Inverter.FstStop` | 2 × 16 Bit; U32/TAGLIST | — | RW | Codes: 381: Stopp (Stop) 1467: Start (Str) | Schnellabschaltung | `homie/sma-inverter3/registers/r41253` |
| 41255 | `Inverter.WModCfg.WCtlComCfg.WNomPrc` | 1 × 16 Bit; S16/FIX2 | % | RW | 0 % bis 100 % | Normierte Wirkleistungsbegrenzung durch Anlagensteuerung | `homie/sma-inverter3/registers/r41255` |
| 41256 | `Inverter.VArModCfg.VArCtlComCfg.VArNomPrc` | 1 × 16 Bit; S16/FIX2 | % | RW | -60 % bis 60 % | Normierte Blindleistungsbegrenzung durch Anlagensteuerung | `homie/sma-inverter3/registers/r41256` |
| 41257 | `Inverter.VArModCfg.PFCtlComCfg.PFEEI` | 2 × 16 Bit; S32/FIX4 | — | RW | 80 bis 100 | Sollwert cos(Phi) gemäß EEI-Konvention | `homie/sma-inverter3/registers/r41257` |

### Anlagenvorgaben und Kommunikation

| Register | SMA-Objekt | Typ / Format | Unit | Quellenzugriff | Bereich / Optionen | Kurzbeschreibung | MQTT-Topic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 30925 | `Spdwr.ComSocA.ConnSpd` | 2 × 16 Bit; U32/TAGLIST | — | RO | Codes: 1720: 10 Mbit/s (ConnSpd10) 1721: 100 Mbit/s (ConnSpd100) 3581: Keine Verbindungsgeschwindigkeit gesetzt (ConnSpdNone) | Verbindungsgeschwindigkeit von SMACOM A | `homie/sma-inverter3/registers/r30925` |
| 30927 | `Spdwr.ComSocA.DpxMode` | 2 × 16 Bit; U32/TAGLIST | — | RO | Codes: 1726: Halbduplex (HalfDpx) 1727: Vollduplex (FulDpx) 3582: Kein Duplexmodus gesetzt (DpxModNone) | Duplexmodus von SMACOM A | `homie/sma-inverter3/registers/r30927` |
| 30929 | `Spdwr.ComSocA.Stt` | 2 × 16 Bit; U32/TAGLIST | — | RO | Codes: 35: Fehler (Alm) 307: Ok (Ok) 455: Warnung (Wrn) 1725: Keine Verbindung (NotConn) | Speedwire-Verbindungsstatus von SMACOM A | `homie/sma-inverter3/registers/r30929` |
| 31017 | `Spdwr.ActlIp` | 8 × 16 Bit; STR32/UTF8 | — | RO | nicht angegeben | Aktuelle IP-Adresse. | X: kein reguläres Topic |
| 31025 | `Spdwr.ActlSnetMsk` | 8 × 16 Bit; STR32/UTF8 | — | RO | nicht angegeben | Aktuelle Subnetzmaske. | X: kein reguläres Topic |
| 31033 | `Spdwr.ActlGwIp` | 8 × 16 Bit; STR32/UTF8 | — | RO | nicht angegeben | Aktuelles Standardgateway. | X: kein reguläres Topic |
| 31041 | `Spdwr.ActlDnsSrvIp` | 8 × 16 Bit; STR32/UTF8 | — | RO | nicht angegeben | Aktueller DNS-Server. | X: kein reguläres Topic |
| 40157 | `Spdwr.AutoCfgIsOn` | 2 × 16 Bit; U32/TAGLIST | — | RW | Codes: 1129: Ja (Yes) 1130: Nein (No) | Automatische Speedwire-Konfiguration eingeschaltet | `homie/sma-inverter3/registers/r40157` |
| 40159 | `Spdwr.Ip` | 8 × 16 Bit; STR32/IP4 | — | RW | nicht angegeben | Konfigurierte IP-Adresse. | X: kein reguläres Topic |
| 40167 | `Spdwr.SnetMsk` | 8 × 16 Bit; STR32/IP4 | — | RW | nicht angegeben | Konfigurierte Subnetzmaske. | X: kein reguläres Topic |
| 40175 | `Spdwr.GwIp` | 8 × 16 Bit; STR32/IP4 | — | RW | nicht angegeben | Konfiguriertes Standardgateway. | X: kein reguläres Topic |
| 40513 | `Spdwr.DnsSrvIp` | 8 × 16 Bit; STR32/IP4 | — | RW | nicht angegeben | Konfigurierter DNS-Server. | X: kein reguläres Topic |
| 41199 | `PCC.WMaxNom` | 2 × 16 Bit; U32/FIX0 | % | RW | 0 % bis 100 % | Eingestellte Wirkleistungsgrenze am Netzanschlusspunkt | `homie/sma-inverter3/registers/r41199` |
| 41203 | `Plnt.DcWRtg` | 2 × 16 Bit; U32/FIX0 | W | RW | 0 W bis 500000 W | Anlagen-Nennleistung | `homie/sma-inverter3/registers/r41203` |
| 41217 | `PCC.WMax` | 2 × 16 Bit; U32/FIX0 | W | RW | 0 W bis 500000 W | Eingestellte Wirkleistungsgrenze am Netzanschlusspunkt | `homie/sma-inverter3/registers/r41217` |

## SunSpec-Zuordnungen

S01 hat für **63 SMA-Einträge** zusätzlich SunSpec-Entsprechungen, teils mehrere pro Eintrag. Diese Tabelle enthält sämtliche belegten Zuordnungszellen. Mehrere Angaben in einer Zelle entsprechen der Reihenfolge der Herstellerliste. Sie sind Alternativrepräsentationen derselben Funktion; das Zustands-Topic bleibt gleich. SunSpec-Modelladressen und Skalierungsfaktor-Register müssen vor Verwendung am Gerät bestätigt werden.

SunSpec verwendet die konfigurierte SMA-Unit-ID + 123 (bei SMA-Unit 3 also 126), Adressspalte −1 und eigene Datentypen/NaN-Regeln. Numerische Werte mit `sunssf` als Rohwert × 10^SF dekodieren; ein fehlender SF-Eintrag ist keine Lizenz, SMA-FIX-Skalierung zu übernehmen. `acc32`/`acc64` besitzen besondere NaN-/Zählerregeln; nicht pauschal wie SMA-U32/U64 behandeln. Modell 101 bezeichnet ein einphasiges Invertermodell, auch wenn die Gerätefamilientabelle weitere Phasenspalten enthält. Für das konkrete Modell ausschließlich tatsächlich vorhandene Werte veröffentlichen.

| SMA-Register | SunSpec-Adresse laut Liste | Name | Modell | Registerzahl | Datentyp | SF-Register | Zugriff | MQTT-Topic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 30953 | 40219 | TmpCab | 101 | 1 | int16 | - | RO | `homie/sma-inverter3/registers/r30953` |
| 30769 | 40641 | DCA | 160 | 1 | uint16 | 40624 | RO | `homie/sma-inverter3/measurements/current-a-input` |
| 30957 | 40661 | DCA | 160 | 1 | uint16 | 40624 | RO | `homie/sma-inverter3/registers/r30957` |
| 30771 | 40642 | DCV | 160 | 1 | uint16 | 40625 | RO | `homie/sma-inverter3/measurements/voltage-a-input` |
| 30959 | 40662 | DCV | 160 | 1 | uint16 | 40625 | RO | `homie/sma-inverter3/registers/r30959` |
| 30773 | 40643 | DCW | 160 | 1 | uint16 | 40626 | RO | `homie/sma-inverter3/measurements/power-a-input` |
| 30961 | 40663 | DCW | 160 | 1 | uint16 | 40626 | RO | `homie/sma-inverter3/registers/r30961` |
| 40135 | 40286 | ECPNomHz | 121 | 1 | uint16 | 40297 | RW | `homie/sma-inverter3/registers/r40135` |
| 40448 | 40830 | V2 | 130 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r40448` |
| 40450 | 40829 | Tms2 | 130 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r40450` |
| 40452 | 40828 | V1 | 130 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r40452` |
| 40456 | 40827 | Tms1 | 130 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r40456` |
| 40464 | 40768 | V2 | 129 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r40464` |
| 40466 | 40767 | Tms2 | 129 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r40466` |
| 40458 | 40766 | V1 | 129 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r40458` |
| 40462 | 40765 | Tms1 | 129 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r40462` |
| 41111 | 40770 | V3 | 129 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r41111` |
| 41113 | 40769 | Tms3 | 129 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r41113` |
| 41115 | 40832 | V3 | 130 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r41115` |
| 41117 | 40831 | Tms3 | 130 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r41117` |
| 30783 | 40196 | PhVphA | 101 | 1 | uint16 | 40199 | RO | `homie/sma-inverter3/measurements/volt-g1` |
| 30785 | 40197 | PhVphB | 101 | 1 | uint16 | 40199 | RO | `homie/sma-inverter3/registers/r30785` |
| 30787 | 40198 | PhVphC | 101 | 1 | uint16 | 40199 | RO | `homie/sma-inverter3/registers/r30787` |
| 30977 | 40189 | AphA | 101 | 1 | int16 | 40192 | RO | `homie/sma-inverter3/registers/r30977` |
| 30979 | 40190 | AphB | 101 | 1 | int16 | 40192 | RO | `homie/sma-inverter3/registers/r30979` |
| 30981 | 40191 | AphC | 101 | 1 | int16 | 40192 | RO | `homie/sma-inverter3/registers/r30981` |
| 30803 | 40202 | Hz | 101 | 1 | uint16 | 40203 | RO | `homie/sma-inverter3/registers/r30803` |
| 30813 | 40204 | VA | 101 | 1 | int16 | 40205 | RO | `homie/sma-inverter3/registers/r30813` |
| 30805 | 40206 | VAr | 101 | 1 | int16 | 40207 | RO | `homie/sma-inverter3/registers/r30805` |
| 30775 | 40200 | W | 101 | 1 | int16 | 40201 | RO | `homie/sma-inverter3/measurements/active-power` |
| 41253 | 40348 | Conn | 123 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r41253` |
| 40183 | 40287 | ConnPh | 121 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r40183` |
| 40185 | 40243 | VARtg | 120 | 1 | uint16 | 40244 | RO | `homie/sma-inverter3/registers/r40185` |
| 40195 | 40273 | VAMax | 121 | 1 | uint16 | 40292 | RW | `homie/sma-inverter3/registers/r40195` |
| 41257 | 40354 | OutPFSet | 123 | 1 | int16 | 40368 | RW | `homie/sma-inverter3/registers/r41257` |
| 41256 | 40359 | VArWMaxPct | 123 | 1 | int16 | 40369 | RW | `homie/sma-inverter3/registers/r41256` |
| 40200 | 40366 40358 | VArPct_Ena OutPFSet_Ena | 123 123 | 1 1 | uint16 uint16 | - | RW RW | `homie/sma-inverter3/registers/r40200` |
| 40218 | 40465 | HzStr | 127 | 1 | int16 | 40471 | RW | `homie/sma-inverter3/registers/r40218` |
| 40220 | 40466 | HzStop | 127 | 1 | int16 | 40471 | RW | `homie/sma-inverter3/registers/r40220` |
| 40242 | 40469 | HzStopWGra | 127 | 1 | uint16 | 40472 | RW | `homie/sma-inverter3/registers/r40242` |
| 40240 | 40467 | HysEna | 127 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r40240` |
| 40238 | 40464 | WGra | 127 | 1 | uint16 | 40470 | RW | `homie/sma-inverter3/registers/r40238` |
| 40216 | 40468 | ModEna | 127 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r40216` |
| 30231 | 40241 | WRtg | 120 | 1 | uint16 | 40242 | RO | `homie/sma-inverter3/measurements/max-power` |
| 40915 | 40268 | WMax | 121 | 1 | uint16 | 40288 | RW | `homie/sma-inverter3/registers/r40915` |
| 41255 | 40349 | WMaxLimPct | 123 | 1 | uint16 | 40367 | RW | `homie/sma-inverter3/registers/r41255` |
| 40210 | 40353 | WMaxLim_Ena | 123 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r40210` |
| 30225 | 40342 | Ris | 122 | 1 | uint16 | 40343 | RO | `homie/sma-inverter3/registers/r30225` |
| 30513 | 40303 40210 | ActWh WH | 122 101 | 4 2 | acc64 acc32 | - 40212 | RO RO | `homie/sma-inverter3/registers/r30513` |
| 40497 | 40076 | MAC | 11 | 4 | uint64 | - | RO | X: kein reguläres Topic |
| 30053 | 40240 40037 | DERTyp Opt | 120 1 | 1 8 | uint16 string8 | - | RO RO | `homie/sma-inverter3/measurements/type` |
| 30059 | 40045 | Vr | 1 | 8 | string8 | - | RO | `homie/sma-inverter3/registers/r30059` |
| 40067 | 40053 | SN | 1 | 16 | string16 | - | RO | X: kein reguläres Topic |
| 30247 | 40690 40670 40650 40628 40226 | DCEvt DCEvt DCEvt Evt Evt1 | 160 160 160 160 101 | 2 2 2 2 2 | uint32 uint32 uint32 uint32 uint32 | - | RO RO RO RO RO | `homie/sma-inverter3/registers/r30247` |
| 30217 | 40300 | PVConn | 122 | 1 | uint16 | - | RO | `homie/sma-inverter3/measurements/grid-contactor` |
| 30929 | 40075 | St | 11 | 1 | uint16 | - | RO | `homie/sma-inverter3/registers/r30929` |
| 30925 | 40073 | Spd | 11 | 1 | uint16 | - | RO | `homie/sma-inverter3/registers/r30925` |
| 30927 | 40074 | CfgSt | 11 | 1 | uint16 | - | RO | `homie/sma-inverter3/registers/r30927` |
| 40157 | 40095 | Cfg | 12 | 1 | uint16 | - | RW | `homie/sma-inverter3/registers/r40157` |
| 40159 | 40097 | Addr | 12 | 8 | string8 | - | RW | X: kein reguläres Topic |
| 40167 | 40105 | Msk | 12 | 8 | string8 | - | RW | X: kein reguläres Topic |
| 40175 | 40113 | Gw | 12 | 8 | string8 | - | RW | X: kein reguläres Topic |
| 40513 | 40121 | DNS1 | 12 | 8 | string8 | - | RW | X: kein reguläres Topic |

## Home Manager: lokale Zählerwerte

Der integrierte Zähler liefert Werte seines **Anschlusspunkts**. Netzbezug ist nicht automatisch der gesamte Hausverbrauch; PV-Erzeugung und Batterie kommen aus anderen Quellen. Vorzeichen, saldierte Gesamtwerte und einzelne Phasen nicht miteinander verwechseln. Gesamtzähler verwenden; phasenweise Bezug und Einspeisung nicht als Ersatz für eine saldierte Gesamtmessung zusammenzählen.

W02 beschreibt 16 Standard-Channels: Wirkleistung und Wirkenergie für Bezug und Einspeisung, jeweils gesamt/L1/L2/L3. W03 liefert weitere Kanalnummern als **Kandidaten**, nicht als am eigenen Home Manager bestätigte Werte. Die folgende Tabelle benennt jede Kanalfamilie und beide getrennten Topics für Momentanwert und Zähler, wo vorhanden. Alle sind RO. Die Kurzbeschreibung gilt jeweils für den Anschlusspunkt.

Für den Adapter: bevorzugt variable OBIS-Blöcke statt feste Paketoffsets parsen, Protokoll-ID und Blocklänge prüfen, Quelle privat auswählen. Übliche Rohwertfaktoren aus W03: Leistung /10, Spannung/Strom/Frequenz /1000, Energie in Ws /3 600 000 zu kWh. Zusätzliche Blind-/Scheinenergie in entsprechende kVArh/kVAh. Faktor und tatsächliche Feldpräsenz mit einer bereinigten Telegrammprobe bestätigen. Der Decoder nennt cosφ eine Winkeleinheit; das ist **kein ausreichender Einheitenbeleg**. Leistungsfaktor muss anhand offizieller Kanalmetadaten/Telegramm geprüft werden und wird vorerst nicht als ° ausgegeben.

Default ist UDP 9522 an Multicast 239.12.255.254. S05 Seite 67 beschreibt auch direkte Zählerkommunikation: bei eingetragenen Zielgeräten entfallen die bisherigen Multicast-Telegramme. Das ist vor Docker-Netzwerkplanung zu prüfen. Speedwire-Verschlüsselung und Paketformat können die Lesbarkeit beeinflussen; keine Geräte- oder Netzwerkeinstellungen wurden geändert.

| SMA-Kanal / Typ / Tarif | Kurzbeschreibung | Unit Momentanwert / Zähler | Nachweis | MQTT-Topics |
| --- | --- | --- | --- | --- |
| 1.4.0 / 1.8.0 | Wirkbezug gesamt | W / kWh | D/W02 | `homie/sma-home-manager/measurements/power-import`; `homie/sma-home-manager/measurements/energy-import` |
| 2.4.0 / 2.8.0 | Wirkeinspeisung gesamt | W / kWh | D/W02 | `homie/sma-home-manager/measurements/power-export`; `homie/sma-home-manager/measurements/energy-export` |
| 3.4.0 / 3.8.0 | Blindbezug gesamt | VAr / kVArh | K/W03 | `homie/sma-home-manager/meter/reactive-power-import`; `homie/sma-home-manager/meter/reactive-energy-import` |
| 4.4.0 / 4.8.0 | Blindeinspeisung gesamt | VAr / kVArh | K/W03 | `homie/sma-home-manager/meter/reactive-power-export`; `homie/sma-home-manager/meter/reactive-energy-export` |
| 9.4.0 / 9.8.0 | Scheinbezug gesamt | VA / kVAh | K/W03 | `homie/sma-home-manager/meter/apparent-power-import`; `homie/sma-home-manager/meter/apparent-energy-import` |
| 10.4.0 / 10.8.0 | Scheineinspeisung gesamt | VA / kVAh | K/W03 | `homie/sma-home-manager/meter/apparent-power-export`; `homie/sma-home-manager/meter/apparent-energy-export` |
| 13.4.0 | Leistungsfaktor gesamt | offen | K/W03 | `homie/sma-home-manager/meter/power-factor` |
| 14.4.0 | Netzfrequenz | Hz | K/W03 | `homie/sma-home-manager/meter/frequency` |
| 21.4.0 / 21.8.0 | Wirkbezug L1 | W / kWh | D/W02 | `homie/sma-home-manager/meter/active-power-import-l1`; `homie/sma-home-manager/meter/active-energy-import-l1` |
| 22.4.0 / 22.8.0 | Wirkeinspeisung L1 | W / kWh | D/W02 | `homie/sma-home-manager/meter/active-power-export-l1`; `homie/sma-home-manager/meter/active-energy-export-l1` |
| 23.4.0 / 23.8.0 | Blindbezug L1 | VAr / kVArh | K/W03 | `homie/sma-home-manager/meter/reactive-power-import-l1`; `homie/sma-home-manager/meter/reactive-energy-import-l1` |
| 24.4.0 / 24.8.0 | Blindeinspeisung L1 | VAr / kVArh | K/W03 | `homie/sma-home-manager/meter/reactive-power-export-l1`; `homie/sma-home-manager/meter/reactive-energy-export-l1` |
| 29.4.0 / 29.8.0 | Scheinbezug L1 | VA / kVAh | K/W03 | `homie/sma-home-manager/meter/apparent-power-import-l1`; `homie/sma-home-manager/meter/apparent-energy-import-l1` |
| 30.4.0 / 30.8.0 | Scheineinspeisung L1 | VA / kVAh | K/W03 | `homie/sma-home-manager/meter/apparent-power-export-l1`; `homie/sma-home-manager/meter/apparent-energy-export-l1` |
| 31.4.0 | Strom L1 | A | K/W03 | `homie/sma-home-manager/meter/current-l1` |
| 32.4.0 | Spannung L1 | V | K/W03 | `homie/sma-home-manager/meter/voltage-l1` |
| 33.4.0 | Leistungsfaktor L1 | offen | K/W03 | `homie/sma-home-manager/meter/power-factor-l1` |
| 41.4.0 / 41.8.0 | Wirkbezug L2 | W / kWh | D/W02 | `homie/sma-home-manager/meter/active-power-import-l2`; `homie/sma-home-manager/meter/active-energy-import-l2` |
| 42.4.0 / 42.8.0 | Wirkeinspeisung L2 | W / kWh | D/W02 | `homie/sma-home-manager/meter/active-power-export-l2`; `homie/sma-home-manager/meter/active-energy-export-l2` |
| 43.4.0 / 43.8.0 | Blindbezug L2 | VAr / kVArh | K/W03 | `homie/sma-home-manager/meter/reactive-power-import-l2`; `homie/sma-home-manager/meter/reactive-energy-import-l2` |
| 44.4.0 / 44.8.0 | Blindeinspeisung L2 | VAr / kVArh | K/W03 | `homie/sma-home-manager/meter/reactive-power-export-l2`; `homie/sma-home-manager/meter/reactive-energy-export-l2` |
| 49.4.0 / 49.8.0 | Scheinbezug L2 | VA / kVAh | K/W03 | `homie/sma-home-manager/meter/apparent-power-import-l2`; `homie/sma-home-manager/meter/apparent-energy-import-l2` |
| 50.4.0 / 50.8.0 | Scheineinspeisung L2 | VA / kVAh | K/W03 | `homie/sma-home-manager/meter/apparent-power-export-l2`; `homie/sma-home-manager/meter/apparent-energy-export-l2` |
| 51.4.0 | Strom L2 | A | K/W03 | `homie/sma-home-manager/meter/current-l2` |
| 52.4.0 | Spannung L2 | V | K/W03 | `homie/sma-home-manager/meter/voltage-l2` |
| 53.4.0 | Leistungsfaktor L2 | offen | K/W03 | `homie/sma-home-manager/meter/power-factor-l2` |
| 61.4.0 / 61.8.0 | Wirkbezug L3 | W / kWh | D/W02 | `homie/sma-home-manager/meter/active-power-import-l3`; `homie/sma-home-manager/meter/active-energy-import-l3` |
| 62.4.0 / 62.8.0 | Wirkeinspeisung L3 | W / kWh | D/W02 | `homie/sma-home-manager/meter/active-power-export-l3`; `homie/sma-home-manager/meter/active-energy-export-l3` |
| 63.4.0 / 63.8.0 | Blindbezug L3 | VAr / kVArh | K/W03 | `homie/sma-home-manager/meter/reactive-power-import-l3`; `homie/sma-home-manager/meter/reactive-energy-import-l3` |
| 64.4.0 / 64.8.0 | Blindeinspeisung L3 | VAr / kVArh | K/W03 | `homie/sma-home-manager/meter/reactive-power-export-l3`; `homie/sma-home-manager/meter/reactive-energy-export-l3` |
| 69.4.0 / 69.8.0 | Scheinbezug L3 | VA / kVAh | K/W03 | `homie/sma-home-manager/meter/apparent-power-import-l3`; `homie/sma-home-manager/meter/apparent-energy-import-l3` |
| 70.4.0 / 70.8.0 | Scheineinspeisung L3 | VA / kVAh | K/W03 | `homie/sma-home-manager/meter/apparent-power-export-l3`; `homie/sma-home-manager/meter/apparent-energy-export-l3` |
| 71.4.0 | Strom L3 | A | K/W03 | `homie/sma-home-manager/meter/current-l3` |
| 72.4.0 | Spannung L3 | V | K/W03 | `homie/sma-home-manager/meter/voltage-l3` |
| 73.4.0 | Leistungsfaktor L3 | offen | K/W03 | `homie/sma-home-manager/meter/power-factor-l3` |
| 36864.0.0 | Version aus Telegramm | — | K/W03 | `homie/sma-home-manager/device/speedwire-version` |

## Home Manager: Modbus für Netzsystemdienstleistungen

S03 ist ausdrücklich ein **Modbus-Serverprofil** ab Softwarepaket 2.10. Es ist von der Modbus-Clientfunktion für beispielsweise Moxa-Schaltgeräte zu unterscheiden. Die NSD-Schnittstelle muss eingerichtet sein. Unit 1 ist für Home-Manager-Informationen/Anlagenübersicht reserviert, Unit 2 für Anlagenwerte, Unit 3–247 für untergeordnete Wechselrichter.

S03 Seiten 20–24 verlangt Grid-Guard-Anmeldung für Unit 2 sowie die delegierten Wechselrichterparameter, auch für lesenden Zugriff. Das ist zunächst nur dokumentiert, am Gerät nicht geprüft. Die Bridge soll keine Anmeldung oder Freischaltung nur zur gewöhnlichen Zählerabfrage auslösen. Telegramme bleiben die bevorzugte Zählerquelle. Gerätezuordnungen über den Home Manager sind nicht identisch mit direkt an jedem Wechselrichter konfigurierten Unit-IDs.

Die folgenden Tabellen erfassen das gesamte S03-Profil. RW bleibt nur lesender Kandidat; WO erhält kein MQTT-Zustands-Topic und keinen `/set`-Befehl. Ein Sonderfall ist 43090: Lesen liefert die Zahl freigeschalteter Geräte, Schreiben übermittelt den geheimen Grid-Guard-Code. Nur die Lesesemantik darf als Diagnose kandidieren. Die Zuordnungstabelle besitzt 245 dokumentierte Slots, obwohl das Dokument den Anlagenbetrieb auf 24 SMA-Geräte begrenzt.

### Unit 1: Geräteinformation und Zuordnung

| Register | Registerzahl | Typ / Format | Unit | Zugriff | Kurzbeschreibung | MQTT-Topic |
| --- | --- | --- | --- | --- | --- | --- |
| 30001 | 2 | U32/RAW | — | RO | Version des SMA-Profils | `homie/sma-home-manager/device/modbus-profile-version` |
| 30003 | 2 | U32/RAW | — | RO | SUSy-Geräteklasse des Home Managers | `homie/sma-home-manager/device/susy-id` |
| 30005 | 2 | U32/RAW | — | RO | Seriennummer; private Identität | X: kein reguläres Topic |
| 30007 | 2 | U32/RAW | — | RO | Änderungszähler des Modbus-Profils; kann überlaufen | `homie/sma-home-manager/diagnostics/modbus-change-counter` |
| 30051 | 2 | U32/ENUM | — | RO | Geräteklasse; Kommunikationsprodukt 8128 | `homie/sma-home-manager/device/class` |
| 30053 | 2 | U32/ENUM | — | RO | Gerätetyp; laut Liste 9343 | `homie/sma-home-manager/device/type` |
| 30055 | 2 | U32/RAW | — | RO | Herstellerkennung SMA 461 | `homie/sma-home-manager/device/vendor` |
| 30057 | 2 | U32/RAW | — | RO | Seriennummer, zweite Darstellung | X: kein reguläres Topic |
| 30193 | 2 | U32/DT | s → ISO 8601 | RO | UTC-Gerätezeit | `homie/sma-home-manager/device/system-time` |
| 42109 + 4×(n−1) | 1 | U16/RAW | — | RW | SUSy-ID des Gerätes n; n=1…245 | X: kein reguläres Topic |
| 42110 + 4×(n−1) | 2 | U32/RAW | — | RW | Seriennummer des Gerätes n; private Zuordnung | X: kein reguläres Topic |
| 42112 + 4×(n−1) | 1 | U16/RAW | — | RW | Zugeteilte Unit-ID des Gerätes n; Zuordnung nur privat | X: kein reguläres Topic |
| 43090 | 2 | U32/FIX0 | Anzahl | RW | Lesen: freigeschaltete Geräte; Schreiben: Grid-Guard-Code | `homie/sma-home-manager/diagnostics/grid-guard-enabled-count` |

### Unit 2: Anlagenwerte und reine Steuerbefehle

| Register | Registerzahl | Typ / Format | Unit | Zugriff | Kurzbeschreibung | MQTT-Topic |
| --- | --- | --- | --- | --- | --- | --- |
| 30193 | 2 | U32/DT | s → ISO 8601 | RO | UTC-Anlagenzeit | `homie/sma-home-manager/plant/system-time` |
| 30201 | 2 | U32/ENUM | — | RO | Anlagenzustand; 307 OK, 455 Warnung, 35 Fehler | `homie/sma-home-manager/plant/health` |
| 30581 | 2 | U32/FIX0 | Wh | RO | Gesamtzähler Netzbezug | `homie/sma-home-manager/plant/modbus-energy-import` |
| 30583 | 2 | U32/FIX0 | Wh | RO | Gesamtzähler Netzeinspeisung | `homie/sma-home-manager/plant/modbus-energy-export` |
| 30865 | 2 | S32/FIX0 | W | RO | Gesamtwirkleistung Netzbezug | `homie/sma-home-manager/plant/modbus-power-import` |
| 30867 | 2 | S32/FIX0 | W | RO | Gesamtwirkleistung Netzeinspeisung | `homie/sma-home-manager/plant/modbus-power-export` |
| 40015 | 1 | S16/FIX0 | % | WO | Blindleistungsvorgabe relativ zu Pmax; −100…100 | X: kein Zustands-Topic / kein /set |
| 40016 | 1 | S16/FIX0 | % | WO | Wirkleistungsvorgabe relativ zu Pmax; −100…100 | X: kein Zustands-Topic / kein /set |
| 40024 | 1 | U16/FIX4 | — | WO | cosφ-Vorgabe 0…1 | X: kein Zustands-Topic / kein /set |
| 40025 | 2 | U32/ENUM | — | WO | Erregung: 1041 übererregt / 1042 untererregt | X: kein Zustands-Topic / kein /set |
| 40149 | 2 | S32/FIX0 | W | WO | Wirkleistungsvorgabe an Batterie-Wechselrichter | X: kein Zustands-Topic / kein /set |
| 40151 | 2 | U32/ENUM | — | WO | Kommunikationsregelung Batterie: 802 aktiv / 803 inaktiv | X: kein Zustands-Topic / kein /set |
| 40153 | 2 | S32/FIX0 | W laut S03; prüfen | WO | Blindleistungsvorgabe Batterie; gedruckte Einheit W ist zu klären | X: kein Zustands-Topic / kein /set |

### Unit 3–247: delegierte Wechselrichterparameter

| Register | Registerzahl | Typ / Format | Unit | Zugriff | Kurzbeschreibung | MQTT-Topic je zugeordnetem Wechselrichter |
| --- | --- | --- | --- | --- | --- | --- |
| 30233 | 2 | U32/FIX0 | W | RO | Dauerhafte Wirkleistungsbegrenzung; nur PV | `homie/sma-inverter<N>/nsd/r30233` |
| 30825 | 2 | U32/ENUM | — | RO | Betriebsart Blindleistungsregelung | `homie/sma-inverter<N>/nsd/r30825` |
| 30831 | 2 | S32/FIX2 | — | RO | Sollwert cosφ | `homie/sma-inverter<N>/nsd/r30831` |
| 30833 | 2 | U32/ENUM | — | RO | Sollwert Erregungsart | `homie/sma-inverter<N>/nsd/r30833` |
| 40200 | 2 | U32/ENUM | — | RW | Betriebsart Blindleistungsregelung | `homie/sma-inverter<N>/nsd/r40200` |
| 40206 | 2 | S32/FIX2 | — | RW | Sollwert cosφ | `homie/sma-inverter<N>/nsd/r40206` |
| 40208 | 2 | U32/ENUM | — | RW | Sollwert Erregungsart | `homie/sma-inverter<N>/nsd/r40208` |
| 40216 | 2 | U32/ENUM | — | RW | Wirkleistungsbegrenzung bei Überfrequenz | `homie/sma-inverter<N>/nsd/r40216` |
| 40218 | 2 | U32/FIX2 | Hz | RW | Startfrequenzabstand P(f) | `homie/sma-inverter<N>/nsd/r40218` |
| 40220 | 2 | U32/FIX2 | Hz | RW | Rücksetzfrequenzabstand P(f) | `homie/sma-inverter<N>/nsd/r40220` |
| 40222 | 2 | U32/FIX2 | — | RW | cosφ-Kennlinie: Startpunkt | `homie/sma-inverter<N>/nsd/r40222` |
| 40224 | 2 | U32/ENUM | — | RW | cosφ-Kennlinie: Erregung Startpunkt | `homie/sma-inverter<N>/nsd/r40224` |
| 40226 | 2 | U32/FIX2 | — | RW | cosφ-Kennlinie: Endpunkt | `homie/sma-inverter<N>/nsd/r40226` |
| 40228 | 2 | U32/ENUM | — | RW | cosφ-Kennlinie: Erregung Endpunkt | `homie/sma-inverter<N>/nsd/r40228` |
| 40230 | 2 | U32/FIX0 | % | RW | cosφ-Kennlinie: Wirkleistung Startpunkt | `homie/sma-inverter<N>/nsd/r40230` |
| 40232 | 2 | U32/FIX0 | % | RW | cosφ-Kennlinie: Wirkleistung Endpunkt | `homie/sma-inverter<N>/nsd/r40232` |

`<N>` ist hier die noch privat aufzulösende Gerätezuordnung (1/2/3), keine gültige wörtliche Homie-ID. Diese Werte über den Home Manager nicht zusätzlich als unabhängige Wechselrichter addieren. NSD-Steuerbefehle sind laut S03 zeitlich begrenzt (60 Minuten) und höchstens ein Schreibkommando/s zulässig. Das ist kein Polling- oder Keepalive-Auftrag für diese Bridge.

## eCharger: Bedienparameter und Messwerte

Lokale HTTPS-Sitzung: `POST /api/v1/token`, `POST /api/v1/parameters/search`, `POST /api/v1/measurements/live`, Parameterwrite `PUT /api/v1/parameters/IGULD:SELF`. Lokales Zertifikat ausdrücklich vertrauen; TLS-Prüfung beibehalten. Portal- und lokale Tokens sind getrennt.

Die folgende **11er-Befehlsliste** entspricht P04/P02 und den berichteten Schreibrechten. Nur die Statusbeleuchtung hat einen ausdrücklich berichteten einzelnen Live-Schreib-/Rücklesetest. Alle weiteren Befehle benötigen Implementierungs- und Rücklesevalidierung. Bei `RW*` sind Metadatenrechte bekannt, aber Energie-/Zeitkonvertierung noch offen. Die tatsächlichen Optionen und Grenzen vor jedem Befehl erneut lesen, keine Start-/Reconnect-Schreibzugriffe.

| Lokaler Kanal | Unit | Zugriff vorgesehen | Kurzbeschreibung | Nachweis | MQTT-Topic |
| --- | --- | --- | --- | --- | --- |
| `Parameter.Chrg.ActChaMod` | — | RW | Lademodus: 4718 schnell, 4719 optimiert/PV, 4720 Zielvorgabe, 4721 Stopp. | B/R P02–P04 | `homie/sma-echarger/settings/charge-mode` |
| `Parameter.Chrg.ChrgApv` | — | RW | Laden freigeben (5172) oder gesperrt halten (5171). | B/R P02–P04 | `homie/sma-echarger/settings/charging-release` |
| `Parameter.Chrg.ChrgLok` | — | RW | Für jeden Ladevorgang eine Freigabe verlangen; 1129 ja, 1130 nein. | B/R P02–P04 | `homie/sma-echarger/settings/approval-required` |
| `Parameter.Chrg.StpWhenFl` | — | RW | Ladevorgang beenden, wenn das Fahrzeug als voll erkannt wird. | B/R P02–P04 | `homie/sma-echarger/settings/stop-when-full` |
| `Parameter.Chrg.StpWhenFlTm` | min | RW | Wartezeit bis zur Beendigung; Metadaten 5…1440 min, ganzzahlig. | B/R P02–P04 | `homie/sma-echarger/settings/stop-delay` |
| `Parameter.Chrg.CblLok` | — | RW | Ladekabel dauerhaft verriegeln; 308 ein, 303 aus. | B/R P02–P04 | `homie/sma-echarger/settings/cable-lock` |
| `Parameter.Sys.DevSigBri` | — | RW | Statuslicht: 5191 niedrig, 5190 mittel, 5173 hoch. | B/R P02–P04 | `homie/sma-echarger/settings/led-brightness` |
| `Parameter.Sys.AmbLghtBri` | — | RW | Ambientelicht-Helligkeit; gleiche drei Stufen. | B/R P02–P04 | `homie/sma-echarger/settings/ambient-brightness` |
| `Parameter.Sys.UseAmbLght` | — | RW | Ambientelicht aktivieren; 308 ein, 303 aus. | B/R P02–P04 | `homie/sma-echarger/settings/ambient-enabled` |
| `Parameter.Chrg.Plan.En` | kWh; lokal 2.6.37.R verifiziert | RW* | Für den Ladeplan gewünschte zu ladende Energie; kein Fahrzeug-SoC. | B/R P02–P04 | `homie/sma-echarger/settings/plan-energy` |
| `Parameter.Chrg.Plan.StopTm` | s → ISO 8601 | RW* | End-/Abfahrtszeit des Ladeplans; Zeitbasis und Zeitzone prüfen. | B/R P02–P04 | `homie/sma-echarger/settings/plan-end` |

Ein Zielplan benötigt Energie und Endzeit gemeinsam sowie einen expliziten Übernahmebefehl; zwei nacheinander eintreffende Zustandswerte dürfen keine halbfertige Planung auslösen. Konkretes MQTT-Befehlsformat wird im Adapterentwurf festgelegt. Der Referenz-Slider beginnt teilweise bei 0, obwohl der Geräteexport für StopDelay mindestens 5 vorgibt: Geräte-Metadaten haben Vorrang. „Stopp“ ist eine lokale Moduswahl, kein sicherheitstechnischer Not-Aus.

| Kanal | MQTT-Unit / Umrechnung | Kurzbeschreibung | Nachweis | MQTT-Topic |
| --- | --- | --- | --- | --- |
| `Measurement.Metering.GridMs.TotWIn.ChaSta` | W | Ladeleistung | B/P03 | `homie/sma-echarger/measurements/power` |
| `Measurement.ChaSess.WhIn` | Wh → kWh | Energie des aktuellen Ladevorgangs | B/P03 | `homie/sma-echarger/measurements/session-energy` |
| `Measurement.Operation.EVeh.ChaStt` | — | Fahrzeug-Ladezustands-Code, z. B. verbunden/lädt; kein SoC-Prozent | B/P03 | `homie/sma-echarger/measurements/vehicle-status-code` |
| `Measurement.Operation.Health` | — | Allgemeiner Wallboxzustand als Rohcode; Text getrennt | B/P03 | `homie/sma-echarger/measurements/health-code` |
| `Measurement.Metering.GridMs.TotWhIn.ChaSta oder Measurement.Metering.GridMs.TotWhIn` | Wh → kWh | Gesamtenergiezähler; Quelle/Fallback anhand Antwort wählen | R/P04; Liveantwort offen | `homie/sma-echarger/measurements/total-energy` |
| `Measurement.GridMs.A.phsA` | A | Ladestrom L1 | R/P04; Liveantwort offen | `homie/sma-echarger/measurements/current-l1` |
| `Measurement.GridMs.PhV.phsA` | V | Spannung L1 | R/P04; Liveantwort offen | `homie/sma-echarger/measurements/voltage-l1` |
| `Measurement.GridMs.A.phsB` | A | Ladestrom L2 | R/P04; Liveantwort offen | `homie/sma-echarger/measurements/current-l2` |
| `Measurement.GridMs.PhV.phsB` | V | Spannung L2 | R/P04; Liveantwort offen | `homie/sma-echarger/measurements/voltage-l2` |
| `Measurement.GridMs.A.phsC` | A | Ladestrom L3 | R/P04; Liveantwort offen | `homie/sma-echarger/measurements/current-l3` |
| `Measurement.GridMs.PhV.phsC` | V | Spannung L3 | R/P04; Liveantwort offen | `homie/sma-echarger/measurements/voltage-l3` |
| `Measurement.GridMs.Hz` | Hz | Netzfrequenz | R/P04; Liveantwort offen | `homie/sma-echarger/measurements/frequency` |

## eCharger: vollständiger Parameterbestand

Alle **85 Metadateneinträge aus P02** sind hier erfasst. Der verkürzte JSON-Katalog enthält keine Einheiten: Angaben mit `?` sind plausible Deutungen aus Kanalname und Gerätefunktion, **keine bestätigten API-Einheiten**. Grenzen sind die im Export enthaltenen Rohgrenzen, nicht automatisch MQTT-Grenzen. Nicht beschriftete Enum-Codes werden nicht frei übersetzt. `RO geplant` bei `editable=true` bedeutet: Wert kann als Diagnose inventarisiert werden, ein `/set`-Befehl ist nicht freigegeben. Administrative Aktionen haben überhaupt kein Zustands-Topic.

Passwort-/WLAN-/FTP-/Identitäts-/Netzwerkwertfelder werden ausschließlich als vorhandene Möglichkeiten benannt. Ihre Inhalte dürfen nicht über MQTT, Log oder Fixtures veröffentlicht werden. Arrays `[]` sind kanalgebundene Mehrfachwerte; ihre Anzahl/Zuordnung ist noch zu prüfen. Namen, IDs und Komponenteninformationen bei Bedarf privat zur Quellenauswahl verwenden.

| Parameter-Kanal | Unit | API editable | Rohgrenzen / Optionen | Kurzbeschreibung | MQTT-Zugriff | MQTT-Topic |
| --- | --- | --- | --- | --- | --- | --- |
| `Parameter.Acs.PwdIstl` | — | ja | nicht angegeben | Installateurpasswort; geheim. | X | X: kein reguläres Topic |
| `Parameter.Acs.PwdUsr` | — | ja | nicht angegeben | Benutzerpasswort; geheim. | X | X: kein reguläres Topic |
| `Parameter.Chrg.AMinCha` | A? | ja | min 6; max 32 | Minimaler Ladestrom; Lade-/Fahrzeuggrenze. | RO geplant | `homie/sma-echarger/parameters/chrg-amincha` |
| `Parameter.Chrg.ActChaMod` | — | ja | Codes 4718, 4719, 4720, 4721 | Aktuell eingestellter Lademodus. | RW | `homie/sma-echarger/settings/charge-mode` |
| `Parameter.Chrg.CblLok` | — | ja | Codes 303, 308 | Dauerhafte Kabelverriegelung aktiviert. | RW | `homie/sma-echarger/settings/cable-lock` |
| `Parameter.Chrg.ChrgApv` | — | ja | Codes 5171, 5172 | Ladefreigabe/Sperrzustand. | RW | `homie/sma-echarger/settings/charging-release` |
| `Parameter.Chrg.ChrgLok` | — | ja | Codes 1130, 1129 | Freigabe für Ladevorgänge erforderlich. | RW | `homie/sma-echarger/settings/approval-required` |
| `Parameter.Chrg.Plan.DurTmm` | min? | ja | min 0 | Ladeplandauer; Zusammenhang mit Endzeit noch prüfen. | RO geplant | `homie/sma-echarger/parameters/chrg-plan-durtmm` |
| `Parameter.Chrg.Plan.En` | kWh; lokal 2.6.37.R verifiziert | ja | min 0 | Zielenergie für Ladeplan. | RW* | `homie/sma-echarger/settings/plan-energy` |
| `Parameter.Chrg.Plan.StopTm` | s → ISO 8601 | ja | min 0 | Endzeit des Ladeplans. | RW* | `homie/sma-echarger/settings/plan-end` |
| `Parameter.Chrg.StpWhenFl` | — | ja | Codes 1129, 1130 | Beenden bei vollem Fahrzeug. | RW | `homie/sma-echarger/settings/stop-when-full` |
| `Parameter.Chrg.StpWhenFlTm` | min | ja | min 5; max 1440 | Wartezeit bis Beendigung. | RW | `homie/sma-echarger/settings/stop-delay` |
| `Parameter.Chrg.UseEnergyMeter` | — | ja | Codes 1129, 1130 | Energiezähler im Ladebetrieb verwenden; Lastmanagementfunktion. | RO geplant | `homie/sma-echarger/parameters/chrg-useenergymeter` |
| `Parameter.DevUpd.IsOn` | — | ja | Codes 1129, 1130 | Geräte-Updatefunktion aktiviert; Abgrenzung AutoUpd offen. | RO geplant | `homie/sma-echarger/parameters/devupd-ison` |
| `Parameter.DtTm.NtpSrv` | — | ja | nicht angegeben | NTP-Server; private Netzwerkadresse. | X | X: kein reguläres Topic |
| `Parameter.FTPPush.IsOn` | — | ja | Codes 1129, 1130 | FTP-Datenexport aktiviert. | X | X: kein reguläres Topic |
| `Parameter.FTPPush.Login` | — | ja | nicht angegeben | FTP-Benutzername; Zugangsdaten. | X | X: kein reguläres Topic |
| `Parameter.FTPPush.Port` | Port | ja | min 0; max 65535 | FTP-Serverport; privates Exportziel. | X | X: kein reguläres Topic |
| `Parameter.FTPPush.Pwd` | — | ja | nicht angegeben | FTP-Passwort; geheim. | X | X: kein reguläres Topic |
| `Parameter.FTPPush.RemStoLcn` | — | ja | nicht angegeben | FTP-Zielverzeichnis; privates Exportziel. | X | X: kein reguläres Topic |
| `Parameter.FTPPush.Srv` | — | ja | nicht angegeben | FTP-Server; privates Exportziel. | X | X: kein reguläres Topic |
| `Parameter.FTPPush.UpldCyc` | — | ja | Codes 1188, 1189 | Zyklus des FTP-Datenexports; Codes prüfen. | X | X: kein reguläres Topic |
| `Parameter.GridGuard.Cntry.PEOpnMon` | — | ja | Codes 1129, 1130 | Schutzleiter-Unterbrechungsüberwachung; keine allgemeine Ladeoption. | RO geplant | `homie/sma-echarger/parameters/gridguard-cntry-peopnmon` |
| `Parameter.GridGuard.Cntry.VRtg` | V? | ja | min 210; max 260 | Netz-Nennspannung; Installations-/Netzparameter. | RO geplant | `homie/sma-echarger/parameters/gridguard-cntry-vrtg` |
| `Parameter.IecCfg.GoCfg.GoAppId` | — | ja | min 0; max 16384 | IEC-GOOSE-Anwendungskennung; administrativer Parameter. | RO geplant | `homie/sma-echarger/parameters/ieccfg-gocfg-goappid` |
| `Parameter.IecCfg.GoCfg.GoMacId` | — | ja | nicht angegeben | GOOSE-MAC-Ziel; private Netzwerkdaten. | X | X: kein reguläres Topic |
| `Parameter.IecCfg.SrvIsOn` | — | ja | Codes 1129, 1130 | IEC-Kommunikationsserver aktiv; Protokollfunktion konkret prüfen. | RO geplant | `homie/sma-echarger/parameters/ieccfg-srvison` |
| `Parameter.Inverter.AcALim` | A? | ja | min 6; max 32 | Maximaler AC-Ladestrom; Installationsgrenze. | RO geplant | `homie/sma-echarger/parameters/inverter-acalim` |
| `Parameter.Inverter.OutPhs` | — | ja | Codes 325, 327, 329, 326, 5194, 5195 | Phasenkonfiguration; sechs Codes, automatische Zuordnung prüfen. | RO geplant | `homie/sma-echarger/parameters/inverter-outphs` |
| `Parameter.Inverter.WMax` | W? | ja | min 4500; max 22000 | Eingestellte maximale Wirkleistung. | RO geplant | `homie/sma-echarger/parameters/inverter-wmax` |
| `Parameter.Inverter.WMaxIn` | W? | ja | min 4500; max 22000 | Maximale aufgenommene Leistung; Bedeutung gegenüber WMax prüfen. | RO geplant | `homie/sma-echarger/parameters/inverter-wmaxin` |
| `Parameter.Inverter.WMaxInRtg` | W? | nein | nicht angegeben | Nennleistung für Leistungsaufnahme. | RO geplant | `homie/sma-echarger/parameters/inverter-wmaxinrtg` |
| `Parameter.Mb.ScdInEna` | — | ja | Codes 308, 303 | Modbus-Steuereingang; genaue Betriebssemantik offen. | RO geplant | `homie/sma-echarger/parameters/mb-scdinena` |
| `Parameter.Mb.TcpSrv.IsOn` | — | ja | Codes 1130, 1129 | Modbus-TCP-Server eingeschaltet; Profil separat benötigt. | RO geplant | `homie/sma-echarger/parameters/mb-tcpsrv-ison` |
| `Parameter.Mb.TcpSrv.Port` | Port | ja | min 0; max 65535 | Modbus-TCP-Port; Profil separat benötigt. | RO geplant | `homie/sma-echarger/parameters/mb-tcpsrv-port` |
| `Parameter.Mb.UdpSrv.IsOn` | — | ja | Codes 1130, 1129 | Modbus-UDP-Server eingeschaltet. | RO geplant | `homie/sma-echarger/parameters/mb-udpsrv-ison` |
| `Parameter.Mb.UdpSrv.Port` | Port | ja | min 0; max 65535 | Modbus-UDP-Port; dokumentiertes Feld beweist keinen nutzbaren Readserver. | RO geplant | `homie/sma-echarger/parameters/mb-udpsrv-port` |
| `Parameter.Nameplate.ARtg` | A? | nein | min 32; max 32 | Nennstrom des Geräts laut Typenschildmetadaten. | RO geplant | `homie/sma-echarger/parameters/nameplate-artg` |
| `Parameter.Nameplate.ChrgCtrl.SerNumTxt` | — | nein | nicht angegeben | Seriennummer des Ladereglers; private Identität. | X | X: kein reguläres Topic |
| `Parameter.Nameplate.ChrgCtrl.SusyId` | — | nein | nicht angegeben | SUSy-Kennung Laderegler. | RO geplant | `homie/sma-echarger/parameters/nameplate-chrgctrl-susyid` |
| `Parameter.Nameplate.ChrgCtrl.SwRevTxt` | — | nein | nicht angegeben | Softwarestand Laderegler. | RO geplant | `homie/sma-echarger/parameters/nameplate-chrgctrl-swrevtxt` |
| `Parameter.Nameplate.CmpCom.HwVer` | — | nein | nicht angegeben | Hardwarestand Kommunikationskomponente. | RO geplant | `homie/sma-echarger/parameters/nameplate-cmpcom-hwver` |
| `Parameter.Nameplate.CmpCom.Rev` | — | nein | nicht angegeben | Revision der Kommunikationskomponente. | RO geplant | `homie/sma-echarger/parameters/nameplate-cmpcom-rev` |
| `Parameter.Nameplate.CmpCom.SerNum` | — | nein | nicht angegeben | Seriennummer Kommunikationskomponente; private Identität. | X | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpMain.SusyId` | — | nein | nicht angegeben | SUSy-Kennung der Hauptkomponente. | RO geplant | `homie/sma-echarger/parameters/nameplate-cmpmain-susyid` |
| `Parameter.Nameplate.CmpOS.SwRev` | — | nein | nicht angegeben | Softwarestand Betriebssystem. | RO geplant | `homie/sma-echarger/parameters/nameplate-cmpos-swrev` |
| `Parameter.Nameplate.Location` | — | ja | nicht angegeben | Gerätename/Standort; privater Anzeigename. | X | X: kein reguläres Topic |
| `Parameter.Nameplate.MacId` | — | nein | nicht angegeben | LAN-MAC-Adresse; private Identität. | X | X: kein reguläres Topic |
| `Parameter.Nameplate.MainModel` | — | nein | Codes 8008 | Geräteklasse, z. B. Ladegerät. | RO geplant | `homie/sma-echarger/parameters/nameplate-mainmodel` |
| `Parameter.Nameplate.Model` | — | nein | Codes 19143 | Numerischer Produkttyp, hier eCharger-Modellklasse. | RO geplant | `homie/sma-echarger/parameters/nameplate-model` |
| `Parameter.Nameplate.ModelStr` | — | nein | nicht angegeben | Gerätemodell als Text. | RO geplant | `homie/sma-echarger/parameters/nameplate-modelstr` |
| `Parameter.Nameplate.PkgRev` | — | nein | nicht angegeben | Firmwarepaket-Version. | RO geplant | `homie/sma-echarger/parameters/nameplate-pkgrev` |
| `Parameter.Nameplate.SerNum` | — | nein | nicht angegeben | Seriennummer; private Geräteidentität. | X | X: kein reguläres Topic |
| `Parameter.Nameplate.Vendor` | — | nein | Codes 461 | Herstellerkennung SMA. | RO geplant | `homie/sma-echarger/parameters/nameplate-vendor` |
| `Parameter.Nameplate.VendorStr` | — | nein | nicht angegeben | Herstellername als Text. | RO geplant | `homie/sma-echarger/parameters/nameplate-vendorstr` |
| `Parameter.Nameplate.WlMacId` | — | nein | nicht angegeben | WLAN-MAC-Adresse; private Identität. | X | X: kein reguläres Topic |
| `Parameter.Operation.ComTmOut` | ms? | ja | min 200; max 60000 | Timeout der Steuerkommunikation; Rückfallverhalten prüfen. | RO geplant | `homie/sma-echarger/parameters/operation-comtmout` |
| `Parameter.PCC.ARtg` | A? | ja | min 16; max 1000 | Nennstrom des Netzanschlusses; beeinflusst Lastmanagement. | RO geplant | `homie/sma-echarger/parameters/pcc-artg` |
| `Parameter.PCC.FlbInv.WMax` | W? | ja | min 0; max 22000 | Fallback-Leistungsgrenze bei gestörter Anlagenkommunikation. | RO geplant | `homie/sma-echarger/parameters/pcc-flbinv-wmax` |
| `Parameter.PCC.WMaxAsym` | W? | ja | min 0; max 10000 | Grenze zulässiger asymmetrischer Belastung/Schieflast. | RO geplant | `homie/sma-echarger/parameters/pcc-wmaxasym` |
| `Parameter.Spdwr.ActlDnsSrvIp[]` | — | nein | nicht angegeben | Aktuelle DNS-Server; private Netzwerkdaten. | X | X: kein reguläres Topic |
| `Parameter.Spdwr.ActlGwIp[]` | — | nein | nicht angegeben | Aktuelle Gateways; private Netzwerkdaten. | X | X: kein reguläres Topic |
| `Parameter.Spdwr.ActlIp[]` | — | nein | nicht angegeben | Aktuelle IP-Adressen; private Netzwerkdaten. | X | X: kein reguläres Topic |
| `Parameter.Spdwr.ActlSnetMsk[]` | — | nein | nicht angegeben | Aktuelle Subnetzmasken; private Netzwerkkonfiguration. | X | X: kein reguläres Topic |
| `Parameter.Spdwr.AutoCfgIsOn[]` | — | ja | Codes 1129 | Automatische Speedwire-Netzwerkkonfiguration. | RO geplant | `homie/sma-echarger/parameters/spdwr-autocfgison` |
| `Parameter.Spdwr.IgmpQryTms` | s? | ja | min 11; max 31744 | IGMP-Abfrageintervall; Zeitunit offen. | RO geplant | `homie/sma-echarger/parameters/spdwr-igmpqrytms` |
| `Parameter.Spdwr.IgmpQryTx` | — | ja | Codes 303, 4478, 4479 | IGMP-Querier-Sendemodus; Codes prüfen. | RO geplant | `homie/sma-echarger/parameters/spdwr-igmpqrytx` |
| `Parameter.SwCmp.CmpComBlt.SwRev` | — | nein | nicht angegeben | Softwarestand der Kommunikationskomponente. | RO geplant | `homie/sma-echarger/parameters/swcmp-cmpcomblt-swrev` |
| `Parameter.SwCmp.CmpEnnexOS.Frwk.SwRev` | — | nein | nicht angegeben | Softwarestand ennexOS-Framework. | RO geplant | `homie/sma-echarger/parameters/swcmp-cmpennexos-frwk-swrev` |
| `Parameter.Sys.AmbLghtBri` | — | ja | Codes 5191, 5190, 5173 | Helligkeitsstufe Ambientelicht. | RW | `homie/sma-echarger/settings/ambient-brightness` |
| `Parameter.Sys.DevRstr` | — | ja | Codes 302, 1146 | Neustart/Aktion auslösen; genaue Metadaten prüfen. | X | X: kein reguläres Topic |
| `Parameter.Sys.DevSig` | — | ja | Codes 303, 878 | Gerätesignalisierung/Identifikationslicht; Funktionsprüfung offen. | RO geplant | `homie/sma-echarger/parameters/sys-devsig` |
| `Parameter.Sys.DevSigBri` | — | ja | Codes 5191, 5190, 5173 | Helligkeit Statuslicht. | RW | `homie/sma-echarger/settings/led-brightness` |
| `Parameter.Sys.UseAmbLght` | — | ja | Codes 308, 303 | Ambientelicht aktiviert. | RW | `homie/sma-echarger/settings/ambient-enabled` |
| `Parameter.Upd.AutoUpdIsOn` | — | ja | Codes 1129, 1130 | Automatische Firmwareupdates eingeschaltet. | RO geplant | `homie/sma-echarger/parameters/upd-autoupdison` |
| `Parameter.Upd.AvalChkIstl` | — | ja | Codes 302, 1146 | Verfügbarkeitsprüfung für Updates auslösen; administrative Aktion. | X | X: kein reguläres Topic |
| `Parameter.WebConn.IsOn` | — | ja | Codes 1129, 1130 | Webconnect-Kommunikation eingeschaltet. | RO geplant | `homie/sma-echarger/parameters/webconn-ison` |
| `Parameter.WebConn.SwRev` | — | nein | nicht angegeben | Version der Webconnect-Komponente. | RO geplant | `homie/sma-echarger/parameters/webconn-swrev` |
| `Parameter.Wl.DoAcq` | — | ja | Codes 3342, 302 | WLAN-Suche/Erfassung auslösen; administrative Aktion. | X | X: kein reguläres Topic |
| `Parameter.Wl.DoWPS` | — | ja | Codes 3321, 302 | WPS-Verbindungsaufbau auslösen; administrativer Vorgang. | X | X: kein reguläres Topic |
| `Parameter.Wl.IsOn` | — | ja | Codes 1129, 1130 | WLAN eingeschaltet. | RO geplant | `homie/sma-echarger/parameters/wl-ison` |
| `Parameter.Wl.Sec.Cry` | — | ja | Codes 3323, 3324, 3398 | WLAN-Verschlüsselungsverfahren; Codes nicht übersetzt. | RO geplant | `homie/sma-echarger/parameters/wl-sec-cry` |
| `Parameter.Wl.Sec.Psk` | — | ja | nicht angegeben | WLAN-Schlüssel; geheim. | X | X: kein reguläres Topic |
| `Parameter.Wl.Sec.Ssid` | — | ja | nicht angegeben | WLAN-Netzwerkname; private Netzwerkdaten. | X | X: kein reguläres Topic |
| `Parameter.Wl.SoftAcsIsOn` | — | ja | Codes 1129, 1130 | WLAN-Access-Point eingeschaltet. | RO geplant | `homie/sma-echarger/parameters/wl-softacsison` |

## eCharger: SEMP

SEMP wird **lesend** über `/SEMP/` und `/SEMP/Parameters` ausgewertet. 25 Kanäle aus P03 sind vollständig aufgeführt; identische Parameter verwenden dasselbe Zustands-Topic wie die lokale API. SEMP-Metadaten beweisen keine Schreibmöglichkeit über diesen Endpunkt. Ein vom Home Manager empfangener Leistungssollwert ist kein Mindest-PV-Anteil. Die Bridge sendet keine konkurrierenden SEMP-Empfehlungen.

| SEMP-Kanal | Unit | Zugriff | Kurzbeschreibung | MQTT-Topic |
| --- | --- | --- | --- | --- |
| `Parameter.Chrg.ActChaMod` | — | RO über SEMP | Aktuell eingestellter Lademodus. | `homie/sma-echarger/settings/charge-mode` |
| `Parameter.Chrg.Plan.StopTm` | s → ISO 8601 | RO über SEMP | Endzeit des Ladeplans. | `homie/sma-echarger/settings/plan-end` |
| `Parameter.Chrg.Plan.En` | kWh; lokal 2.6.37.R verifiziert | RO über SEMP | Zielenergie für Ladeplan. | `homie/sma-echarger/settings/plan-energy` |
| `Parameter.Chrg.StpWhenFl` | — | RO über SEMP | Beenden bei vollem Fahrzeug. | `homie/sma-echarger/settings/stop-when-full` |
| `Parameter.Chrg.StpWhenFlTm` | min | RO über SEMP | Wartezeit bis Beendigung. | `homie/sma-echarger/settings/stop-delay` |
| `Parameter.Inverter.OutPhs` | — | RO über SEMP | Phasenkonfiguration; sechs Codes, automatische Zuordnung prüfen. | `homie/sma-echarger/parameters/inverter-outphs` |
| `Setpoint.PlantControl.PCC.ChrgActCnt` | Anzahl? | RO über SEMP | Aktive Ladepunkte gemäß Anlagensteuerung; Semantik prüfen. | `homie/sma-echarger/control/active-charging-count` |
| `Measurement.Operation.EVeh.Health` | — | RO über SEMP | Zustand der Fahrzeug-Ladeverbindung. | `homie/sma-echarger/measurements/vehicle-health` |
| `Measurement.Operation.EVeh.ChaStt` | — | RO über SEMP | Fahrzeug-Ladezustands-Code. | `homie/sma-echarger/measurements/vehicle-status-code` |
| `Measurement.Operation.Health` | — | RO über SEMP | Gerätezustands-Code; Text getrennt. | `homie/sma-echarger/measurements/health-code` |
| `Measurement.Operation.Evt.Msg` | — | RO über SEMP | Aktuelle Ereignismeldung; Textauflösung prüfen. | `homie/sma-echarger/measurements/event-code` |
| `Measurement.ChaSess.WhIn` | Wh → kWh | RO über SEMP | Energie des Ladevorgangs. | `homie/sma-echarger/measurements/session-energy` |
| `Parameter.Nameplate.PkgRev` | — | RO über SEMP | Firmwarepaket-Version. | `homie/sma-echarger/parameters/nameplate-pkgrev` |
| `Measurement.Metering.GridMs.TotWIn.ChaSta` | W | RO über SEMP | Ladeleistung. | `homie/sma-echarger/measurements/power` |
| `Measurement.Chrg.ModSw` | — | RO über SEMP | Modusumschalt-/Schaltzustand; Bedeutung des Codes offen. | `homie/sma-echarger/measurements/mode-switch-code` |
| `Parameter.Chrg.ChrgLok` | — | RO über SEMP | Freigabe für Ladevorgänge erforderlich. | `homie/sma-echarger/settings/approval-required` |
| `Parameter.Chrg.ChrgApv` | — | RO über SEMP | Ladefreigabe/Sperrzustand. | `homie/sma-echarger/settings/charging-release` |
| `Parameter.Chrg.CblLok` | — | RO über SEMP | Dauerhafte Kabelverriegelung aktiviert. | `homie/sma-echarger/settings/cable-lock` |
| `Measurement.Acs.AuthRegistStt` | — | RO über SEMP | Autorisierungs-/Registrierungsstatus; Enum offen. | `homie/sma-echarger/measurements/auth-registration-code` |
| `Parameter.Sys.DevSigBri` | — | RO über SEMP | Helligkeit Statuslicht. | `homie/sma-echarger/settings/led-brightness` |
| `Parameter.Sys.AmbLghtBri` | — | RO über SEMP | Helligkeitsstufe Ambientelicht. | `homie/sma-echarger/settings/ambient-brightness` |
| `Parameter.Sys.UseAmbLght` | — | RO über SEMP | Ambientelicht aktiviert. | `homie/sma-echarger/settings/ambient-enabled` |
| `Setpoint.PlantControl.Inverter.WModCfg.WCtlComCfg.WSptMaxNom` | %? | RO über SEMP | Obere normierte Leistungsvorgabe, kein gemessener PV-Anteil. | `homie/sma-echarger/control/power-setpoint-max-percent` |
| `Setpoint.PlantControl.Inverter.WModCfg.WCtlComCfg.WSptMinNom` | %? | RO über SEMP | Untere normierte Leistungsvorgabe, kein Mindest-PV-Anteil. | `homie/sma-echarger/control/power-setpoint-min-percent` |
| `Parameter.Nameplate.Location` | — | RO über SEMP | Gerätename/Standort; privater Anzeigename. | X: kein reguläres Topic |

| SEMP-Strukturelement | Unit | Kurzbeschreibung | MQTT-Topic |
| --- | --- | --- | --- |
| `/DeviceInfo/Identification/DeviceType` | — | Gerätetyp als Text. | `homie/sma-echarger/device/semp-type` |
| `/DeviceInfo/Identification/DeviceVendor` | — | Hersteller als Text. | `homie/sma-echarger/device/semp-vendor` |
| `/DeviceInfo/Identification/DeviceId, DeviceSerial, DeviceName` | — | Private Identität/Anzeigenamen; nur zur Quellenauswahl. | X: kein reguläres Topic |
| `/DeviceInfo/Characteristics/MaxPowerConsumption` | W | Vom Gerät gemeldete aktuelle Obergrenze; nicht Datenblatt-Nennleistung. | `homie/sma-echarger/semp/max-power` |
| `/DeviceInfo/Characteristics/MinPowerConsumption` | W | Vom Gerät gemeldete Mindestleistung. | `homie/sma-echarger/semp/min-power` |
| `/DeviceInfo/Characteristics/MinOnTime` | s | SEMP-Mindest-Einschaltdauer. | `homie/sma-echarger/semp/min-on-time` |
| `/DeviceInfo/Characteristics/MinOffTime` | s | SEMP-Mindest-Ausschaltdauer. | `homie/sma-echarger/semp/min-off-time` |
| `/DeviceInfo/Capabilities/CurrentPower/Method` | — | Ermittlungsmethode der Leistung. | `homie/sma-echarger/semp/power-method` |
| `/DeviceInfo/Capabilities/Timestamps/AbsoluteTimestamps` | — | Absolute statt relative SEMP-Zeitstempel. | `homie/sma-echarger/semp/absolute-timestamps` |
| `/DeviceInfo/Capabilities/Interruptions/InterruptionsAllowed` | — | Ob Ladeunterbrechungen unterstützt werden. | `homie/sma-echarger/semp/interruptions-allowed` |
| `/DeviceInfo/Capabilities/Requests/OptionalEnergy` | — | Unterstützung optionalen Energiebedarfs. | `homie/sma-echarger/semp/optional-energy` |
| `/DeviceStatus/EMSignalsAccepted` | — | Ob Energiemanagementsignale akzeptiert werden. | `homie/sma-echarger/semp/em-signals-accepted` |
| `/DeviceStatus/Status` | — | SEMP-Betriebsstatus, unabhängig vom Fahrzeugcode. | `homie/sma-echarger/semp/status` |
| `/DeviceStatus/PowerConsumption/PowerInfo/AveragePower` | W | Gemittelte Leistungsaufnahme. | `homie/sma-echarger/semp/average-power` |
| `/DeviceStatus/PowerConsumption/PowerInfo/Timestamp` | s relativ/absolut | SEMP-Zeitbezug; bei relativer Quelle kein Unix-Zeitstempel. | `homie/sma-echarger/semp/power-timestamp` |
| `/DeviceStatus/PowerConsumption/PowerInfo/AveragingInterval` | s | Mittelungsdauer der Leistungsangabe. | `homie/sma-echarger/semp/averaging-interval` |

Zusätzliche `PlanningRequest`-/Energieanforderungs-Felder sind mögliche dynamische SEMP-Ausgaben, aber in der gelieferten `/SEMP/`-Antwort nicht vorhanden. Frühesten/spätesten Start, benötigte Energie, Laufzeit und Abschlussstatus erst anhand einer tatsächlichen Ladeplan-Antwort einzeln aufnehmen. Keine Fahrzeug-SoC-, Reichweiten-, VIN- oder Batteriekapazitätsmessung ist über diese Unterlagen für den eCharger belegt. RFID-Verwaltung ist in S08 als UI-Funktion beschrieben, ohne bestätigten API-Endpunkt; Kartenkennungen werden nicht zu MQTT-Telemetrie.

## ennexOS: bestätigte Felder und weitere Kandidaten

### Bestätigte eCharger-Felder aus der funktionierenden Referenz

Quelle P05; zusätzlich ist der Mindest-PV-Anteil in U01 sichtbar. Anmeldung über das normale SMA-Konto, OAuth Authorization Code mit PKCE und Refresh; **keine kostenpflichtige Developer-API**. Lesepfad: `GET https://uiapi.sunnyportal.com/api/v1/plants/{plantId}/devices/{deviceId}?menuItemType=ViewDeviceProperties`. Der bekannte Schreibpfad lautet `PUT /plants/{plantId}/devices/{deviceId}/optionalenergydemand`. Platzhalter bleiben privat konfiguriert.

Anfangs ausschließlich Mindest-PV-Anteil schreiben. Die vier Payload-Felder `minPvPercentage`, `pvSurplusOnly`, `usePriceLimit`, `priceLimit` wie P05 behandeln; die drei nicht geänderten Einstellungen erhalten. `feedInLimitation` nicht mitschreiben. Nur ganze Prozentwerte 0…100. Bei aktivem Preislimit oder `pvSurplusOnly=true` verweigert die Referenz den PV-Befehl; Verhalten erhalten. Schreibrecht aus dem Vorhandensein von `_links.ui_Edit_OptionalEnergyDemand` bestimmen, auch bei leerem Array. Geräte-/Verbraucheridentität vor jedem Befehl prüfen.

Eine erfolgreiche HTTP-Antwort ist kein bestätigter Gerätezustand. Einstellung rücklesen, bei ungewissem Schreibausgang keinen automatischen zweiten Schreibversuch. Keine Start-/Reconnect-Befehle und zunächst ausdrücklich ausgelöste Portalaktualisierung wie in P05.

| Quellfeld / Ableitung | Typ geplant | Unit | Zugriff | Kurzbeschreibung | MQTT-Topic |
| --- | --- | --- | --- | --- | --- |
| `optionalEnergyDemand.minPvPercentage` | integer | % | RW freigegeben; Implementierung offen | Mindestanteil PV bei optionalem Laden, 0…100; keine gemessene Energiequote. | `homie/sma-echarger/portal/pv-minimum` |
| `100 − minPvPercentage` | integer | % | RO; A | Daraus berechneter erlaubter Netzanteil; eine Vorgabe, kein Ist-Netzanteil. | `homie/sma-echarger/portal/grid-share` |
| `optionalEnergyDemand.isOptionalConsumer` | boolean | — | RO | Ob dieser Verbraucher optionalen Energiebedarf unterstützt. | `homie/sma-echarger/portal/optional-consumer` |
| `optionalEnergyDemand.pvSurplusOnly` | boolean/nullable | — | RO | Besonderer Überschussmodus; null bleibt von false unterscheidbar. | `homie/sma-echarger/portal/pv-surplus-only` |
| `optionalEnergyDemand.feedInLimitation` | offen | offen | RO/K | Zusatzinformation zur Einspeisebegrenzung; Typ/Einheit nicht bestätigt. | `homie/sma-echarger/portal/feed-in-limitation` |
| `optionalEnergyDemand.priceLimit` | float/nullable | offen | RO | Optionales Preislimit; Währung/Skalierung dieses API-Felds separat prüfen. | `homie/sma-echarger/portal/price-limit` |
| `optionalEnergyDemand.usePriceLimit` | boolean | — | RO | Ob das Preislimit verwendet wird; beeinflusst zulässige PV-Befehle. | `homie/sma-echarger/portal/use-price-limit` |
| `_links.ui_Edit_OptionalEnergyDemand vorhanden` | boolean | — | RO; A | Schreibberechtigung der angemeldeten Rolle für optionalen Energiebedarf. | `homie/sma-echarger/portal/writable` |
| `P05-Modusklassifizierung` | string/enum | — | RO; A | PV/Netz-, Überschuss- oder Preismodus aus den Feldern bestimmen. | `homie/sma-echarger/portal/setting-mode` |

`nullable`-Werte brauchen ein ausdrücklich dokumentiertes Homie-Stringformat mit `unknown`/`unset` oder eine separate Gültigkeitsproperty. Ein Homie-Boolean kann kein `null` transportieren; daraus nicht stillschweigend `false` machen. Kosten- und Modusfelder werden erst mit geklärter Typabbildung veröffentlicht.

### Weitere Werte der tatsächlich gesehenen Portaloberfläche

Quelle U01. Die aktive Anlagenansicht liefert die folgenden Kategorien; die zweite Ansicht ohne Live-Daten wird nicht als zusätzliche Messquelle verwendet. **Alle folgenden Topics sind K: Web-API-Endpunkte, Zeitskalen, Rechte und Aktualität sind noch zu bestätigen.** Sie erweitern die dokumentierte Möglichkeit, nicht den ersten Cloud-Adapter. Lokale gleichwertige Werte haben Vorrang; Portalhistorie und Momentanwerte bekommen getrennte Zeitstempel und werden nicht als zusätzliche Energie addiert.

| Portalwert | Unit geplant | Kurzbeschreibung | MQTT-Topic (K) |
| --- | --- | --- | --- |
| PV-Erzeugung | W | Aktuelle PV-Leistung der Anlage. | `homie/sma-home-manager/portal/pv-power` |
| Netzbezug | W | Aktueller Bezug am Netzanschlusspunkt; Anzeige/Quelle prüfen. | `homie/sma-home-manager/portal/grid-import-power` |
| Netzeinspeisung | W | Aktuelle Einspeisung am Netzanschlusspunkt. | `homie/sma-home-manager/portal/grid-export-power` |
| Batterieladung | W | Aktuelle Ladeleistung des stationären Speichers. | `homie/sma-home-manager/portal/battery-charge-power` |
| Batterieentladung | W | Aktuelle Entladeleistung, abhängig vom Betriebszustand. | `homie/sma-home-manager/portal/battery-discharge-power` |
| Verbrauch | W | Anlagenverbrauch laut Portalbilanz. | `homie/sma-home-manager/portal/consumption-power` |
| Autarkie | % | Im Portal angezeigter Selbstversorgungsanteil; Zeitbezug prüfen. | `homie/sma-home-manager/portal/self-sufficiency` |
| Eigenverbrauch | % | Im Portal angezeigte Eigenverbrauchsquote; Formel/Zeitbezug prüfen. | `homie/sma-home-manager/portal/self-consumption-ratio` |
| Batterie-SoC | % | Ladezustand der stationären Batterie, nicht des Fahrzeugs. | `homie/sma-home-manager/portal/battery-soc` |
| PV-Überschuss | W | Im Portal errechnete momentan verfügbare PV-Leistung. | `homie/sma-home-manager/portal/pv-surplus-power` |
| Netzsystemdienstleistungen: Quelle | — | Angezeigter Steuerkanal, hier Modbus; beweist allein keinen aktiven externen Schreibcontroller. | `homie/sma-home-manager/portal/grid-control-source` |
| Aktuelle Wirkleistungsbegrenzung | % | Vom Portal angezeigte Begrenzung für die Anlage. | `homie/sma-home-manager/portal/active-power-limit` |
| Installierte PV-Leistung | kWp | Nenn-/Konfigurationswert der Anlage, kein Ist-Messwert. | `homie/sma-home-manager/portal/pv-capacity` |
| Batteriekapazität | kWh | Konfigurierter Kapazitätswert der stationären Batterie; nutzbar/nominal prüfen. | `homie/sma-home-manager/portal/battery-capacity` |
| Netzgekoppelter Anlagenbetrieb | — | Betriebsart der Anlage laut Dashboard. | `homie/sma-home-manager/portal/operating-mode` |
| Geräte senden Live-Daten | — | Portal-Kommunikationsindikator; kein Beleg für lokale MQTT-Erreichbarkeit. | `homie/sma-home-manager/portal/live-data-available` |

| Aggregat laut Dashboard | MQTT-Unit geplant | Kurzbeschreibung | MQTT-Topic (K) |
| --- | --- | --- | --- |
| PV-Erzeugung — Heute | kWh | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/pv-energy-day` |
| PV-Erzeugung — Aktueller Monat | kWh | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/pv-energy-month` |
| PV-Erzeugung — Aktuelles Jahr | kWh | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/pv-energy-year` |
| Batterieladung — Heute | kWh | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/battery-charge-energy-day` |
| Batterieladung — Aktueller Monat | kWh | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/battery-charge-energy-month` |
| Batterieladung — Aktuelles Jahr | kWh | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/battery-charge-energy-year` |
| Batterieentladung — Heute | kWh | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/battery-discharge-energy-day` |
| Batterieentladung — Aktueller Monat | kWh | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/battery-discharge-energy-month` |
| Batterieentladung — Aktuelles Jahr | kWh | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/battery-discharge-energy-year` |
| Netzbezug am Home Manager — Heute | kWh | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/grid-import-energy-day` |
| Netzbezug am Home Manager — Aktueller Monat | kWh | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/grid-import-energy-month` |
| Netzbezug am Home Manager — Aktuelles Jahr | kWh | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/grid-import-energy-year` |
| Netzeinspeisung am Home Manager — Heute | kWh | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/grid-export-energy-day` |
| Netzeinspeisung am Home Manager — Aktueller Monat | kWh | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/grid-export-energy-month` |
| Netzeinspeisung am Home Manager — Aktuelles Jahr | kWh | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/grid-export-energy-year` |
| Vermiedene CO₂-Emissionen — Heute | kg | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/co2-avoided-day` |
| Vermiedene CO₂-Emissionen — Gesamt | kg | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/co2-avoided-total` |
| Einspeisevergütung als Geldbetrag — Heute | EUR | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/feed-in-revenue-day` |
| Einspeisevergütung als Geldbetrag — Gesamt | EUR | Historischer/aggregierter Portalwert; Wh/kWh/MWh bzw. kg/t normalisieren, Zeitraum/Zeitzone bestätigen. | `homie/sma-home-manager/portal/feed-in-revenue-total` |

| Wallbox im Portal | Unit geplant | Kurzbeschreibung | MQTT-Topic (K) |
| --- | --- | --- | --- |
| Status Ladestation | — | Portal-Gerätestatus; lokaler Status bleibt bevorzugte Quelle. | `homie/sma-echarger/portal/device-health` |
| Status Fahrzeug | — | Verbindungs-/Ladestatus des Fahrzeugs, kein SoC. | `homie/sma-echarger/portal/vehicle-status` |
| Ladeleistung | W | Leistungsanzeige im Portal; getrennt vom lokalen Messwert. | `homie/sma-echarger/portal/charging-power` |
| Letzter Ladevorgang | kWh | Angezeigte Energie des letzten Ladevorgangs; Sessiongrenze bestätigen. | `homie/sma-echarger/portal/last-session-energy` |
| Verbrauch heute / Monat / Jahr | kWh | Drei getrennte Zeitaggregate der Wallbox. | `homie/sma-echarger/portal/energy-day`; `homie/sma-echarger/portal/energy-month`; `homie/sma-echarger/portal/energy-year` |
| Maximale Leistungsaufnahme | W | Geräteeigenschaft; im Portal konfiguriert, nicht automatisch Datenblatt-Nennleistung. | `homie/sma-echarger/portal/max-power` |
| Priorität | — | Planungspriorität des Verbrauchers im Home Manager. | `homie/sma-echarger/portal/priority` |

Die [offizielle Energiebilanz-Anleitung](https://manuals.sma.de/HM-20-ennexOS/de-DE/13856916363.html) beschreibt zusätzlich historische Erzeugung, Netzbezug, Einspeisung, Eigenverbrauch, Verbrauch, Batterieflüsse und Selbstversorgung einschließlich Download. Die hier nicht direkt gesehenen Historienwerte bleiben D/K; passende Endpunkte und Aggregationsintervalle dürfen nicht aus Dashboard-URLs geraten werden.

| Weitere Portalhistorie | Unit | Kurzbeschreibung | MQTT-Topic (D/K) |
| --- | --- | --- | --- |
| Netzbezugsenergie | kWh | Zeitaggregat des Netzbezugs; Zeitraum konfigurierbar, Metadaten nötig. | `homie/sma-home-manager/portal/grid-import-energy` |
| Netzeinspeiseenergie | kWh | Zeitaggregat der Einspeisung. | `homie/sma-home-manager/portal/grid-export-energy` |
| Verbrauchsenergie | kWh | Verbrauch aus der Portal-Energiebilanz. | `homie/sma-home-manager/portal/consumption-energy` |
| Eigenverbrauchsenergie | kWh | Lokal verwendete Erzeugungsenergie gemäß Portaldefinition. | `homie/sma-home-manager/portal/self-consumption-energy` |
| Messzeitraum Beginn / Ende | —; ISO 8601 | Zeitgrenzen dieser konfigurierten Historienabfrage; keine gleitenden Werte ohne Zeitraumkennzeichnung. | `homie/sma-home-manager/portal/period-start`; `homie/sma-home-manager/portal/period-end` |

### Portal-Einstellungen des Home Managers und weitere Bedienmöglichkeiten

U01 bestätigt die sichtbaren Bediengruppen, W04/S05 ergänzen deren Bedeutung. Für diese Tabelle gilt **RO als möglicher MQTT-Zustand, kein freigegebenes `/set`**. Eine „Bearbeiten“-Schaltfläche belegt eine UI-Bedienmöglichkeit für das Konto; sie belegt weder einen implementierten API-Befehl noch eine erfolgreiche Geräteänderung. Die Bridge bleibt zunächst bei lokalen eCharger-Optionen und dem einen PV-Portalsetter.

| Portal-/HM-Einstellung | Unit geplant | Nachweis | Kurzbeschreibung | MQTT-Topic (RO-Kandidat) |
| --- | --- | --- | --- | --- |
| Prognosebasiertes Batterieladen | — | U01/D | Batterieladen anhand Erzeugungs-/Verbrauchsprognose planen. | `homie/sma-home-manager/settings/forecast-charging-enabled` |
| Erforderlicher Batterieladezustand | % | U01/D | SoC-Schwelle für den Beginn prognoseabhängigen Ladens. | `homie/sma-home-manager/settings/forecast-min-soc` |
| Verkürzter Prognosezeitraum | — | U01/D | Kürzeren Planungshorizont für prognosebasiertes Laden verwenden. | `homie/sma-home-manager/settings/short-forecast-enabled` |
| Priorisiertes Batterieladen | — | U01/D | Batterieladung gegenüber optionalen Verbrauchern priorisieren. | `homie/sma-home-manager/settings/battery-priority-enabled` |
| Zeitfenstergesteuertes Batterieladen | — | U01 | Laden während konfigurierter Zeitfenster aktivieren. | `homie/sma-home-manager/settings/scheduled-charging-enabled` |
| Batterie-Ladezeitfenster | —; strukturierter Zeitplan | K | Wochentage, Beginn/Ende und weitere Planfelder anhand tatsächlicher Antwort bestimmen. | `homie/sma-home-manager/settings/battery-charge-schedule` |
| Lastspitzenkappung aktiv | — | U01/D | Netzbezugsspitzen mithilfe der Batterie begrenzen. | `homie/sma-home-manager/settings/peak-shaving-enabled` |
| Bezugsleistungsgrenze | W | D/K | Netzbezugsgrenze für Lastspitzenkappung; genaue API-Einheit prüfen. | `homie/sma-home-manager/settings/peak-shaving-limit` |
| Multi-Use-SoC-Grenze | % | D/K | Batterie-Kapazitätsaufteilung zwischen Eigenverbrauch und Spitzenkappung. | `homie/sma-home-manager/settings/peak-shaving-multi-use-soc` |
| Adaptive Spitzenkappung | — | D/K | SoC-/Leistungsgrenzen automatisch an die Anwendung anpassen. | `homie/sma-home-manager/settings/peak-shaving-adaptive` |
| Optimierungsziel | —; enum | U01/D | Ökologisch, ausgewogen oder wirtschaftlich; verändert Planungsschwerpunkte. | `homie/sma-home-manager/settings/optimization-goal` |
| Tarifart | —; enum | U01/D | Fester, zeitbasierter oder dynamischer Stromtarif; Anbieterabhängigkeiten prüfen. | `homie/sma-home-manager/settings/electricity-tariff-type` |
| Strompreis | EUR/kWh | U01 | Konfigurierter Bezugspreis; zeitabhängige Preise brauchen gültige Zeitfenster. | `homie/sma-home-manager/settings/electricity-price` |
| Einspeisevergütung | EUR/kWh | U01 | Konfigurierter Vergütungssatz, unabhängig vom Geldbetragsaggregat. | `homie/sma-home-manager/settings/feed-in-tariff` |
| Währung | — | U01 | Währung der Tarif- und Geldwerte; nicht immer EUR voraussetzen. | `homie/sma-home-manager/settings/currency` |
| Zeitbasierte Netzentgelte | EUR/kWh; Zeitplan | U01 | Zu-/Abschläge in konfigurierten Zeiträumen; vollständiges Schema offen. | `homie/sma-home-manager/settings/grid-fee-schedule` |
| Negative Strompreise berücksichtigen | — | U01 | Vergütungsberechnung bei negativen Preisen; laut UI ohne Auswirkung auf Verbraucherplanung. | `homie/sma-home-manager/settings/negative-price-accounting` |
| Datenabfrageintervall | —; enum | D/K S05 | Automatisch/stündlich/täglich; ältere Portaloption, ennexOS-Geltung prüfen. | `homie/sma-home-manager/settings/data-query-interval` |
| Direkte Zählerkommunikation | — | D/K S05 | Gezielte Telegrammzustellung kann Multicast ersetzen; Empfang zuerst prüfen. | `homie/sma-home-manager/settings/direct-meter-communication` |
| Messintervall | ms | U01 | Intervall der lokalen Zählermessung; im Portal angezeigt, Telegrammrhythmus getrennt prüfen. | `homie/sma-home-manager/settings/meter-interval` |
| Externer Stromwandler | — | U01 | Ob externe Stromwandler für die Zählermessung verwendet werden. | `homie/sma-home-manager/settings/external-current-transformer` |
| Home-Manager-Betriebsart | — | U01 | Geräterolle, hier System Manager; nicht mit Modbus-Clientrolle verwechseln. | `homie/sma-home-manager/settings/operating-mode` |
| Speedwire-Verschlüsselung | — | D/K | Beeinflusst lokale Protokollnutzung; tatsächlichen Zustand prüfen. | `homie/sma-home-manager/settings/speedwire-encryption` |
| Edimax-Kommunikation verwenden | — | U01 | Einbindung kompatibler Steckdosen; keine deren Messwerte bestätigt. | `homie/sma-home-manager/settings/edimax-enabled` |
| FRITZ!Box-Schnittstelle eingerichtet | — | U01 | AVM-Smart-Home-Integration; Zugangsdaten bleiben privat. | `homie/sma-home-manager/settings/fritz-integration-configured` |
| Shelly-Kommunikation verwenden | — | U01 | Einbindung kompatibler Shelly-Geräte. | `homie/sma-home-manager/settings/shelly-enabled` |
| Modbus-Geräte verwenden | — | U01 | Home Manager als Client externer Geräte; getrennt vom NSD-Server. | `homie/sma-home-manager/settings/modbus-client-enabled` |
| Nutzerdefinierte Wirkleistungsbegrenzung | — | U01 | Begrenzungsmodus der Anlage; Netzschutzfunktion, kein allgemeiner Ladebefehl. | `homie/sma-home-manager/settings/user-active-power-limit-enabled` |
| NSD-Vorgabe über Modbus | — | U01 | Aktivierung lokaler NSD-Vorgaben; in der geprüften UI ausgeschaltet. | `homie/sma-home-manager/settings/nsd-modbus-enabled` |
| FNN-Steuerbox Verbindungszustand | — | U01 | Verbindung zu externem Netzsteuergerät; keine Schlüssel/Pairingdaten publizieren. | `homie/sma-home-manager/settings/fnn-connection-status` |
| Verbrauchersteuerung § 14a | — | U01 | Angezeigte Aktivierung der Netzbetreibervorgaben für steuerbare Verbraucher. | `homie/sma-home-manager/settings/grid-consumer-control-enabled` |
| Einspeisebegrenzung § 9 | — | U01 | Angezeigte Aktivierung der Netzbetreibervorgaben für die Einspeisung. | `homie/sma-home-manager/settings/grid-export-control-enabled` |

Quellen für die zusätzlichen Funktionsdetails: [Prognoseladen](https://manuals.sma.de/HM-20-ennexOS/de-DE/12563269899.html), [Optimierungsziel](https://manuals.sma.de/HM-20-ennexOS/de-DE/13841009035.html), [Lastspitzenkappung](https://manuals.sma.de/HM-20-ennexOS/de-DE/13840653451.html), [Tarife](https://manuals.sma.de/HM-20-ennexOS/de-DE/13856910475.html), [PV-Anteil](https://manuals.sma.de/HM-20-ennexOS/de-DE/13674317323.html). Aktuelle Tarifwerte und SoC-Vorgaben werden hier bewusst nicht als feste Bridge-Defaults hinterlegt.

Weitere sichtbare Menüfunktionen sind Anlagenüberwachung/Status/Ereignisse, Geräteparameter, Geräteverwaltung, Anlageneigenschaften, Teilanlagen, Sensorzuweisung, Zählerkonfiguration, Netzsystemdienstleistungen, Datenexport sowie Benachrichtigungen. Am Home Manager sind auch Neustart und Parameteraktualisierung als administrative UI-Aktionen sichtbar (X, keine MQTT-Befehle). Datenexport ist als spätere Historienquelle denkbar; automatische Planung/Intervalle, Exportformat und API noch prüfen. Konto-/Benutzerrechte, Benachrichtigungsadressen, Anlagenstandort, private Bezeichnungen und Lizenzkäufe erhalten kein MQTT-Topic (X). Wetter-/Ertragsprognosen sind mögliche Zusatzquellen; Vorhersagehorizont, Einheiten und API sind noch nicht inventarisiert, deshalb kein scheinbar fertiges Wertemapping.

### Vollständige Parameter-Metadaten aus den aktuellen Portalexporten

Quelle U02: Am 2026-10-10 über die sichtbare CSV-Exportfunktion für die aktuellen Geräte heruntergeladen. Übernommen werden ausschließlich Gruppe, technischer Kanal, deutsche Bedeutung, Einheit und die Zugriffskennzeichnung. **Aktuelle Einstellwerte, übersetzte Werte, Anlagen-/Gerätekennungen und Export-Kopfmetadaten werden nicht übernommen.** Die vollständigen Exporte liegen lokal im Downloadordner und gehören nicht ins Repository.

Diese Tabellen sind der für das angemeldete Portal sichtbare Parameterbestand; Live-Messkanäle sind eine andere Quelle. `RO` ist die Zugriffsangabe dieses Exports, keine universelle Aussage über Installateurrechte am lokalen Gerät. Ein leerer Einheitseintrag wird als „nicht angegeben“ erhalten; aus einem aktuellen Wert wird kein zulässiger Bereich abgeleitet. Portal-API-Abfrage und Aktualität sind noch offen. Die Topics sind lesende Kandidaten unter `parameters`; gleiche physikalische Bedeutungen im Register-/UI-Katalog werden später mit einer kanonischen Quelle zusammengeführt.

#### Portalparameter: Home Manager 2.0

| Portal-Kanal | Gruppe | Export-Unit | Export-Zugriff | Kurzbeschreibung | MQTT-Topic (lesender Kandidat) |
| --- | --- | --- | --- | --- | --- |
| `Parameter.AVM.FritzboxUrl` | Externe Kommunikation | nicht angegeben | RO | Fritz!Box-Adresse; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.AVM.FritzboxUsr` | Externe Kommunikation | nicht angegeben | RO | Fritz!Box-Benutzer; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.AVM.IsOn` | Externe Kommunikation | nicht angegeben | RO | AVM FRITZ!Box SmartHome Steuerung | `homie/sma-home-manager/parameters/avm-ison` |
| `Parameter.AVM.LEDUse` | Externe Kommunikation | nicht angegeben | RO | Statusanzeige über | `homie/sma-home-manager/parameters/avm-leduse` |
| `Parameter.Dev.ExCT` | Gerät | nicht angegeben | RO | externer Stromwandler | `homie/sma-home-manager/parameters/dev-exct` |
| `Parameter.Dev.PriA` | Gerät | nicht angegeben | RO | Primärstrom | `homie/sma-home-manager/parameters/dev-pria` |
| `Parameter.Dev.ScdA` | Gerät | nicht angegeben | RO | Sekundärstrom | `homie/sma-home-manager/parameters/dev-scda` |
| `Parameter.DevUpd.IsOn` | Anlagenkommunikation | nicht angegeben | RO | Geräte-Updates eingeschaltet | `homie/sma-home-manager/parameters/devupd-ison` |
| `Parameter.EEBus.LPC.IsOn` | Energiemanagement | nicht angegeben | RO | Begrenzung der Bezugsleistung | `homie/sma-home-manager/parameters/eebus-lpc-ison` |
| `Parameter.EEBus.LPP.IsOn` | Energiemanagement | nicht angegeben | RO | Begrenzung der Einspeiseleistung | `homie/sma-home-manager/parameters/eebus-lpp-ison` |
| `Parameter.EEBus.SKI` | Externe Kommunikation | nicht angegeben | RO | EEBUS SKI Gerätekennung; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Eth.SCastIpCfg` | Externe Kommunikation | nicht angegeben | RO | Direkte Zäherkonfiguration; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Inverter.CtlComCfg.WCtlCom.CtlComMssMod` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Externe Wirkleistungsvorgabe, Rückfallverhalten | `homie/sma-home-manager/parameters/inverter-ctlcomcfg-wctlcom-ctlcommssmod` |
| `Parameter.Inverter.CtlComCfg.WCtlCom.FlbWNom` | Anlagen- und Gerätesteuerung | % | RO | Rückfallwert Wirkleistungsbegrenzung P in % von WMax für ausbleibende Wirkleistungsbegrenzung | `homie/sma-home-manager/parameters/inverter-ctlcomcfg-wctlcom-flbwnom` |
| `Parameter.Inverter.CtlComCfg.WCtlCom.TmsOut` | Anlagen- und Gerätesteuerung | s | RO | Externe Wirkleistungsvorgabe, Timeout | `homie/sma-home-manager/parameters/inverter-ctlcomcfg-wctlcom-tmsout` |
| `Parameter.Inverter.WModCfg.WCtlComCfg.Ena` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Externe Wirkleistungsvorgabe | `homie/sma-home-manager/parameters/inverter-wmodcfg-wctlcomcfg-ena` |
| `Parameter.Itf.MsCyc` | Gerät | nicht angegeben | RO | Messintervall | `homie/sma-home-manager/parameters/itf-mscyc` |
| `Parameter.Mb.DetCfg` | Anlagenkommunikation | nicht angegeben | RO | Modbus Geräte | `homie/sma-home-manager/parameters/mb-detcfg` |
| `Parameter.Mb.TcpSrv.IsOn` | Externe Kommunikation | nicht angegeben | RO | Modbus TCP-Server eingeschaltet | `homie/sma-home-manager/parameters/mb-tcpsrv-ison` |
| `Parameter.Mb.TcpSrv.Port` | Externe Kommunikation | nicht angegeben | RO | Modbus TCP-Server-Port | `homie/sma-home-manager/parameters/mb-tcpsrv-port` |
| `Parameter.Metering.MsItf1.MsType` | AC-Seite | nicht angegeben | RO | Typ des Zählers am Mess-Interface 1 | `homie/sma-home-manager/parameters/metering-msitf1-mstype` |
| `Parameter.Metering.MsItf1.PIC` | AC-Seite | nicht angegeben | RO | PIC des Zählers am Mess-Interface 1; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Metering.MsItf2.MsType` | AC-Seite | nicht angegeben | RO | Typ des Zählers am Mess-Interface 2 | `homie/sma-home-manager/parameters/metering-msitf2-mstype` |
| `Parameter.Metering.MsItf2.PIC` | AC-Seite | nicht angegeben | RO | PIC des Zählers am Mess-Interface 2; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Metering.MsItf3.MsType` | AC-Seite | nicht angegeben | RO | Typ des Zählers am Mess-Interface 3 | `homie/sma-home-manager/parameters/metering-msitf3-mstype` |
| `Parameter.Nameplate.CmpMain.HwRev` | Gerätekomponenten | nicht angegeben | RO | Hardware-Version des Hauptprozessors | `homie/sma-home-manager/parameters/nameplate-cmpmain-hwrev` |
| `Parameter.Nameplate.CmpMain.SwRev` | Gerätekomponenten | nicht angegeben | RO | Firmware-Version des Hauptprozessors | `homie/sma-home-manager/parameters/nameplate-cmpmain-swrev` |
| `Parameter.Nameplate.CmpOS.SwRev` | Gerätekomponenten | nicht angegeben | RO | Firmware-Version des Betriebssystems | `homie/sma-home-manager/parameters/nameplate-cmpos-swrev` |
| `Parameter.Nameplate.Location` | Typenschild | nicht angegeben | RO | Gerätename; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.MainModel` | Typenschild | nicht angegeben | RO | Geräteklasse | `homie/sma-home-manager/parameters/nameplate-mainmodel` |
| `Parameter.Nameplate.Model` | Typenschild | nicht angegeben | RO | Gerätetyp | `homie/sma-home-manager/parameters/nameplate-model` |
| `Parameter.Nameplate.PkgRev` | Typenschild | nicht angegeben | RO | Firmware-Version | `homie/sma-home-manager/parameters/nameplate-pkgrev` |
| `Parameter.Operation.LdcBatChaPrio` | Energiemanagement | nicht angegeben | RO | Priorisiertes Batterieladen | `homie/sma-home-manager/parameters/operation-ldcbatchaprio` |
| `Parameter.Operation.LdcFcBatCha.IsOn` | Energiemanagement | nicht angegeben | RO | Prognosebasiertes Batterieladen | `homie/sma-home-manager/parameters/operation-ldcfcbatcha-ison` |
| `Parameter.Operation.LdcFcBatCha.ShrtIsOn` | Energiemanagement | nicht angegeben | RO | Verkürzter Prognosezeitraum | `homie/sma-home-manager/parameters/operation-ldcfcbatcha-shrtison` |
| `Parameter.Operation.LdcFcBatCha.SocThold` | Energiemanagement | % | RO | Erforderlicher Batterieladezustand (SoC) | `homie/sma-home-manager/parameters/operation-ldcfcbatcha-socthold` |
| `Parameter.PCC.DynWMax` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Dynamische Wirkleistungsbegrenzung am Netzanschlusspunkt | `homie/sma-home-manager/parameters/pcc-dynwmax` |
| `Parameter.PCC.WMax` | Anlagen- und Gerätesteuerung | W | RO | Eingestellte Wirkleistungsgrenze am Netzanschlusspunkt | `homie/sma-home-manager/parameters/pcc-wmax` |
| `Parameter.PCC.WMaxMod` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Betriebsart der Wirkleistungsbegrenzung am Netzanschlusspunkt | `homie/sma-home-manager/parameters/pcc-wmaxmod` |
| `Parameter.PCC.WMaxNom` | Anlagen- und Gerätesteuerung | % | RO | Eingestellte Wirkleistungsgrenze am Netzanschlusspunkt | `homie/sma-home-manager/parameters/pcc-wmaxnom` |
| `Parameter.Plnt.DcWRtg` | DC-Seite | W | RO | Anlagen-Nennleistung | `homie/sma-home-manager/parameters/plnt-dcwrtg` |
| `Parameter.PLS.BllIntv` | Energiemanagement | nicht angegeben | RO | Abrechnungszeitraum | `homie/sma-home-manager/parameters/pls-bllintv` |
| `Parameter.PLS.BllIntvStrDy` | Energiemanagement | nicht angegeben | RO | Start des Abrechnungszeitraums (Tag) | `homie/sma-home-manager/parameters/pls-bllintvstrdy` |
| `Parameter.PLS.BllIntvStrMth` | Energiemanagement | nicht angegeben | RO | Start des Abrechnungszeitraums (Monat) | `homie/sma-home-manager/parameters/pls-bllintvstrmth` |
| `Parameter.PLS.IsOn` | Energiemanagement | nicht angegeben | RO | Lastspitzenkappung | `homie/sma-home-manager/parameters/pls-ison` |
| `Parameter.PLS.SocThold` | Energiemanagement | % | RO | Schwelle zum Umschalten der Betriebsmodi (Multi Use): Batterieladezustand (SoC) | `homie/sma-home-manager/parameters/pls-socthold` |
| `Parameter.PLS.TholdIncIsOn` | Energiemanagement | nicht angegeben | RO | Adaptive Erhöhung des Schwellwerts | `homie/sma-home-manager/parameters/pls-tholdincison` |
| `Parameter.PLS.TholdRsIsOn` | Energiemanagement | nicht angegeben | RO | Automatisches Zurücksetzen des Schwellwerts | `homie/sma-home-manager/parameters/pls-tholdrsison` |
| `Parameter.PLS.WInTholdStr` | Energiemanagement | W | RO | Schwellwert für die Lastspitzenkappung | `homie/sma-home-manager/parameters/pls-wintholdstr` |
| `Parameter.PortalUsrSettings.PlntId` | Sunny Portal | nicht angegeben | RO | Anlagenkennung im Portal; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.SelfCsmp.OpMod` | Gerät | nicht angegeben | RO | Anlage mit Eigenverbrauch | `homie/sma-home-manager/parameters/selfcsmp-opmod` |
| `Parameter.Shelly.Pwd` | Externe Kommunikation | nicht angegeben | RO | Shelly Passwort; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Spdwr.Sec.IsOn` | Externe Kommunikation | nicht angegeben | RO | Speedwire-Verschlüsselung aktivieren | `homie/sma-home-manager/parameters/spdwr-sec-ison` |
| `Parameter.Upd.AutoUpdIsOn` | Gerät | nicht angegeben | RO | Automatische Updates eingeschaltet | `homie/sma-home-manager/parameters/upd-autoupdison` |
| `Parameter.WebConn.SwRev` | Externe Kommunikation | nicht angegeben | RO | Version des Webconnect | `homie/sma-home-manager/parameters/webconn-swrev` |

#### Portalparameter: STP8.0-3AV-40

| Portal-Kanal | Gruppe | Export-Unit | Export-Zugriff | Kurzbeschreibung | MQTT-Topic (lesender Kandidat) |
| --- | --- | --- | --- | --- | --- |
| `Parameter.Acs.PwdIstl` | Benutzerrechte | nicht angegeben | RO | Installateurpasswort setzen; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Acs.PwdUsr` | Benutzerrechte | nicht angegeben | RO | Benutzerpasswort setzen; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Coolsys.FanTst` | Gerät | nicht angegeben | RO | Lüftertest; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.DcCfg.MPPShdw.CycTms` | DC-Seite | s | RO | Zeitintervall SMA ShadeFix | `homie/sma-inverter1/parameters/dccfg-mppshdw-cyctms` |
| `Parameter.DcCfg.MPPShdw.IsOn` | DC-Seite | nicht angegeben | RO | SMA ShadeFix | `homie/sma-inverter1/parameters/dccfg-mppshdw-ison` |
| `Parameter.DtTm.NtpSrv` | Gerät | nicht angegeben | RO | NTP-Server; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.DtTm.TmSynIsOn` | Gerät | nicht angegeben | RO | Automatische Zeitsynchronisation | `homie/sma-inverter1/parameters/dttm-tmsynison` |
| `Parameter.DtTm.TmZn` | Gerät | nicht angegeben | RO | Zeitzone | `homie/sma-inverter1/parameters/dttm-tmzn` |
| `Parameter.Eth.Proxy.IsOn` | Externe Kommunikation | nicht angegeben | RO | Ethernet Proxy eingeschaltet | `homie/sma-inverter1/parameters/eth-proxy-ison` |
| `Parameter.Eth.Proxy.Login` | Externe Kommunikation | nicht angegeben | RO | Ethernet Proxy-Server Login; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Eth.Proxy.Port` | Externe Kommunikation | nicht angegeben | RO | Ethernet Proxy-Server Port | `homie/sma-inverter1/parameters/eth-proxy-port` |
| `Parameter.Eth.Proxy.Srv` | Externe Kommunikation | nicht angegeben | RO | Ethernet Proxy-Server Adresse; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.GridGuard.Cntry` | Netzüberwachung | nicht angegeben | RO | Eingestellter Länderdatensatz | `homie/sma-inverter1/parameters/gridguard-cntry` |
| `Parameter.GridGuard.Cntry.Aid.AsymDet.AsymMax` | Netzüberwachung | % | RO | Inselnetzerkennung, Zulässige Netzunsymmetrie | `homie/sma-inverter1/parameters/gridguard-cntry-aid-asymdet-asymmax` |
| `Parameter.GridGuard.Cntry.Aid.AsymDet.AsymMaxTmms` | Netzüberwachung | ms | RO | Inselnetzerkennung, Auslösezeit der Unsymmetrieerkennung | `homie/sma-inverter1/parameters/gridguard-cntry-aid-asymdet-asymmaxtmms` |
| `Parameter.GridGuard.Cntry.Aid.AsymDet.Stt` | Netzüberwachung | nicht angegeben | RO | Inselnetzerkennung, Status der Unsymmetrieerkennung | `homie/sma-inverter1/parameters/gridguard-cntry-aid-asymdet-stt` |
| `Parameter.GridGuard.Cntry.Aid.HzMon.HzMonTmms` | Netzüberwachung | ms | RO | Inselnetzerkennung, Auslösezeit der Frequenzüberwachung | `homie/sma-inverter1/parameters/gridguard-cntry-aid-hzmon-hzmontmms` |
| `Parameter.GridGuard.Cntry.Aid.HzMon.Stt` | Netzüberwachung | nicht angegeben | RO | Inselnetzerkennung, Status der Frequenzüberwachung | `homie/sma-inverter1/parameters/gridguard-cntry-aid-hzmon-stt` |
| `Parameter.GridGuard.Cntry.AMaxOfs` | Netzüberwachung | A | RO | Auslöseschwelle Gleichstromüberwachung | `homie/sma-inverter1/parameters/gridguard-cntry-amaxofs` |
| `Parameter.GridGuard.Cntry.AMaxOfsTmms` | Netzüberwachung | ms | RO | Auslösezeit Gleichstromüberwachung | `homie/sma-inverter1/parameters/gridguard-cntry-amaxofstmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.ChgMax` | Netzüberwachung | Hz/s | RO | Frequenzüberwachung, Maximale Frequenzänderung pro Sekunde | `homie/sma-inverter1/parameters/gridguard-cntry-frqctl-chgmax` |
| `Parameter.GridGuard.Cntry.FrqCtl.ChgMaxTmms` | Netzüberwachung | ms | RO | Frequenzüberwachung, Maximale Frequenzänderung Auslösezeit | `homie/sma-inverter1/parameters/gridguard-cntry-frqctl-chgmaxtmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.hLim` | Netzüberwachung | Hz | RO | Frequenzüberwachung, untere Maximalschwelle | `homie/sma-inverter1/parameters/gridguard-cntry-frqctl-hlim` |
| `Parameter.GridGuard.Cntry.FrqCtl.hLimTmms` | Netzüberwachung | ms | RO | Frequenzüberwachung, untere Maximalschwelle Auslösezeit | `homie/sma-inverter1/parameters/gridguard-cntry-frqctl-hlimtmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.lLim` | Netzüberwachung | Hz | RO | Frequenzüberwachung, obere Minimalschwelle | `homie/sma-inverter1/parameters/gridguard-cntry-frqctl-llim` |
| `Parameter.GridGuard.Cntry.FrqCtl.lLimTmms` | Netzüberwachung | ms | RO | Frequenzüberwachung, obere Minimalschwelle Auslösezeit | `homie/sma-inverter1/parameters/gridguard-cntry-frqctl-llimtmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.Max` | Netzüberwachung | Hz | RO | Frequenzüberwachung, obere Maximalschwelle | `homie/sma-inverter1/parameters/gridguard-cntry-frqctl-max` |
| `Parameter.GridGuard.Cntry.FrqCtl.MaxTmms` | Netzüberwachung | ms | RO | Frequenzüberwachung, obere Maximalschwelle Auslösezeit | `homie/sma-inverter1/parameters/gridguard-cntry-frqctl-maxtmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.Min` | Netzüberwachung | Hz | RO | Frequenzüberwachung, untere Minimalschwelle | `homie/sma-inverter1/parameters/gridguard-cntry-frqctl-min` |
| `Parameter.GridGuard.Cntry.FrqCtl.MinTmms` | Netzüberwachung | ms | RO | Frequenzüberwachung, untere Minimalschwelle Auslösezeit | `homie/sma-inverter1/parameters/gridguard-cntry-frqctl-mintmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.ReconMax` | Netzüberwachung | Hz | RO | Maximale Zuschaltfrequenz | `homie/sma-inverter1/parameters/gridguard-cntry-frqctl-reconmax` |
| `Parameter.GridGuard.Cntry.FrqCtl.ReconMin` | Netzüberwachung | Hz | RO | Minimale Zuschaltfrequenz | `homie/sma-inverter1/parameters/gridguard-cntry-frqctl-reconmin` |
| `Parameter.GridGuard.Cntry.GriFltMonTms` | Netzüberwachung | s | RO | Zuschaltzeit nach Netzfehler | `homie/sma-inverter1/parameters/gridguard-cntry-grifltmontms` |
| `Parameter.GridGuard.Cntry.GriFltReConTms` | Netzüberwachung | s | RO | Schnellzuschaltzeit nach Kurzunterbrechung | `homie/sma-inverter1/parameters/gridguard-cntry-grifltrecontms` |
| `Parameter.GridGuard.Cntry.GriFltTms` | Netzüberwachung | s | RO | Maximale Dauer einer Kurzunterbrechung | `homie/sma-inverter1/parameters/gridguard-cntry-griflttms` |
| `Parameter.GridGuard.Cntry.GriStrTms` | Netzüberwachung | s | RO | Zuschaltzeit nach Neustart | `homie/sma-inverter1/parameters/gridguard-cntry-gristrtms` |
| `Parameter.GridGuard.Cntry.HzRtg` | Netzüberwachung | Hz | RO | Nennfrequenz | `homie/sma-inverter1/parameters/gridguard-cntry-hzrtg` |
| `Parameter.GridGuard.Cntry.LeakRisMin` | Netzüberwachung | Ohm | RO | Minimaler Isolationswiderstand | `homie/sma-inverter1/parameters/gridguard-cntry-leakrismin` |
| `Parameter.GridGuard.Cntry.PEOpnMon` | Netzüberwachung | nicht angegeben | RO | Überwachung Erdungsanschluss | `homie/sma-inverter1/parameters/gridguard-cntry-peopnmon` |
| `Parameter.GridGuard.Cntry.VolCtl.hhLimTmms` | Netzüberwachung | ms | RO | Spannungsüberwachung, mittlere Maximalschwelle Auslösezeit | `homie/sma-inverter1/parameters/gridguard-cntry-volctl-hhlimtmms` |
| `Parameter.GridGuard.Cntry.VolCtl.hLimTmms` | Netzüberwachung | ms | RO | Spannungsüberwachung, untere Maximalschwelle Auslösezeit | `homie/sma-inverter1/parameters/gridguard-cntry-volctl-hlimtmms` |
| `Parameter.GridGuard.Cntry.VolCtl.lLimTmms` | Netzüberwachung | ms | RO | Spannungsüberwachung, obere Minimalschwelle Auslösezeit | `homie/sma-inverter1/parameters/gridguard-cntry-volctl-llimtmms` |
| `Parameter.GridGuard.Cntry.VolCtl.llLimTmms` | Netzüberwachung | ms | RO | Spannungsüberwachung, mittlere Minimalschwelle Auslösezeit | `homie/sma-inverter1/parameters/gridguard-cntry-volctl-lllimtmms` |
| `Parameter.GridGuard.CntryBas` | Netzüberwachung | nicht angegeben | RO | Basierender Länderdatensatz | `homie/sma-inverter1/parameters/gridguard-cntrybas` |
| `Parameter.GridGuard.CntrySet` | Netzüberwachung | nicht angegeben | RO | Setze Länderdatensatz | `homie/sma-inverter1/parameters/gridguard-cntryset` |
| `Parameter.Inverter.CtlComCfg.VArCtlCom.FlbVArNom` | Anlagen- und Gerätesteuerung | % | RO | Externe Blindleistungsvorgabe, Rückfallwert | `homie/sma-inverter1/parameters/inverter-ctlcomcfg-varctlcom-flbvarnom` |
| `Parameter.Inverter.CtlComCfg.WCtlCom.CtlComMssMod` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Externe Wirkleistungsvorgabe, Rückfallverhalten | `homie/sma-inverter1/parameters/inverter-ctlcomcfg-wctlcom-ctlcommssmod` |
| `Parameter.Inverter.CtlComCfg.WCtlCom.TmsOut` | Anlagen- und Gerätesteuerung | s | RO | Externe Wirkleistungsvorgabe, Timeout | `homie/sma-inverter1/parameters/inverter-ctlcomcfg-wctlcom-tmsout` |
| `Parameter.Inverter.DGSModCfg.DGSMod` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Dynamische Netzstützung, Betriebsart | `homie/sma-inverter1/parameters/inverter-dgsmodcfg-dgsmod` |
| `Parameter.Inverter.FltAMod` | Gerät | nicht angegeben | RO | RCD Anpassung | `homie/sma-inverter1/parameters/inverter-fltamod` |
| `Parameter.Inverter.PlntCtl.VRef` | AC-Seite | V | RO | Netznennspannung | `homie/sma-inverter1/parameters/inverter-plntctl-vref` |
| `Parameter.Inverter.StopTms` | Gerät | s | RO | Abschaltverzögerung | `homie/sma-inverter1/parameters/inverter-stoptms` |
| `Parameter.Inverter.VArModCfg.VArCnstCfg.VArNom` | Anlagen- und Gerätesteuerung | % | RO | Manuelle Blindleistungsvorgabe bei Wirkleistungsabgabe | `homie/sma-inverter1/parameters/inverter-varmodcfg-varcnstcfg-varnom` |
| `Parameter.Inverter.VArModCfg.VArModOut` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Blindleistungsverfahren bei Wirkleistungsabgabe | `homie/sma-inverter1/parameters/inverter-varmodcfg-varmodout` |
| `Parameter.Inverter.VRtg` | Gerät | V | RO | Wechselrichternennspannung | `homie/sma-inverter1/parameters/inverter-vrtg` |
| `Parameter.Inverter.WGraReconEna` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Sanftanlauf P nach Netzfehler | `homie/sma-inverter1/parameters/inverter-wgrareconena` |
| `Parameter.Inverter.WLim` | Gerät | W | RO | Bemessungswirkleistung WMaxOutRtg | `homie/sma-inverter1/parameters/inverter-wlim` |
| `Parameter.Inverter.WMax` | Gerät | W | RO | Nennwirkleistung WMaxOut | `homie/sma-inverter1/parameters/inverter-wmax` |
| `Parameter.Inverter.WMaxIn` | AC-Seite | W | RO | Nennwirkleistung WMaxIn | `homie/sma-inverter1/parameters/inverter-wmaxin` |
| `Parameter.Inverter.WModCfg.WCnstCfg.W` | Anlagen- und Gerätesteuerung | W | RO | Wirkleistungsbegrenzung in W | `homie/sma-inverter1/parameters/inverter-wmodcfg-wcnstcfg-w` |
| `Parameter.Inverter.WModCfg.WCnstCfg.WNom` | Anlagen- und Gerätesteuerung | % | RO | Wirkleistungsbegrenzung in % | `homie/sma-inverter1/parameters/inverter-wmodcfg-wcnstcfg-wnom` |
| `Parameter.Inverter.WModCfg.WMod` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Betriebsart Wirkleistungsvorgabe | `homie/sma-inverter1/parameters/inverter-wmodcfg-wmod` |
| `Parameter.Mb.TcpSrv.IsOn` | Externe Kommunikation | nicht angegeben | RO | Modbus TCP-Server eingeschaltet | `homie/sma-inverter1/parameters/mb-tcpsrv-ison` |
| `Parameter.Mb.TcpSrv.Port` | Externe Kommunikation | nicht angegeben | RO | Modbus TCP-Server-Port | `homie/sma-inverter1/parameters/mb-tcpsrv-port` |
| `Parameter.Mb.UntId` | Externe Kommunikation | nicht angegeben | RO | Modbus Unit ID | `homie/sma-inverter1/parameters/mb-untid` |
| `Parameter.Metering.EnMtrTyp` | Anlagenkommunikation | nicht angegeben | RO | Verwendeter Energiezähler | `homie/sma-inverter1/parameters/metering-enmtrtyp` |
| `Parameter.Metering.GridMs.TotkWhInOfs` | AC-Seite | kWh | RO | Offset der aufgenommenen Energie setzen | `homie/sma-inverter1/parameters/metering-gridms-totkwhinofs` |
| `Parameter.Metering.GridMs.TotkWhOutOfs` | AC-Seite | kWh | RO | Offset der eingespeisten Energie setzen | `homie/sma-inverter1/parameters/metering-gridms-totkwhoutofs` |
| `Parameter.Metering.MsSpdwr.SerNumEN` | Anlagenkommunikation | nicht angegeben | RO | Seriennummer des Zählers an Speedwire; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Metering.TotFeedTmhSet` | AC-Seite | h | RO | Setze Gesamte Einspeisezeit am Netzanschlusspunkt | `homie/sma-inverter1/parameters/metering-totfeedtmhset` |
| `Parameter.Metering.TotkWhOutSet` | AC-Seite | kWh | RO | Setze Gesamtertrag | `homie/sma-inverter1/parameters/metering-totkwhoutset` |
| `Parameter.Metering.TotOpTmhSet` | AC-Seite | h | RO | Setze Gesamte Betriebszeit am Netzanschlusspunkt | `homie/sma-inverter1/parameters/metering-totoptmhset` |
| `Parameter.Nameplate.CmpCom.HwRev` | Gerätekomponenten | nicht angegeben | RO | Hardware-Version der Kommunikationsbaugruppe | `homie/sma-inverter1/parameters/nameplate-cmpcom-hwrev` |
| `Parameter.Nameplate.CmpCom.SerNum` | Gerätekomponenten | nicht angegeben | RO | Seriennummer der Kommunikationsbaugruppe; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpCom.SusyId` | Gerätekomponenten | nicht angegeben | RO | SUSyID der Kommunikationsbaugruppe | `homie/sma-inverter1/parameters/nameplate-cmpcom-susyid` |
| `Parameter.Nameplate.CmpCom.SwRev` | Gerätekomponenten | nicht angegeben | RO | Firmware-Version der Kommunikationsbaugruppe | `homie/sma-inverter1/parameters/nameplate-cmpcom-swrev` |
| `Parameter.Nameplate.CmpMain.Rev` | Gerätekomponenten | nicht angegeben | RO | Umbaustand des Hauptprozessors | `homie/sma-inverter1/parameters/nameplate-cmpmain-rev` |
| `Parameter.Nameplate.CmpMain.SerNum` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Hauptprozessors; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpMain.SusyId` | Gerätekomponenten | nicht angegeben | RO | SUSyID des Hauptprozessors | `homie/sma-inverter1/parameters/nameplate-cmpmain-susyid` |
| `Parameter.Nameplate.CmpMain.SwRev` | Gerätekomponenten | nicht angegeben | RO | Firmware-Version des Hauptprozessors | `homie/sma-inverter1/parameters/nameplate-cmpmain-swrev` |
| `Parameter.Nameplate.CmpOS.SwRev` | Gerätekomponenten | nicht angegeben | RO | Firmware-Version des Betriebssystems | `homie/sma-inverter1/parameters/nameplate-cmpos-swrev` |
| `Parameter.Nameplate.ComRev` | Typenschild | nicht angegeben | RO | Kommunikationsversion | `homie/sma-inverter1/parameters/nameplate-comrev` |
| `Parameter.Nameplate.Location` | Typenschild | nicht angegeben | RO | Gerätename; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.MacId` | Typenschild | nicht angegeben | RO | MAC-Adresse; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.MainModel` | Typenschild | nicht angegeben | RO | Geräteklasse | `homie/sma-inverter1/parameters/nameplate-mainmodel` |
| `Parameter.Nameplate.Model` | Typenschild | nicht angegeben | RO | Gerätetyp | `homie/sma-inverter1/parameters/nameplate-model` |
| `Parameter.Nameplate.PkgRev` | Typenschild | nicht angegeben | RO | Firmware-Version | `homie/sma-inverter1/parameters/nameplate-pkgrev` |
| `Parameter.Nameplate.SerNum` | Typenschild | nicht angegeben | RO | Seriennummer; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.WlMacId` | Typenschild | nicht angegeben | RO | WLAN-MAC-Adresse; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Operation.LodFnc` | Gerät | nicht angegeben | RO | Parameter laden | `homie/sma-inverter1/parameters/operation-lodfnc` |
| `Parameter.Operation.OpMod` | Gerät | nicht angegeben | RO | Allgemeine Betriebsart | `homie/sma-inverter1/parameters/operation-opmod` |
| `Parameter.PCC.FlbInv.WMax` | Anlagen- und Gerätesteuerung | W | RO | Rückfallwert Wirkleistungsbegrenzung, Regelung am Netzanschlusspunkt | `homie/sma-inverter1/parameters/pcc-flbinv-wmax` |
| `Parameter.PCC.FlbInv.WMaxNom` | Anlagen- und Gerätesteuerung | % | RO | Rückfallwert Wirkleistungsbegrenzung in Prozent, Regelung am Netzanschlusspunkt | `homie/sma-inverter1/parameters/pcc-flbinv-wmaxnom` |
| `Parameter.PCC.WMax` | Anlagen- und Gerätesteuerung | W | RO | Eingestellte Wirkleistungsgrenze am Netzanschlusspunkt | `homie/sma-inverter1/parameters/pcc-wmax` |
| `Parameter.PCC.WMaxMod` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Betriebsart der Wirkleistungsbegrenzung am Netzanschlusspunkt | `homie/sma-inverter1/parameters/pcc-wmaxmod` |
| `Parameter.PCC.WMaxNom` | Anlagen- und Gerätesteuerung | % | RO | Eingestellte Wirkleistungsgrenze am Netzanschlusspunkt | `homie/sma-inverter1/parameters/pcc-wmaxnom` |
| `Parameter.Plnt.DcWRtg` | DC-Seite | W | RO | Anlagen-Nennleistung | `homie/sma-inverter1/parameters/plnt-dcwrtg` |
| `Parameter.RS485.RS485Mod` | Anlagenkommunikation | nicht angegeben | RO | Protokoll RS485-Schnittstelle | `homie/sma-inverter1/parameters/rs485-rs485mod` |
| `Parameter.Spdwr.AutoCfgIsOn` | Anlagenkommunikation | nicht angegeben | RO | Automatische Speedwire-Konfiguration eingeschaltet | `homie/sma-inverter1/parameters/spdwr-autocfgison` |
| `Parameter.Spdwr.Cry` | Anlagenkommunikation | nicht angegeben | RO | Verschlüsselung | `homie/sma-inverter1/parameters/spdwr-cry` |
| `Parameter.Spdwr.DnsSrvIp` | Anlagenkommunikation | nicht angegeben | RO | Speedwire-IP-Adresse DNS-Server; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Spdwr.GwIp` | Anlagenkommunikation | nicht angegeben | RO | Speedwire-IP-Adresse Gateway; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Spdwr.Ip` | Anlagenkommunikation | nicht angegeben | RO | Speedwire-IP-Adresse; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Spdwr.SnetMsk` | Anlagenkommunikation | nicht angegeben | RO | Speedwire-Subnetzmaske; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.SwCmp.CmpMainBlt.SwRev` | Gerät | nicht angegeben | RO | Version des HP-Bootloaders | `homie/sma-inverter1/parameters/swcmp-cmpmainblt-swrev` |
| `Parameter.Upd.AutoUpdIsOn` | Gerät | nicht angegeben | RO | Automatische Updates eingeschaltet | `homie/sma-inverter1/parameters/upd-autoupdison` |
| `Parameter.WebConn.SwRev` | Externe Kommunikation | nicht angegeben | RO | Version des Webconnect | `homie/sma-inverter1/parameters/webconn-swrev` |
| `Parameter.Wl.IsOn` | Anlagenkommunikation | nicht angegeben | RO | WLAN ist eingeschaltet | `homie/sma-inverter1/parameters/wl-ison` |
| `Parameter.Wl.SoftAcsIsOn` | Anlagenkommunikation | nicht angegeben | RO | Soft-Access-Point ist eingeschaltet | `homie/sma-inverter1/parameters/wl-softacsison` |

#### Portalparameter: SBS3.7-10

| Portal-Kanal | Gruppe | Export-Unit | Export-Zugriff | Kurzbeschreibung | MQTT-Topic (lesender Kandidat) |
| --- | --- | --- | --- | --- | --- |
| `Parameter.Acs.PwdIstl` | Benutzerrechte | nicht angegeben | RO | Installateurpasswort setzen; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Acs.PwdUsr` | Benutzerrechte | nicht angegeben | RO | Benutzerpasswort setzen; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Bat.CapacRtgWh` | Batterie | Wh | RO | Nennkapazität der Batterie | `homie/sma-inverter2/parameters/bat-capacrtgwh` |
| `Parameter.Bat.CapacRtgWhArr[0]` | Batterie | Wh | RO | Nennkapazität der Batterie | `homie/sma-inverter2/parameters/bat-capacrtgwharr-0` |
| `Parameter.Bat.CapacRtgWhArr[1]` | Batterie | Wh | RO | Nennkapazität der Batterie | `homie/sma-inverter2/parameters/bat-capacrtgwharr-1` |
| `Parameter.Bat.CapacRtgWhArr[2]` | Batterie | Wh | RO | Nennkapazität der Batterie | `homie/sma-inverter2/parameters/bat-capacrtgwharr-2` |
| `Parameter.Bat.Typ` | Batterie | nicht angegeben | RO | Batterietyp | `homie/sma-inverter2/parameters/bat-typ` |
| `Parameter.BatConv.WMaxCha` | Batterie | W | RO | Maximale Ladeleistung des Batteriestellers | `homie/sma-inverter2/parameters/batconv-wmaxcha` |
| `Parameter.BatConv.WMaxDsch` | Batterie | W | RO | Maximale Entladeleistung des Batteriestellers | `homie/sma-inverter2/parameters/batconv-wmaxdsch` |
| `Parameter.BatUsDm.BckDmMin` | Batterie | % | RO | Minimale Breite des Ersatzstrombereichs | `homie/sma-inverter2/parameters/batusdm-bckdmmin` |
| `Parameter.BatUsDm.DschProDmLim` | Batterie | % | RO | Tiefenentladeschutzbereich | `homie/sma-inverter2/parameters/batusdm-dschprodmlim` |
| `Parameter.BatUsDm.DschProDmMin` | Batterie | % | RO | Entladestoppbereich | `homie/sma-inverter2/parameters/batusdm-dschprodmmin` |
| `Parameter.BatUsDm.SelfCsmpBrd` | Batterie | % | RO | Breite des Bereichs zur Erhaltung des Batterieladezustands | `homie/sma-inverter2/parameters/batusdm-selfcsmpbrd` |
| `Parameter.CmpMdul.RS485Mod` | Anlagenkommunikation | nicht angegeben | RO | Protokoll RS485-Schnittstelle | `homie/sma-inverter2/parameters/cmpmdul-rs485mod` |
| `Parameter.DtTm.NtpSrv` | Gerät | nicht angegeben | RO | NTP-Server; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.DtTm.TmSynIsOn` | Gerät | nicht angegeben | RO | Automatische Zeitsynchronisation | `homie/sma-inverter2/parameters/dttm-tmsynison` |
| `Parameter.DtTm.TmZn` | Gerät | nicht angegeben | RO | Zeitzone | `homie/sma-inverter2/parameters/dttm-tmzn` |
| `Parameter.Eth.Proxy.IsOn` | Externe Kommunikation | nicht angegeben | RO | Ethernet Proxy eingeschaltet | `homie/sma-inverter2/parameters/eth-proxy-ison` |
| `Parameter.Eth.Proxy.Login` | Externe Kommunikation | nicht angegeben | RO | Ethernet Proxy-Server Login; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Eth.Proxy.Port` | Externe Kommunikation | nicht angegeben | RO | Ethernet Proxy-Server Port | `homie/sma-inverter2/parameters/eth-proxy-port` |
| `Parameter.Eth.Proxy.Srv` | Externe Kommunikation | nicht angegeben | RO | Ethernet Proxy-Server Adresse; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.GridGuard.Cntry` | Netzüberwachung | nicht angegeben | RO | Eingestellter Länderdatensatz | `homie/sma-inverter2/parameters/gridguard-cntry` |
| `Parameter.GridGuard.Cntry.Aid.HzMon.HzMonTmms` | Netzüberwachung | ms | RO | Inselnetzerkennung, Auslösezeit der Frequenzüberwachung | `homie/sma-inverter2/parameters/gridguard-cntry-aid-hzmon-hzmontmms` |
| `Parameter.GridGuard.Cntry.Aid.HzMon.Stt` | Netzüberwachung | nicht angegeben | RO | Inselnetzerkennung, Status der Frequenzüberwachung | `homie/sma-inverter2/parameters/gridguard-cntry-aid-hzmon-stt` |
| `Parameter.GridGuard.Cntry.AMaxOfs` | Netzüberwachung | A | RO | Auslöseschwelle Gleichstromüberwachung | `homie/sma-inverter2/parameters/gridguard-cntry-amaxofs` |
| `Parameter.GridGuard.Cntry.AMaxOfsTmms` | Netzüberwachung | ms | RO | Auslösezeit Gleichstromüberwachung | `homie/sma-inverter2/parameters/gridguard-cntry-amaxofstmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.ChgMax` | Netzüberwachung | Hz/s | RO | Frequenzüberwachung, Maximale Frequenzänderung pro Sekunde | `homie/sma-inverter2/parameters/gridguard-cntry-frqctl-chgmax` |
| `Parameter.GridGuard.Cntry.FrqCtl.ChgMaxTmms` | Netzüberwachung | ms | RO | Frequenzüberwachung, Maximale Frequenzänderung Auslösezeit | `homie/sma-inverter2/parameters/gridguard-cntry-frqctl-chgmaxtmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.hLim` | Netzüberwachung | Hz | RO | Frequenzüberwachung, untere Maximalschwelle | `homie/sma-inverter2/parameters/gridguard-cntry-frqctl-hlim` |
| `Parameter.GridGuard.Cntry.FrqCtl.hLimTmms` | Netzüberwachung | ms | RO | Frequenzüberwachung, untere Maximalschwelle Auslösezeit | `homie/sma-inverter2/parameters/gridguard-cntry-frqctl-hlimtmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.lLim` | Netzüberwachung | Hz | RO | Frequenzüberwachung, obere Minimalschwelle | `homie/sma-inverter2/parameters/gridguard-cntry-frqctl-llim` |
| `Parameter.GridGuard.Cntry.FrqCtl.lLimTmms` | Netzüberwachung | ms | RO | Frequenzüberwachung, obere Minimalschwelle Auslösezeit | `homie/sma-inverter2/parameters/gridguard-cntry-frqctl-llimtmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.Max` | Netzüberwachung | Hz | RO | Frequenzüberwachung, obere Maximalschwelle | `homie/sma-inverter2/parameters/gridguard-cntry-frqctl-max` |
| `Parameter.GridGuard.Cntry.FrqCtl.MaxTmms` | Netzüberwachung | ms | RO | Frequenzüberwachung, obere Maximalschwelle Auslösezeit | `homie/sma-inverter2/parameters/gridguard-cntry-frqctl-maxtmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.Min` | Netzüberwachung | Hz | RO | Frequenzüberwachung, untere Minimalschwelle | `homie/sma-inverter2/parameters/gridguard-cntry-frqctl-min` |
| `Parameter.GridGuard.Cntry.FrqCtl.MinTmms` | Netzüberwachung | ms | RO | Frequenzüberwachung, untere Minimalschwelle Auslösezeit | `homie/sma-inverter2/parameters/gridguard-cntry-frqctl-mintmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.ReconMax` | Netzüberwachung | Hz | RO | Maximale Zuschaltfrequenz | `homie/sma-inverter2/parameters/gridguard-cntry-frqctl-reconmax` |
| `Parameter.GridGuard.Cntry.FrqCtl.ReconMin` | Netzüberwachung | Hz | RO | Minimale Zuschaltfrequenz | `homie/sma-inverter2/parameters/gridguard-cntry-frqctl-reconmin` |
| `Parameter.GridGuard.Cntry.GriFltMonTms` | Netzüberwachung | s | RO | Zuschaltzeit nach Netzfehler | `homie/sma-inverter2/parameters/gridguard-cntry-grifltmontms` |
| `Parameter.GridGuard.Cntry.GriFltReConTms` | Netzüberwachung | s | RO | Schnellzuschaltzeit nach Kurzunterbrechung | `homie/sma-inverter2/parameters/gridguard-cntry-grifltrecontms` |
| `Parameter.GridGuard.Cntry.GriFltTms` | Netzüberwachung | s | RO | Maximale Dauer einer Kurzunterbrechung | `homie/sma-inverter2/parameters/gridguard-cntry-griflttms` |
| `Parameter.GridGuard.Cntry.GriStrTms` | Netzüberwachung | s | RO | Zuschaltzeit nach Neustart | `homie/sma-inverter2/parameters/gridguard-cntry-gristrtms` |
| `Parameter.GridGuard.Cntry.HzRtg` | Netzüberwachung | Hz | RO | Nennfrequenz | `homie/sma-inverter2/parameters/gridguard-cntry-hzrtg` |
| `Parameter.GridGuard.Cntry.LeakRisMin` | Netzüberwachung | Ohm | RO | Minimaler Isolationswiderstand | `homie/sma-inverter2/parameters/gridguard-cntry-leakrismin` |
| `Parameter.GridGuard.Cntry.PEOpnMon` | Netzüberwachung | nicht angegeben | RO | Überwachung Erdungsanschluss | `homie/sma-inverter2/parameters/gridguard-cntry-peopnmon` |
| `Parameter.GridGuard.Cntry.VolCtl.hhLimTmms` | Netzüberwachung | ms | RO | Spannungsüberwachung, mittlere Maximalschwelle Auslösezeit | `homie/sma-inverter2/parameters/gridguard-cntry-volctl-hhlimtmms` |
| `Parameter.GridGuard.Cntry.VolCtl.hLimTmms` | Netzüberwachung | ms | RO | Spannungsüberwachung, untere Maximalschwelle Auslösezeit | `homie/sma-inverter2/parameters/gridguard-cntry-volctl-hlimtmms` |
| `Parameter.GridGuard.Cntry.VolCtl.lLimTmms` | Netzüberwachung | ms | RO | Spannungsüberwachung, obere Minimalschwelle Auslösezeit | `homie/sma-inverter2/parameters/gridguard-cntry-volctl-llimtmms` |
| `Parameter.GridGuard.Cntry.VolCtl.llLimTmms` | Netzüberwachung | ms | RO | Spannungsüberwachung, mittlere Minimalschwelle Auslösezeit | `homie/sma-inverter2/parameters/gridguard-cntry-volctl-lllimtmms` |
| `Parameter.GridGuard.CntryBas` | Netzüberwachung | nicht angegeben | RO | Basierender Länderdatensatz | `homie/sma-inverter2/parameters/gridguard-cntrybas` |
| `Parameter.GridGuard.CntrySet` | Netzüberwachung | nicht angegeben | RO | Setze Länderdatensatz | `homie/sma-inverter2/parameters/gridguard-cntryset` |
| `Parameter.Inverter.CtlComCfg.VArCtlCom.FlbVArNom` | Anlagen- und Gerätesteuerung | % | RO | Externe Blindleistungsvorgabe, Rückfallwert | `homie/sma-inverter2/parameters/inverter-ctlcomcfg-varctlcom-flbvarnom` |
| `Parameter.Inverter.CtlComCfg.WCtlCom.CtlComMssMod` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Externe Wirkleistungsvorgabe, Rückfallverhalten | `homie/sma-inverter2/parameters/inverter-ctlcomcfg-wctlcom-ctlcommssmod` |
| `Parameter.Inverter.CtlComCfg.WCtlCom.TmsOut` | Anlagen- und Gerätesteuerung | s | RO | Externe Wirkleistungsvorgabe, Timeout | `homie/sma-inverter2/parameters/inverter-ctlcomcfg-wctlcom-tmsout` |
| `Parameter.Inverter.DGSModCfg.DGSMod` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Dynamische Netzstützung, Betriebsart | `homie/sma-inverter2/parameters/inverter-dgsmodcfg-dgsmod` |
| `Parameter.Inverter.OutPhs` | AC-Seite | nicht angegeben | RO | Phasenzuordnung | `homie/sma-inverter2/parameters/inverter-outphs` |
| `Parameter.Inverter.PlntCtl.VRef` | AC-Seite | V | RO | Netznennspannung | `homie/sma-inverter2/parameters/inverter-plntctl-vref` |
| `Parameter.Inverter.StopTms` | Gerät | s | RO | Abschaltverzögerung | `homie/sma-inverter2/parameters/inverter-stoptms` |
| `Parameter.Inverter.VArModCfg.VArCnstCfg.VArNom` | Anlagen- und Gerätesteuerung | % | RO | Manuelle Blindleistungsvorgabe bei Wirkleistungsabgabe | `homie/sma-inverter2/parameters/inverter-varmodcfg-varcnstcfg-varnom` |
| `Parameter.Inverter.VArModCfg.VArModOut` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Blindleistungsverfahren bei Wirkleistungsabgabe | `homie/sma-inverter2/parameters/inverter-varmodcfg-varmodout` |
| `Parameter.Inverter.WGraReconEna` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Sanftanlauf P nach Netzfehler | `homie/sma-inverter2/parameters/inverter-wgrareconena` |
| `Parameter.Inverter.WLim` | Gerät | W | RO | Bemessungswirkleistung WMaxOutRtg | `homie/sma-inverter2/parameters/inverter-wlim` |
| `Parameter.Inverter.WMax` | Gerät | W | RO | Nennwirkleistung WMaxOut | `homie/sma-inverter2/parameters/inverter-wmax` |
| `Parameter.Inverter.WMaxIn` | AC-Seite | W | RO | Nennwirkleistung WMaxIn | `homie/sma-inverter2/parameters/inverter-wmaxin` |
| `Parameter.Inverter.WModCfg.WCnstCfg.W` | Anlagen- und Gerätesteuerung | W | RO | Wirkleistungsbegrenzung in W | `homie/sma-inverter2/parameters/inverter-wmodcfg-wcnstcfg-w` |
| `Parameter.Inverter.WModCfg.WCnstCfg.WNom` | Anlagen- und Gerätesteuerung | % | RO | Wirkleistungsbegrenzung in % | `homie/sma-inverter2/parameters/inverter-wmodcfg-wcnstcfg-wnom` |
| `Parameter.Inverter.WModCfg.WMod` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Betriebsart Wirkleistungsvorgabe | `homie/sma-inverter2/parameters/inverter-wmodcfg-wmod` |
| `Parameter.Mb.TcpSrv.IsOn` | Externe Kommunikation | nicht angegeben | RO | Modbus TCP-Server eingeschaltet | `homie/sma-inverter2/parameters/mb-tcpsrv-ison` |
| `Parameter.Mb.TcpSrv.Port` | Externe Kommunikation | nicht angegeben | RO | Modbus TCP-Server-Port | `homie/sma-inverter2/parameters/mb-tcpsrv-port` |
| `Parameter.Mb.UntId` | Externe Kommunikation | nicht angegeben | RO | Modbus Unit ID | `homie/sma-inverter2/parameters/mb-untid` |
| `Parameter.Metering.EnMtrTyp` | Anlagenkommunikation | nicht angegeben | RO | Verwendeter Energiezähler | `homie/sma-inverter2/parameters/metering-enmtrtyp` |
| `Parameter.Metering.GridMs.TotkWhInOfs` | AC-Seite | kWh | RO | Offset der aufgenommenen Energie setzen | `homie/sma-inverter2/parameters/metering-gridms-totkwhinofs` |
| `Parameter.Metering.GridMs.TotkWhOutOfs` | AC-Seite | kWh | RO | Offset der eingespeisten Energie setzen | `homie/sma-inverter2/parameters/metering-gridms-totkwhoutofs` |
| `Parameter.Metering.MsSpdwr.SerNumEN` | Anlagenkommunikation | nicht angegeben | RO | Seriennummer des Zählers an Speedwire; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Metering.TotFeedTmhSet` | AC-Seite | h | RO | Setze Gesamte Einspeisezeit am Netzanschlusspunkt | `homie/sma-inverter2/parameters/metering-totfeedtmhset` |
| `Parameter.Metering.TotkWhOutSet` | AC-Seite | kWh | RO | Setze Gesamtertrag | `homie/sma-inverter2/parameters/metering-totkwhoutset` |
| `Parameter.Metering.TotOpTmhSet` | AC-Seite | h | RO | Setze Gesamte Betriebszeit am Netzanschlusspunkt | `homie/sma-inverter2/parameters/metering-totoptmhset` |
| `Parameter.MltFncSw.BatCha.MinOnPwr` | Gerät | W | RO | Mindesteinschaltleistung des MFR Batteriebank | `homie/sma-inverter2/parameters/mltfncsw-batcha-minonpwr` |
| `Parameter.MltFncSw.BatCha.MinReconTmm` | Gerät | min | RO | Mindestpause vor erneutem Einschalten des MFR Batteriebank | `homie/sma-inverter2/parameters/mltfncsw-batcha-minrecontmm` |
| `Parameter.MltFncSw.ComCtl.Stt` | Gerät | nicht angegeben | RO | Status des MFR bei Steuerung über Kommunikation | `homie/sma-inverter2/parameters/mltfncsw-comctl-stt` |
| `Parameter.MltFncSw.OpMode` | Gerät | nicht angegeben | RO | Betriebsart des Multifunktionsrelais | `homie/sma-inverter2/parameters/mltfncsw-opmode` |
| `Parameter.MltFncSw.SelfCsmp.MinOnPwr` | Gerät | W | RO | Mindesteinschaltleistung des MFR Eigenverbrauch | `homie/sma-inverter2/parameters/mltfncsw-selfcsmp-minonpwr` |
| `Parameter.MltFncSw.SelfCsmp.MinOnPwrTmm` | Gerät | min | RO | Mindestzeit für Einschaltleistung MFR Eigenverbrauch | `homie/sma-inverter2/parameters/mltfncsw-selfcsmp-minonpwrtmm` |
| `Parameter.MltFncSw.SelfCsmp.MinOnTmm` | Gerät | min | RO | Mindesteinschaltzeit des MFR Eigenverbrauch | `homie/sma-inverter2/parameters/mltfncsw-selfcsmp-minontmm` |
| `Parameter.Nameplate.Bat.Detl.Typ` | Typenschild | nicht angegeben | RO | Typ des Batteriemanagementsystems | `homie/sma-inverter2/parameters/nameplate-bat-detl-typ` |
| `Parameter.Nameplate.Bat.Detl.Vendor` | Typenschild | nicht angegeben | RO | Hersteller | `homie/sma-inverter2/parameters/nameplate-bat-detl-vendor` |
| `Parameter.Nameplate.Bat.ProdTm` | Typenschild | nicht angegeben | RO | Batterie-Herstelldatum | `homie/sma-inverter2/parameters/nameplate-bat-prodtm` |
| `Parameter.Nameplate.Bat.Vendor[0]` | Typenschild | nicht angegeben | RO | Batterie-Hersteller | `homie/sma-inverter2/parameters/nameplate-bat-vendor-0` |
| `Parameter.Nameplate.Bat.Vendor[1]` | Typenschild | nicht angegeben | RO | Batterie-Hersteller | `homie/sma-inverter2/parameters/nameplate-bat-vendor-1` |
| `Parameter.Nameplate.Bat.Vendor[2]` | Typenschild | nicht angegeben | RO | Batterie-Hersteller | `homie/sma-inverter2/parameters/nameplate-bat-vendor-2` |
| `Parameter.Nameplate.CmpBIM.HwVer` | Gerätekomponenten | nicht angegeben | RO | Hardware-Version des Battery Interface Modules | `homie/sma-inverter2/parameters/nameplate-cmpbim-hwver` |
| `Parameter.Nameplate.CmpBIM.SerNum` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Battery Interface Modules; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBIM.SwRev` | Gerätekomponenten | nicht angegeben | RO | SW-Version des Battery Interface Modules | `homie/sma-inverter2/parameters/nameplate-cmpbim-swrev` |
| `Parameter.Nameplate.CmpBMS.HwRevStr` | Gerätekomponenten | nicht angegeben | RO | Hardware-Version des Batteriemanagementsystems | `homie/sma-inverter2/parameters/nameplate-cmpbms-hwrevstr` |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatARck1[0]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss A; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatARck1[1]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss A; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatARck1[2]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss A; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatARck1[3]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss A; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatARck1[4]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss A; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatARck1[5]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss A; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatARck1[6]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss A; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatARck1[7]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss A; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatBRck1[0]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss B; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatBRck1[1]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss B; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatBRck1[2]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss B; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatBRck1[3]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss B; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatBRck1[4]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss B; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatBRck1[5]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss B; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatBRck1[6]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss B; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatBRck1[7]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss B; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatCRck1[0]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss C; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.MdulSerNumBatCRck1[1]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemoduls (Anschluss C; Rack 1); private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.SerNumTxt[0]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemanagementsystems; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.SerNumTxt[1]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemanagementsystems; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.SerNumTxt[2]` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Batteriemanagementsystems; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBMS.SusyId[0]` | Gerätekomponenten | nicht angegeben | RO | SUSyID des Batteriemanagementsystems | `homie/sma-inverter2/parameters/nameplate-cmpbms-susyid-0` |
| `Parameter.Nameplate.CmpBMS.SusyId[1]` | Gerätekomponenten | nicht angegeben | RO | SUSyID des Batteriemanagementsystems | `homie/sma-inverter2/parameters/nameplate-cmpbms-susyid-1` |
| `Parameter.Nameplate.CmpBMS.SusyId[2]` | Gerätekomponenten | nicht angegeben | RO | SUSyID des Batteriemanagementsystems | `homie/sma-inverter2/parameters/nameplate-cmpbms-susyid-2` |
| `Parameter.Nameplate.CmpBMS.SwRev[0]` | Gerätekomponenten | nicht angegeben | RO | Firmware-Version des Batteriemanagementsystems | `homie/sma-inverter2/parameters/nameplate-cmpbms-swrev-0` |
| `Parameter.Nameplate.CmpBMS.SwRev[1]` | Gerätekomponenten | nicht angegeben | RO | Firmware-Version des Batteriemanagementsystems | `homie/sma-inverter2/parameters/nameplate-cmpbms-swrev-1` |
| `Parameter.Nameplate.CmpBMS.Typ[0]` | Gerätekomponenten | nicht angegeben | RO | Typ des Batteriemanagementsystems | `homie/sma-inverter2/parameters/nameplate-cmpbms-typ-0` |
| `Parameter.Nameplate.CmpBMS.Typ[1]` | Gerätekomponenten | nicht angegeben | RO | Typ des Batteriemanagementsystems | `homie/sma-inverter2/parameters/nameplate-cmpbms-typ-1` |
| `Parameter.Nameplate.CmpBMS.Typ[2]` | Gerätekomponenten | nicht angegeben | RO | Typ des Batteriemanagementsystems | `homie/sma-inverter2/parameters/nameplate-cmpbms-typ-2` |
| `Parameter.Nameplate.CmpBUC.HwVer` | Gerätekomponenten | nicht angegeben | RO | Hardware-Version des Backup Controllers | `homie/sma-inverter2/parameters/nameplate-cmpbuc-hwver` |
| `Parameter.Nameplate.CmpBUC.SerNum` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Backup Controllers; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpBUC.SwRev` | Gerätekomponenten | nicht angegeben | RO | SW-Version des Backup Controllers | `homie/sma-inverter2/parameters/nameplate-cmpbuc-swrev` |
| `Parameter.Nameplate.CmpCom.HwRev` | Gerätekomponenten | nicht angegeben | RO | Hardware-Version der Kommunikationsbaugruppe | `homie/sma-inverter2/parameters/nameplate-cmpcom-hwrev` |
| `Parameter.Nameplate.CmpCom.SerNum` | Gerätekomponenten | nicht angegeben | RO | Seriennummer der Kommunikationsbaugruppe; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpCom.SusyId` | Gerätekomponenten | nicht angegeben | RO | SUSyID der Kommunikationsbaugruppe | `homie/sma-inverter2/parameters/nameplate-cmpcom-susyid` |
| `Parameter.Nameplate.CmpCom.SwRev` | Gerätekomponenten | nicht angegeben | RO | Firmware-Version der Kommunikationsbaugruppe | `homie/sma-inverter2/parameters/nameplate-cmpcom-swrev` |
| `Parameter.Nameplate.CmpMain.HwRev` | Gerätekomponenten | nicht angegeben | RO | Hardware-Version des Hauptprozessors | `homie/sma-inverter2/parameters/nameplate-cmpmain-hwrev` |
| `Parameter.Nameplate.CmpMain.Rev` | Gerätekomponenten | nicht angegeben | RO | Umbaustand des Hauptprozessors | `homie/sma-inverter2/parameters/nameplate-cmpmain-rev` |
| `Parameter.Nameplate.CmpMain.SerNum` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Hauptprozessors; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpMain.SusyId` | Gerätekomponenten | nicht angegeben | RO | SUSyID des Hauptprozessors | `homie/sma-inverter2/parameters/nameplate-cmpmain-susyid` |
| `Parameter.Nameplate.CmpMain.SwRev` | Gerätekomponenten | nicht angegeben | RO | Firmware-Version des Hauptprozessors | `homie/sma-inverter2/parameters/nameplate-cmpmain-swrev` |
| `Parameter.Nameplate.CmpMdul.Typ` | Gerätekomponenten | nicht angegeben | RO | Typ des Moduls im Modulsteckplatz | `homie/sma-inverter2/parameters/nameplate-cmpmdul-typ` |
| `Parameter.Nameplate.CmpMdul2.Typ` | Gerätekomponenten | nicht angegeben | RO | Typ des Moduls im Modulsteckplatz | `homie/sma-inverter2/parameters/nameplate-cmpmdul2-typ` |
| `Parameter.Nameplate.CmpOS.SwRev` | Gerätekomponenten | nicht angegeben | RO | Firmware-Version des Betriebssystems | `homie/sma-inverter2/parameters/nameplate-cmpos-swrev` |
| `Parameter.Nameplate.ComRev` | Typenschild | nicht angegeben | RO | Kommunikationsversion | `homie/sma-inverter2/parameters/nameplate-comrev` |
| `Parameter.Nameplate.Location` | Typenschild | nicht angegeben | RO | Gerätename; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.MacId` | Typenschild | nicht angegeben | RO | MAC-Adresse; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.MainModel` | Typenschild | nicht angegeben | RO | Geräteklasse | `homie/sma-inverter2/parameters/nameplate-mainmodel` |
| `Parameter.Nameplate.Model` | Typenschild | nicht angegeben | RO | Gerätetyp | `homie/sma-inverter2/parameters/nameplate-model` |
| `Parameter.Nameplate.PkgRev` | Typenschild | nicht angegeben | RO | Firmware-Version | `homie/sma-inverter2/parameters/nameplate-pkgrev` |
| `Parameter.Nameplate.SerNum` | Typenschild | nicht angegeben | RO | Seriennummer; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.WlMacId` | Typenschild | nicht angegeben | RO | WLAN-MAC-Adresse; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Operation.LodFnc` | Gerät | nicht angegeben | RO | Parameter laden | `homie/sma-inverter2/parameters/operation-lodfnc` |
| `Parameter.Operation.OpMod` | Gerät | nicht angegeben | RO | Allgemeine Betriebsart | `homie/sma-inverter2/parameters/operation-opmod` |
| `Parameter.PCC.WMax` | Anlagen- und Gerätesteuerung | W | RO | Eingestellte Wirkleistungsgrenze am Netzanschlusspunkt | `homie/sma-inverter2/parameters/pcc-wmax` |
| `Parameter.PCC.WMaxMod` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Betriebsart der Wirkleistungsbegrenzung am Netzanschlusspunkt | `homie/sma-inverter2/parameters/pcc-wmaxmod` |
| `Parameter.PCC.WMaxNom` | Anlagen- und Gerätesteuerung | % | RO | Eingestellte Wirkleistungsgrenze am Netzanschlusspunkt | `homie/sma-inverter2/parameters/pcc-wmaxnom` |
| `Parameter.Plnt.DcWRtg` | DC-Seite | W | RO | Anlagen-Nennleistung | `homie/sma-inverter2/parameters/plnt-dcwrtg` |
| `Parameter.SelfCsmp.BatChaSttMin` | Gerät | % | RO | Untere Entladegrenze bei Eigenverbrauchserhöhung | `homie/sma-inverter2/parameters/selfcsmp-batchasttmin` |
| `Parameter.Spdwr.AutoCfgIsOn` | Anlagenkommunikation | nicht angegeben | RO | Automatische Speedwire-Konfiguration eingeschaltet | `homie/sma-inverter2/parameters/spdwr-autocfgison` |
| `Parameter.Spdwr.Cry` | Anlagenkommunikation | nicht angegeben | RO | Verschlüsselung | `homie/sma-inverter2/parameters/spdwr-cry` |
| `Parameter.Spdwr.DnsSrvIp` | Anlagenkommunikation | nicht angegeben | RO | Speedwire-IP-Adresse DNS-Server; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Spdwr.GwIp` | Anlagenkommunikation | nicht angegeben | RO | Speedwire-IP-Adresse Gateway; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Spdwr.Ip` | Anlagenkommunikation | nicht angegeben | RO | Speedwire-IP-Adresse; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Spdwr.SnetMsk` | Anlagenkommunikation | nicht angegeben | RO | Speedwire-Subnetzmaske; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.SwCmp.CmpMainBlt.SwRev` | Gerät | nicht angegeben | RO | Version des HP-Bootloaders | `homie/sma-inverter2/parameters/swcmp-cmpmainblt-swrev` |
| `Parameter.Upd.AutoUpdIsOn` | Gerät | nicht angegeben | RO | Automatische Updates eingeschaltet | `homie/sma-inverter2/parameters/upd-autoupdison` |
| `Parameter.WebConn.SwRev` | Externe Kommunikation | nicht angegeben | RO | Version des Webconnect | `homie/sma-inverter2/parameters/webconn-swrev` |
| `Parameter.Wl.IsOn` | Anlagenkommunikation | nicht angegeben | RO | WLAN ist eingeschaltet | `homie/sma-inverter2/parameters/wl-ison` |
| `Parameter.Wl.SoftAcsIsOn` | Anlagenkommunikation | nicht angegeben | RO | Soft-Access-Point ist eingeschaltet | `homie/sma-inverter2/parameters/wl-softacsison` |

#### Portalparameter: SB4.0-1AV-41

| Portal-Kanal | Gruppe | Export-Unit | Export-Zugriff | Kurzbeschreibung | MQTT-Topic (lesender Kandidat) |
| --- | --- | --- | --- | --- | --- |
| `Parameter.Acs.PwdIstl` | Benutzerrechte | nicht angegeben | RO | Installateurpasswort setzen; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Acs.PwdUsr` | Benutzerrechte | nicht angegeben | RO | Benutzerpasswort setzen; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Coolsys.FanTst` | Gerät | nicht angegeben | RO | Lüftertest; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.DcCfg.MPPShdw.CycTms` | DC-Seite | s | RO | Zeitintervall SMA ShadeFix | `homie/sma-inverter3/parameters/dccfg-mppshdw-cyctms` |
| `Parameter.DcCfg.MPPShdw.IsOn` | DC-Seite | nicht angegeben | RO | SMA ShadeFix | `homie/sma-inverter3/parameters/dccfg-mppshdw-ison` |
| `Parameter.DtTm.NtpSrv` | Gerät | nicht angegeben | RO | NTP-Server; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.DtTm.TmSynIsOn` | Gerät | nicht angegeben | RO | Automatische Zeitsynchronisation | `homie/sma-inverter3/parameters/dttm-tmsynison` |
| `Parameter.DtTm.TmZn` | Gerät | nicht angegeben | RO | Zeitzone | `homie/sma-inverter3/parameters/dttm-tmzn` |
| `Parameter.Eth.Proxy.IsOn` | Externe Kommunikation | nicht angegeben | RO | Ethernet Proxy eingeschaltet | `homie/sma-inverter3/parameters/eth-proxy-ison` |
| `Parameter.Eth.Proxy.Login` | Externe Kommunikation | nicht angegeben | RO | Ethernet Proxy-Server Login; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Eth.Proxy.Port` | Externe Kommunikation | nicht angegeben | RO | Ethernet Proxy-Server Port | `homie/sma-inverter3/parameters/eth-proxy-port` |
| `Parameter.Eth.Proxy.Srv` | Externe Kommunikation | nicht angegeben | RO | Ethernet Proxy-Server Adresse; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.GridGuard.Cntry` | Netzüberwachung | nicht angegeben | RO | Eingestellter Länderdatensatz | `homie/sma-inverter3/parameters/gridguard-cntry` |
| `Parameter.GridGuard.Cntry.Aid.HzMon.HzMonTmms` | Netzüberwachung | ms | RO | Inselnetzerkennung, Auslösezeit der Frequenzüberwachung | `homie/sma-inverter3/parameters/gridguard-cntry-aid-hzmon-hzmontmms` |
| `Parameter.GridGuard.Cntry.Aid.HzMon.Stt` | Netzüberwachung | nicht angegeben | RO | Inselnetzerkennung, Status der Frequenzüberwachung | `homie/sma-inverter3/parameters/gridguard-cntry-aid-hzmon-stt` |
| `Parameter.GridGuard.Cntry.AMaxOfs` | Netzüberwachung | A | RO | Auslöseschwelle Gleichstromüberwachung | `homie/sma-inverter3/parameters/gridguard-cntry-amaxofs` |
| `Parameter.GridGuard.Cntry.AMaxOfsTmms` | Netzüberwachung | ms | RO | Auslösezeit Gleichstromüberwachung | `homie/sma-inverter3/parameters/gridguard-cntry-amaxofstmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.ChgMax` | Netzüberwachung | Hz/s | RO | Frequenzüberwachung, Maximale Frequenzänderung pro Sekunde | `homie/sma-inverter3/parameters/gridguard-cntry-frqctl-chgmax` |
| `Parameter.GridGuard.Cntry.FrqCtl.ChgMaxTmms` | Netzüberwachung | ms | RO | Frequenzüberwachung, Maximale Frequenzänderung Auslösezeit | `homie/sma-inverter3/parameters/gridguard-cntry-frqctl-chgmaxtmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.hLim` | Netzüberwachung | Hz | RO | Frequenzüberwachung, untere Maximalschwelle | `homie/sma-inverter3/parameters/gridguard-cntry-frqctl-hlim` |
| `Parameter.GridGuard.Cntry.FrqCtl.hLimTmms` | Netzüberwachung | ms | RO | Frequenzüberwachung, untere Maximalschwelle Auslösezeit | `homie/sma-inverter3/parameters/gridguard-cntry-frqctl-hlimtmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.lLim` | Netzüberwachung | Hz | RO | Frequenzüberwachung, obere Minimalschwelle | `homie/sma-inverter3/parameters/gridguard-cntry-frqctl-llim` |
| `Parameter.GridGuard.Cntry.FrqCtl.lLimTmms` | Netzüberwachung | ms | RO | Frequenzüberwachung, obere Minimalschwelle Auslösezeit | `homie/sma-inverter3/parameters/gridguard-cntry-frqctl-llimtmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.Max` | Netzüberwachung | Hz | RO | Frequenzüberwachung, obere Maximalschwelle | `homie/sma-inverter3/parameters/gridguard-cntry-frqctl-max` |
| `Parameter.GridGuard.Cntry.FrqCtl.MaxTmms` | Netzüberwachung | ms | RO | Frequenzüberwachung, obere Maximalschwelle Auslösezeit | `homie/sma-inverter3/parameters/gridguard-cntry-frqctl-maxtmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.Min` | Netzüberwachung | Hz | RO | Frequenzüberwachung, untere Minimalschwelle | `homie/sma-inverter3/parameters/gridguard-cntry-frqctl-min` |
| `Parameter.GridGuard.Cntry.FrqCtl.MinTmms` | Netzüberwachung | ms | RO | Frequenzüberwachung, untere Minimalschwelle Auslösezeit | `homie/sma-inverter3/parameters/gridguard-cntry-frqctl-mintmms` |
| `Parameter.GridGuard.Cntry.FrqCtl.ReconMax` | Netzüberwachung | Hz | RO | Maximale Zuschaltfrequenz | `homie/sma-inverter3/parameters/gridguard-cntry-frqctl-reconmax` |
| `Parameter.GridGuard.Cntry.FrqCtl.ReconMin` | Netzüberwachung | Hz | RO | Minimale Zuschaltfrequenz | `homie/sma-inverter3/parameters/gridguard-cntry-frqctl-reconmin` |
| `Parameter.GridGuard.Cntry.GriFltMonTms` | Netzüberwachung | s | RO | Zuschaltzeit nach Netzfehler | `homie/sma-inverter3/parameters/gridguard-cntry-grifltmontms` |
| `Parameter.GridGuard.Cntry.GriFltReConTms` | Netzüberwachung | s | RO | Schnellzuschaltzeit nach Kurzunterbrechung | `homie/sma-inverter3/parameters/gridguard-cntry-grifltrecontms` |
| `Parameter.GridGuard.Cntry.GriFltTms` | Netzüberwachung | s | RO | Maximale Dauer einer Kurzunterbrechung | `homie/sma-inverter3/parameters/gridguard-cntry-griflttms` |
| `Parameter.GridGuard.Cntry.GriStrTms` | Netzüberwachung | s | RO | Zuschaltzeit nach Neustart | `homie/sma-inverter3/parameters/gridguard-cntry-gristrtms` |
| `Parameter.GridGuard.Cntry.HzRtg` | Netzüberwachung | Hz | RO | Nennfrequenz | `homie/sma-inverter3/parameters/gridguard-cntry-hzrtg` |
| `Parameter.GridGuard.Cntry.LeakRisMin` | Netzüberwachung | Ohm | RO | Minimaler Isolationswiderstand | `homie/sma-inverter3/parameters/gridguard-cntry-leakrismin` |
| `Parameter.GridGuard.Cntry.PEOpnMon` | Netzüberwachung | nicht angegeben | RO | Überwachung Erdungsanschluss | `homie/sma-inverter3/parameters/gridguard-cntry-peopnmon` |
| `Parameter.GridGuard.Cntry.VolCtl.hhLimTmms` | Netzüberwachung | ms | RO | Spannungsüberwachung, mittlere Maximalschwelle Auslösezeit | `homie/sma-inverter3/parameters/gridguard-cntry-volctl-hhlimtmms` |
| `Parameter.GridGuard.Cntry.VolCtl.hLimTmms` | Netzüberwachung | ms | RO | Spannungsüberwachung, untere Maximalschwelle Auslösezeit | `homie/sma-inverter3/parameters/gridguard-cntry-volctl-hlimtmms` |
| `Parameter.GridGuard.Cntry.VolCtl.lLimTmms` | Netzüberwachung | ms | RO | Spannungsüberwachung, obere Minimalschwelle Auslösezeit | `homie/sma-inverter3/parameters/gridguard-cntry-volctl-llimtmms` |
| `Parameter.GridGuard.Cntry.VolCtl.llLimTmms` | Netzüberwachung | ms | RO | Spannungsüberwachung, mittlere Minimalschwelle Auslösezeit | `homie/sma-inverter3/parameters/gridguard-cntry-volctl-lllimtmms` |
| `Parameter.GridGuard.Cntry.VRtg` | Netzüberwachung | V | RO | Netz-Nennspannung | `homie/sma-inverter3/parameters/gridguard-cntry-vrtg` |
| `Parameter.GridGuard.CntryBas` | Netzüberwachung | nicht angegeben | RO | Basierender Länderdatensatz | `homie/sma-inverter3/parameters/gridguard-cntrybas` |
| `Parameter.GridGuard.CntrySet` | Netzüberwachung | nicht angegeben | RO | Setze Länderdatensatz | `homie/sma-inverter3/parameters/gridguard-cntryset` |
| `Parameter.Inverter.CtlComCfg.VArCtlCom.FlbVArNom` | Anlagen- und Gerätesteuerung | % | RO | Externe Blindleistungsvorgabe, Rückfallwert | `homie/sma-inverter3/parameters/inverter-ctlcomcfg-varctlcom-flbvarnom` |
| `Parameter.Inverter.CtlComCfg.WCtlCom.CtlComMssMod` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Externe Wirkleistungsvorgabe, Rückfallverhalten | `homie/sma-inverter3/parameters/inverter-ctlcomcfg-wctlcom-ctlcommssmod` |
| `Parameter.Inverter.CtlComCfg.WCtlCom.TmsOut` | Anlagen- und Gerätesteuerung | s | RO | Externe Wirkleistungsvorgabe, Timeout | `homie/sma-inverter3/parameters/inverter-ctlcomcfg-wctlcom-tmsout` |
| `Parameter.Inverter.DGSModCfg.DGSMod` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Dynamische Netzstützung, Betriebsart | `homie/sma-inverter3/parameters/inverter-dgsmodcfg-dgsmod` |
| `Parameter.Inverter.FltAMod` | Gerät | nicht angegeben | RO | RCD Anpassung | `homie/sma-inverter3/parameters/inverter-fltamod` |
| `Parameter.Inverter.OutPhs` | AC-Seite | nicht angegeben | RO | Phasenzuordnung | `homie/sma-inverter3/parameters/inverter-outphs` |
| `Parameter.Inverter.PlntCtl.VRef` | AC-Seite | V | RO | Netznennspannung | `homie/sma-inverter3/parameters/inverter-plntctl-vref` |
| `Parameter.Inverter.StopTms` | Gerät | s | RO | Abschaltverzögerung | `homie/sma-inverter3/parameters/inverter-stoptms` |
| `Parameter.Inverter.VArModCfg.VArCnstCfg.VArNom` | Anlagen- und Gerätesteuerung | % | RO | Manuelle Blindleistungsvorgabe bei Wirkleistungsabgabe | `homie/sma-inverter3/parameters/inverter-varmodcfg-varcnstcfg-varnom` |
| `Parameter.Inverter.VArModCfg.VArModOut` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Blindleistungsverfahren bei Wirkleistungsabgabe | `homie/sma-inverter3/parameters/inverter-varmodcfg-varmodout` |
| `Parameter.Inverter.WGraReconEna` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Sanftanlauf P nach Netzfehler | `homie/sma-inverter3/parameters/inverter-wgrareconena` |
| `Parameter.Inverter.WLim` | Gerät | W | RO | Bemessungswirkleistung WMaxOutRtg | `homie/sma-inverter3/parameters/inverter-wlim` |
| `Parameter.Inverter.WMax` | Gerät | W | RO | Nennwirkleistung WMaxOut | `homie/sma-inverter3/parameters/inverter-wmax` |
| `Parameter.Inverter.WMaxIn` | AC-Seite | W | RO | Nennwirkleistung WMaxIn | `homie/sma-inverter3/parameters/inverter-wmaxin` |
| `Parameter.Inverter.WModCfg.WCnstCfg.W` | Anlagen- und Gerätesteuerung | W | RO | Wirkleistungsbegrenzung in W | `homie/sma-inverter3/parameters/inverter-wmodcfg-wcnstcfg-w` |
| `Parameter.Inverter.WModCfg.WCnstCfg.WNom` | Anlagen- und Gerätesteuerung | % | RO | Wirkleistungsbegrenzung in % | `homie/sma-inverter3/parameters/inverter-wmodcfg-wcnstcfg-wnom` |
| `Parameter.Inverter.WModCfg.WMod` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Betriebsart Wirkleistungsvorgabe | `homie/sma-inverter3/parameters/inverter-wmodcfg-wmod` |
| `Parameter.Mb.TcpSrv.IsOn` | Externe Kommunikation | nicht angegeben | RO | Modbus TCP-Server eingeschaltet | `homie/sma-inverter3/parameters/mb-tcpsrv-ison` |
| `Parameter.Mb.TcpSrv.Port` | Externe Kommunikation | nicht angegeben | RO | Modbus TCP-Server-Port | `homie/sma-inverter3/parameters/mb-tcpsrv-port` |
| `Parameter.Mb.UntId` | Externe Kommunikation | nicht angegeben | RO | Modbus Unit ID | `homie/sma-inverter3/parameters/mb-untid` |
| `Parameter.Metering.EnMtrTyp` | Anlagenkommunikation | nicht angegeben | RO | Verwendeter Energiezähler | `homie/sma-inverter3/parameters/metering-enmtrtyp` |
| `Parameter.Metering.GridMs.TotkWhInOfs` | AC-Seite | kWh | RO | Offset der aufgenommenen Energie setzen | `homie/sma-inverter3/parameters/metering-gridms-totkwhinofs` |
| `Parameter.Metering.GridMs.TotkWhOutOfs` | AC-Seite | kWh | RO | Offset der eingespeisten Energie setzen | `homie/sma-inverter3/parameters/metering-gridms-totkwhoutofs` |
| `Parameter.Metering.MsSpdwr.SerNumEN` | Anlagenkommunikation | nicht angegeben | RO | Seriennummer des Zählers an Speedwire; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Metering.TotFeedTmhSet` | AC-Seite | h | RO | Setze Gesamte Einspeisezeit am Netzanschlusspunkt | `homie/sma-inverter3/parameters/metering-totfeedtmhset` |
| `Parameter.Metering.TotkWhOutSet` | AC-Seite | kWh | RO | Setze Gesamtertrag | `homie/sma-inverter3/parameters/metering-totkwhoutset` |
| `Parameter.Metering.TotOpTmhSet` | AC-Seite | h | RO | Setze Gesamte Betriebszeit am Netzanschlusspunkt | `homie/sma-inverter3/parameters/metering-totoptmhset` |
| `Parameter.Nameplate.CmpCom.HwRev` | Gerätekomponenten | nicht angegeben | RO | Hardware-Version der Kommunikationsbaugruppe | `homie/sma-inverter3/parameters/nameplate-cmpcom-hwrev` |
| `Parameter.Nameplate.CmpCom.SerNum` | Gerätekomponenten | nicht angegeben | RO | Seriennummer der Kommunikationsbaugruppe; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpCom.SusyId` | Gerätekomponenten | nicht angegeben | RO | SUSyID der Kommunikationsbaugruppe | `homie/sma-inverter3/parameters/nameplate-cmpcom-susyid` |
| `Parameter.Nameplate.CmpCom.SwRev` | Gerätekomponenten | nicht angegeben | RO | Firmware-Version der Kommunikationsbaugruppe | `homie/sma-inverter3/parameters/nameplate-cmpcom-swrev` |
| `Parameter.Nameplate.CmpMain.Rev` | Gerätekomponenten | nicht angegeben | RO | Umbaustand des Hauptprozessors | `homie/sma-inverter3/parameters/nameplate-cmpmain-rev` |
| `Parameter.Nameplate.CmpMain.SerNum` | Gerätekomponenten | nicht angegeben | RO | Seriennummer des Hauptprozessors; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.CmpMain.SusyId` | Gerätekomponenten | nicht angegeben | RO | SUSyID des Hauptprozessors | `homie/sma-inverter3/parameters/nameplate-cmpmain-susyid` |
| `Parameter.Nameplate.CmpMain.SwRev` | Gerätekomponenten | nicht angegeben | RO | Firmware-Version des Hauptprozessors | `homie/sma-inverter3/parameters/nameplate-cmpmain-swrev` |
| `Parameter.Nameplate.CmpOS.SwRev` | Gerätekomponenten | nicht angegeben | RO | Firmware-Version des Betriebssystems | `homie/sma-inverter3/parameters/nameplate-cmpos-swrev` |
| `Parameter.Nameplate.ComRev` | Typenschild | nicht angegeben | RO | Kommunikationsversion | `homie/sma-inverter3/parameters/nameplate-comrev` |
| `Parameter.Nameplate.Location` | Typenschild | nicht angegeben | RO | Gerätename; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.MacId` | Typenschild | nicht angegeben | RO | MAC-Adresse; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.MainModel` | Typenschild | nicht angegeben | RO | Geräteklasse | `homie/sma-inverter3/parameters/nameplate-mainmodel` |
| `Parameter.Nameplate.Model` | Typenschild | nicht angegeben | RO | Gerätetyp | `homie/sma-inverter3/parameters/nameplate-model` |
| `Parameter.Nameplate.PkgRev` | Typenschild | nicht angegeben | RO | Firmware-Version | `homie/sma-inverter3/parameters/nameplate-pkgrev` |
| `Parameter.Nameplate.SerNum` | Typenschild | nicht angegeben | RO | Seriennummer; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.WlMacId` | Typenschild | nicht angegeben | RO | WLAN-MAC-Adresse; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Operation.BckOpMod` | Gerät | nicht angegeben | RO | Betriebsart des Backup-Modus | `homie/sma-inverter3/parameters/operation-bckopmod` |
| `Parameter.Operation.LodFnc` | Gerät | nicht angegeben | RO | Parameter laden | `homie/sma-inverter3/parameters/operation-lodfnc` |
| `Parameter.Operation.OpMod` | Gerät | nicht angegeben | RO | Allgemeine Betriebsart | `homie/sma-inverter3/parameters/operation-opmod` |
| `Parameter.PCC.FlbInv.WMax` | Anlagen- und Gerätesteuerung | W | RO | Rückfallwert Wirkleistungsbegrenzung, Regelung am Netzanschlusspunkt | `homie/sma-inverter3/parameters/pcc-flbinv-wmax` |
| `Parameter.PCC.FlbInv.WMaxNom` | Anlagen- und Gerätesteuerung | % | RO | Rückfallwert Wirkleistungsbegrenzung in Prozent, Regelung am Netzanschlusspunkt | `homie/sma-inverter3/parameters/pcc-flbinv-wmaxnom` |
| `Parameter.PCC.WMax` | Anlagen- und Gerätesteuerung | W | RO | Eingestellte Wirkleistungsgrenze am Netzanschlusspunkt | `homie/sma-inverter3/parameters/pcc-wmax` |
| `Parameter.PCC.WMaxMod` | Anlagen- und Gerätesteuerung | nicht angegeben | RO | Betriebsart der Wirkleistungsbegrenzung am Netzanschlusspunkt | `homie/sma-inverter3/parameters/pcc-wmaxmod` |
| `Parameter.PCC.WMaxNom` | Anlagen- und Gerätesteuerung | % | RO | Eingestellte Wirkleistungsgrenze am Netzanschlusspunkt | `homie/sma-inverter3/parameters/pcc-wmaxnom` |
| `Parameter.Plnt.DcWRtg` | DC-Seite | W | RO | Anlagen-Nennleistung | `homie/sma-inverter3/parameters/plnt-dcwrtg` |
| `Parameter.RS485.RS485Mod` | Anlagenkommunikation | nicht angegeben | RO | Protokoll RS485-Schnittstelle | `homie/sma-inverter3/parameters/rs485-rs485mod` |
| `Parameter.Spdwr.AutoCfgIsOn` | Anlagenkommunikation | nicht angegeben | RO | Automatische Speedwire-Konfiguration eingeschaltet | `homie/sma-inverter3/parameters/spdwr-autocfgison` |
| `Parameter.Spdwr.Cry` | Anlagenkommunikation | nicht angegeben | RO | Verschlüsselung | `homie/sma-inverter3/parameters/spdwr-cry` |
| `Parameter.Spdwr.DnsSrvIp` | Anlagenkommunikation | nicht angegeben | RO | Speedwire-IP-Adresse DNS-Server; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Spdwr.GwIp` | Anlagenkommunikation | nicht angegeben | RO | Speedwire-IP-Adresse Gateway; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Spdwr.Ip` | Anlagenkommunikation | nicht angegeben | RO | Speedwire-IP-Adresse; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Spdwr.SnetMsk` | Anlagenkommunikation | nicht angegeben | RO | Speedwire-Subnetzmaske; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.SwCmp.CmpMainBlt.SwRev` | Gerät | nicht angegeben | RO | Version des HP-Bootloaders | `homie/sma-inverter3/parameters/swcmp-cmpmainblt-swrev` |
| `Parameter.Upd.AutoUpdIsOn` | Gerät | nicht angegeben | RO | Automatische Updates eingeschaltet | `homie/sma-inverter3/parameters/upd-autoupdison` |
| `Parameter.WebConn.SwRev` | Externe Kommunikation | nicht angegeben | RO | Version des Webconnect | `homie/sma-inverter3/parameters/webconn-swrev` |
| `Parameter.Wl.IsOn` | Anlagenkommunikation | nicht angegeben | RO | WLAN ist eingeschaltet | `homie/sma-inverter3/parameters/wl-ison` |
| `Parameter.Wl.SoftAcsIsOn` | Anlagenkommunikation | nicht angegeben | RO | Soft-Access-Point ist eingeschaltet | `homie/sma-inverter3/parameters/wl-softacsison` |

#### Portalparameter: EVC22-3AC-20

| Portal-Kanal | Gruppe | Export-Unit | Export-Zugriff | Kurzbeschreibung | MQTT-Topic (lesender Kandidat) |
| --- | --- | --- | --- | --- | --- |
| `Parameter.Chrg.ActChaMod` | EV-Charger | nicht angegeben | RO | Betriebsart des Ladevorgangs | `homie/sma-echarger/settings/charge-mode` |
| `Parameter.Chrg.CblLok` | EV-Charger | nicht angegeben | RO | Ladekabel an Ladestation verriegeln | `homie/sma-echarger/settings/cable-lock` |
| `Parameter.Chrg.ChrgLok` | EV-Charger | nicht angegeben | RO | Ladefreigabe aktivieren | `homie/sma-echarger/settings/approval-required` |
| `Parameter.Chrg.Plan.En` | EV-Charger | kWh | RO | Energiemenge des Ladevorgangs | `homie/sma-echarger/settings/plan-energy` |
| `Parameter.Chrg.StpWhenFl` | EV-Charger | nicht angegeben | RO | Trennung nach Vollladung | `homie/sma-echarger/settings/stop-when-full` |
| `Parameter.Chrg.StpWhenFlTm` | EV-Charger | min | RO | Ladebereitschaft bis Trennung | `homie/sma-echarger/settings/stop-delay` |
| `Parameter.Csmr.OptEgAval` | Energiemanagement | nicht angegeben | RO | Optionaler Energiebedarf | `homie/sma-echarger/parameters/csmr-optegaval` |
| `Parameter.Csmr.PriceLim` | Energiemanagement | nicht angegeben | RO | Max. Strompreis | `homie/sma-echarger/parameters/csmr-pricelim` |
| `Parameter.Csmr.PriceLimAval` | Energiemanagement | nicht angegeben | RO | Einplanung anhand max. Strompreis | `homie/sma-echarger/parameters/csmr-pricelimaval` |
| `Parameter.Csmr.Prio` | Energiemanagement | nicht angegeben | RO | Priorität | `homie/sma-echarger/parameters/csmr-prio` |
| `Parameter.Inverter.OutPhs` | AC-Seite | nicht angegeben | RO | Phasenzuordnung | `homie/sma-echarger/parameters/inverter-outphs` |
| `Parameter.Nameplate.ComProt` | Typenschild | nicht angegeben | RO | Kommunikationsprotokoll | `homie/sma-echarger/parameters/nameplate-comprot` |
| `Parameter.Nameplate.DevId` | Typenschild | nicht angegeben | RO | Geräte-ID; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.Location` | Typenschild | nicht angegeben | RO | Gerätename; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.MainModel` | Typenschild | nicht angegeben | RO | Geräteklasse | `homie/sma-echarger/parameters/nameplate-mainmodel` |
| `Parameter.Nameplate.Model` | Typenschild | nicht angegeben | RO | Gerätetyp | `homie/sma-echarger/parameters/nameplate-model` |
| `Parameter.Nameplate.ModelStr` | Typenschild | nicht angegeben | RO | Typenbezeichnung | `homie/sma-echarger/parameters/nameplate-modelstr` |
| `Parameter.Nameplate.MsValAcq` | Typenschild | nicht angegeben | RO | Art der Messwert-Erfassung | `homie/sma-echarger/parameters/nameplate-msvalacq` |
| `Parameter.Nameplate.PkgRev` | Typenschild | nicht angegeben | RO | Firmware-Version | `homie/sma-echarger/parameters/nameplate-pkgrev` |
| `Parameter.Nameplate.SerNum` | Typenschild | nicht angegeben | RO | Seriennummer; private Konfiguration oder administrative Aktion, Inhalt/Befehl nicht publizieren. | X: kein reguläres Topic |
| `Parameter.Nameplate.VendorStr` | Typenschild | nicht angegeben | RO | Hersteller | `homie/sma-echarger/parameters/nameplate-vendorstr` |
| `Parameter.Sys.UseAmbLght` | Gerät | nicht angegeben | RO | Umgebungsbeleuchtung aktivieren | `homie/sma-echarger/settings/ambient-enabled` |

Die Portalexporte ergänzen die tatsächlichen aktuellen Geräteparameter, ersetzen aber keine Modbus-Adresse, keinen Rohdatentyp und keine geprüfte lokale Schnittstelle. Insbesondere das Sunny-Boy--40-Registerprofil wird dadurch nicht zum bestätigten -41-Profil. Bei Home-Manager-Funktionen wie Prognoseladen/Lastspitzenkappung sind technische Kanäle jetzt identifiziert; Zugriffs-Endpunkte und Schreibfreigabe bleiben offen. Eine API-Rolle kann einen Parameter als RO exportieren, obwohl dieselbe Oberfläche eine separate Bedienfunktion anbietet.

Der eCharger-Portalexport nennt für `Parameter.Chrg.Plan.En` ausdrücklich kWh und für `Parameter.Chrg.StpWhenFlTm` min. Die lokale SMA-WebUI-Metadatenquelle bestätigt inzwischen dieselben Rohunits für EVC22-3AC-20 / 2.6.37.R ohne zusätzliche Skalierung; siehe VALIDATION.md. Geräte-Schreibabnahme bleibt offen. `Parameter.Csmr.PriceLim` hat im Export keine Unit; daher weiterhin keine erfundene Preisunit im MQTT-Feld.

## Erhalt der bestehenden openHAB-Funktionen

Alle 45 nicht gruppierten Items aus P04/P05 sind unten zugeordnet; die 41 Wechselrichter-Channels stehen oben. M01 ergänzt bestätigte Itemlinks und bestehende Berechnungen. Diese Zuordnung ersetzt keinen vollständigen Abgleich der verbleibenden Items, Regeln, Maps und Persistenz. `docs/migration-coverage.csv` bleibt das maschinenlesbare Migrationsledger; keine Zeile ist als fertig migriert markiert.

Eingabe-Items für Zielenergie, Endzeit und Netzanteil bleiben zunächst lokale openHAB-Vorbereitung. Erst PLAN/APPLY übernimmt ihre Werte ausdrücklich; ein Slider-Update schreibt nichts am Gerät. Gruppen/Widgetstruktur bleiben erhalten. Bool-Topics erfordern eine ausdrückliche `ON/OFF`-Abbildung für vorhandene Switch-Items. Bisherige SMA-Code-/Text-Maps bleiben überprüfbar; unbekannte Codes erhalten zusätzlich ihren Rohwert, keine erfundene Übersetzung.

| Bestehendes Item | openHAB-Typ | Unit / Umrechnung | Zugriff geplant | Kurzbeschreibung | MQTT-Topic |
| --- | --- | --- | --- | --- | --- |
| `SMA_ECharger_Power` | Number:Power | W | RO | Aktuelle Ladeleistung. | `homie/sma-echarger/measurements/power` |
| `SMA_ECharger_SessionEnergy` | Number:Energy | kWh; Quelle Wh / 1000 | RO | Energie des Ladevorgangs. | `homie/sma-echarger/measurements/session-energy` |
| `SMA_ECharger_VehicleStatus` | String | — | RO | Status als Text aus vorhandener MAP. | `homie/sma-echarger/measurements/vehicle-status` |
| `SMA_ECharger_VehicleStatusCode` | Number | — | RO | Unveränderter numerischer Fahrzeugcode. | `homie/sma-echarger/measurements/vehicle-status-code` |
| `SMA_ECharger_Health` | String | — | RO | Gerätezustand als Text aus MAP; Rohcode separat. | `homie/sma-echarger/measurements/health` |
| `SMA_ECharger_Firmware` | String | — | RO | Firmwarepaket als Text. | `homie/sma-echarger/parameters/nameplate-pkgrev` |
| `SMA_ECharger_LastSuccess` | DateTime | —; ISO 8601 | RO/A | Letzte erfolgreiche SEMP-Abfrage. | `homie/sma-echarger/diagnostics/semp-last-success` |
| `SMA_ECharger_ChargeMode` | String | —; SMA-Code als enum | RW vorgesehen | Rückgelesener SMA-Moduscode; vorhandene MAP erhalten. | `homie/sma-echarger/settings/charge-mode` |
| `SMA_ECharger_ManualApproval` | String | — | RO | Freigabestatus als Text zusätzlich zum Bool. | `homie/sma-echarger/measurements/manual-approval` |
| `SMA_ECharger_Control` | String | — | Befehlsentwurf | PV/FAST/STOP/PLAN und lesende TEST/REFRESH/DISCOVER-Aktionen erhalten. | `homie/sma-echarger/commands/control` |
| `SMA_ECharger_ControlResult` | String | — | RO/A | Bereinigtes Ergebnis der letzten Aktion; pending/confirmed/failed/uncertain. | `homie/sma-echarger/diagnostics/control-result` |
| `SMA_ECharger_ChargingRelease` | Switch | — | RW vorgesehen | Laden freigeben (5172) oder gesperrt halten (5171). | `homie/sma-echarger/settings/charging-release` |
| `SMA_ECharger_ChargingLock` | Switch | — | RW vorgesehen | Für jeden Ladevorgang eine Freigabe verlangen; 1129 ja, 1130 nein. | `homie/sma-echarger/settings/approval-required` |
| `SMA_ECharger_StopWhenFull` | Switch | — | RW vorgesehen | Ladevorgang beenden, wenn das Fahrzeug als voll erkannt wird. | `homie/sma-echarger/settings/stop-when-full` |
| `SMA_ECharger_StopDelay` | Number:Time | min | RW vorgesehen | Wartezeit bis zur Beendigung; Metadaten 5…1440 min, ganzzahlig. | `homie/sma-echarger/settings/stop-delay` |
| `SMA_ECharger_CableLock` | Switch | — | RW vorgesehen | Ladekabel dauerhaft verriegeln; 308 ein, 303 aus. | `homie/sma-echarger/settings/cable-lock` |
| `SMA_ECharger_PlanEnergyInput` | Number:Energy | kWh | Lokales Eingabe-Item | Energie vor PLAN vorbereiten; kein automatischer Gerätebefehl. | —: Vorbereitung bleibt in openHAB |
| `SMA_ECharger_PlanEndInput` | DateTime | —; ISO 8601 | Lokales Eingabe-Item | Endzeit vor PLAN vorbereiten; Zeitzone erhalten. | —: Vorbereitung bleibt in openHAB |
| `SMA_ECharger_PlanEnergy` | Number:Energy | kWh; lokal 2.6.37.R verifiziert | RW* vorgesehen | Für den Ladeplan gewünschte zu ladende Energie; kein Fahrzeug-SoC. | `homie/sma-echarger/settings/plan-energy` |
| `SMA_ECharger_PlanEnd` | DateTime | s → ISO 8601 | RW* vorgesehen | End-/Abfahrtszeit des Ladeplans; Zeitbasis und Zeitzone prüfen. | `homie/sma-echarger/settings/plan-end` |
| `SMA_ECharger_LedBrightness` | String | — | RW vorgesehen | Statuslicht: 5191 niedrig, 5190 mittel, 5173 hoch. | `homie/sma-echarger/settings/led-brightness` |
| `SMA_ECharger_AmbientEnabled` | Switch | — | RW vorgesehen | Ambientelicht aktivieren; 308 ein, 303 aus. | `homie/sma-echarger/settings/ambient-enabled` |
| `SMA_ECharger_AmbientBrightness` | String | — | RW vorgesehen | Ambientelicht-Helligkeit; gleiche drei Stufen. | `homie/sma-echarger/settings/ambient-brightness` |
| `SMA_ECharger_TotalEnergy` | Number:Energy | kWh; Quelle Wh / 1000 | RO | Gesamtzähler, Fallback anhand bestätigter API-Antwort. | `homie/sma-echarger/measurements/total-energy` |
| `SMA_ECharger_CurrentL1` | Number:ElectricCurrent | A | RO | Ladestrom der Phase. | `homie/sma-echarger/measurements/current-l1` |
| `SMA_ECharger_CurrentL2` | Number:ElectricCurrent | A | RO | Ladestrom der Phase. | `homie/sma-echarger/measurements/current-l2` |
| `SMA_ECharger_CurrentL3` | Number:ElectricCurrent | A | RO | Ladestrom der Phase. | `homie/sma-echarger/measurements/current-l3` |
| `SMA_ECharger_VoltageL1` | Number:ElectricPotential | V | RO | Spannung der Phase. | `homie/sma-echarger/measurements/voltage-l1` |
| `SMA_ECharger_VoltageL2` | Number:ElectricPotential | V | RO | Spannung der Phase. | `homie/sma-echarger/measurements/voltage-l2` |
| `SMA_ECharger_VoltageL3` | Number:ElectricPotential | V | RO | Spannung der Phase. | `homie/sma-echarger/measurements/voltage-l3` |
| `SMA_ECharger_Frequency` | Number:Frequency | Hz | RO | Netzfrequenz. | `homie/sma-echarger/measurements/frequency` |
| `SMA_ECharger_RuleStatus` | String | — | RO/A | Übernommene Skript-/Adapterdiagnose; keine aktiven alten Doppelregler. | `homie/sma-echarger/diagnostics/adapter-status` |
| `SMA_ECharger_ApiStatus` | String | — | RO/A | Status der lokalen API-Sitzung und Abfragen. | `homie/sma-echarger/diagnostics/api-status` |
| `SMA_ECharger_ApiLastSuccess` | DateTime | —; ISO 8601 | RO/A | Letzte erfolgreiche lokale Parameterabfrage. | `homie/sma-echarger/diagnostics/api-last-success` |
| `SMA_ECharger_ApiOptions` | String | —; bereinigtes JSON | RO/A | Nur erlaubte Kanalmetadaten/Optionen; keine geheimen Werte. | `homie/sma-echarger/diagnostics/api-options` |
| `SMA_ECharger_AdditionalMeasurements` | String | —; bereinigtes JSON | RO/A | Diagnose zusätzlicher erlaubter Kanäle, Einheit und Gültigkeit; Einzelwerte bevorzugen. | `homie/sma-echarger/diagnostics/additional-measurements` |
| `SMA_ECharger_Portal_Control` | String | — | Befehlsentwurf | TEST/REFRESH lesend; APPLY nur ausdrücklich vorbereiteten PV-Wert. | `homie/sma-echarger/portal/control` |
| `SMA_ECharger_Portal_Result` | String | — | RO/A | Portal-Befehls-/Lesergebnis ohne Authentifizierungsdetails. | `homie/sma-echarger/portal/result` |
| `SMA_ECharger_Portal_PvMinimum` | Number | % | RW vorgesehen | Gespeicherter Mindest-PV-Anteil, ganze 0…100. | `homie/sma-echarger/portal/pv-minimum` |
| `SMA_ECharger_Portal_GridShare` | Number | % | RO/A | 100 minus Mindest-PV; erlaubter Netzanteil, kein Istwert. | `homie/sma-echarger/portal/grid-share` |
| `SMA_ECharger_Portal_GridShareInput` | Number | % | Lokales Eingabe-Item | Netzanteil vorbereiten; erst APPLY schreibt die inverse PV-Vorgabe. | —: Vorbereitung bleibt in openHAB |
| `SMA_ECharger_Portal_SettingMode` | String | — | RO/A | Betriebsart aus optionalEnergyDemand-Feldern. | `homie/sma-echarger/portal/setting-mode` |
| `SMA_ECharger_Portal_Rights` | String | —; boolean im MQTT | RO/A | Schreibrecht der Sitzung; bestehendes String-Item braucht explizite Abbildung. | `homie/sma-echarger/portal/writable` |
| `SMA_ECharger_Portal_RuleStatus` | String | — | RO/A | Status des Portaladapters. | `homie/sma-echarger/portal/status` |
| `SMA_ECharger_Portal_LastSuccess` | DateTime | —; ISO 8601 | RO/A | Zeit der letzten bestätigten Portalabfrage. | `homie/sma-echarger/portal/last-success` |

### Nachträglich eingegangene Home-Manager-Items und Berechnungen

M01 ergänzt vier bereits verknüpfte Home-Manager-Items und zehn Berechnungs-/Historienfähigkeiten. Die Energie-Items verwenden derzeit Versatzprofile mit privaten Offsets; alte JS-Offsets nicht zusätzlich anwenden. Bestehende Berechnungen, Datenbankabfragen und Smart-Grid-Steuerung bleiben zunächst in openHAB. Ein neuer lokaler Tageszähler ersetzt weder InfluxDB-Historie noch den externen Shelly-Wallboxzähler automatisch. Der Ledger umfasst jetzt 100 Zeilen, sämtliche vorherigen Zeilen bleiben erhalten.

| Bestehendes Item | Unit laut Inventar | Verbleib / Zugriff | Kurzbeschreibung | MQTT-Topic |
| --- | --- | --- | --- | --- |
| `SMAEnergyMeter_BezogeneEnergie` | kWh | RO | Kumulativer Netzbezug mit bestehendem privatem Versatzprofil. | `homie/sma-home-manager/measurements/energy-import` |
| `SMAEnergyMeter_EingespeisteEnergie` | kWh | RO | Kumulative Einspeisung mit bestehendem privatem Versatzprofil. | `homie/sma-home-manager/measurements/energy-export` |
| `SMAEnergyMeter_BezogeneLeistung` | W | RO | Momentaner Netzbezug. | `homie/sma-home-manager/measurements/power-import` |
| `SMAEnergyMeter_EingespeisteLeistung` | W | RO | Momentane Netzeinspeisung. | `homie/sma-home-manager/measurements/power-export` |
| `inverterActivePower` | W | Berechnung bleibt in openHAB | PV1 + PV3 alle 5 s; auch an Shelly-Display weitergegeben. | —: vorhandenes openHAB-Item weiterführen |
| `inverterDailyYield` | kWh | Berechnung bleibt in openHAB | PV1 + PV3 Tageserträge alle 5 min; Item-/Zählerskalierung prüfen. | —: vorhandenes openHAB-Item weiterführen |
| `inverterTotalYield` | kWh | Berechnung bleibt in openHAB | PV1 + PV3 Gesamterträge alle 5 min; Historie erhalten. | —: vorhandenes openHAB-Item weiterführen |
| `TotalPowerConsumption` | W | Berechnung bleibt in openHAB | PV1 + PV3 + Batterieentladung + Netzbezug − Einspeisung − Batterieladung alle 15 s; negative Ergebnisse übersprungen. | —: vorhandenes openHAB-Item weiterführen |
| `PowerConsumptionBatIncl` | W | Berechnung bleibt in openHAB | Gleiche Bilanz plus Batterieladung; negative Ergebnisse übersprungen. | —: vorhandenes openHAB-Item weiterführen |
| `Wallbox_Tagesverbrauch` | kWh? | Berechnung bleibt in openHAB | Shelly-Gesamtzähler deltaSince lokaler Mitternacht bei Zähleränderung; genaue Quantity-Semantik prüfen. | —: vorhandenes openHAB-Item weiterführen |
| `Strom_Tagesverbrauch_Number_Result` | kWh | Berechnung bleibt in openHAB | InfluxDB-Integration von TotalPowerConsumption seit Mitternacht Europe/Berlin; 10-s-Mittelwerte, Abfrage alle 300 s. | —: vorhandenes openHAB-Item weiterführen |
| `Strom_Tagesbezug` | kWh | Berechnung bleibt in openHAB | Entsprechende InfluxDB-Integration von inverter1PowerDrawn; Abfrage alle 300 s. | —: vorhandenes openHAB-Item weiterführen |
| `Strom_Durchschnitt_Tagesverbrauch_Number_Result` | kWh | Berechnung bleibt in openHAB | Mittelwert der Tagesmaxima aus sieben abgeschlossenen Tagen, Wallbox-ON-Tage ausgeschlossen; Abfrage alle 4 h, Tagesgrenzen offen. | —: vorhandenes openHAB-Item weiterführen |
| `TotalPowerEarnings` | Währung offen | Berechnung bleibt in openHAB | Kumulative Einspeiseenergie × privater Tarif alle 30 min; Einheit aus Item prüfen. | —: vorhandenes openHAB-Item weiterführen |

Referenzen: [offizielle openHAB-Items](https://www.openhab.org/docs/configuration/items.html), [Einheiten](https://www.openhab.org/docs/concepts/units-of-measurement.html), [Modbus](https://www.openhab.org/addons/bindings/modbus/), [Persistenz](https://www.openhab.org/docs/configuration/persistence.html). Eine erfolgreiche Item-Zuordnung gilt erst nach Vergleich von Einheit, Zeitbezug, Triggern, Zählerhistorie und UI-Verhalten als Migration.

### Inzwischen gelieferte Wechselrichter-Transformationen

| Transform | Unit-Auswirkung | Kurzbeschreibung | MQTT-Zuordnung |
| --- | --- | --- | --- |
| smalimit.js | unverändert | Nichtnegative Eingabe parseFloat; negativ → 0. Kein allgemeiner NaN-Filter. | Bestehende Channels oben; separate Kompatibilitätsentscheidung offen. |
| smalimit_undef.js | unverändert | Nichtnegative Eingabe parseFloat; negativ → UNDEF. | Bestehende Ertrags-Channels oben. |
| smalimit1000.js | ÷ 1000 | Nichtnegative Eingabe skalieren; negativ → 0. | Bestehende DC-Strom-Channels oben. |
| smalimit100.js | ÷ 100 | Nichtnegative Eingabe skalieren; negativ → 0. | Bestehende Spannungs-Channels oben. |
| smalimit10_undef.js | ÷ 10 | Nichtnegative Eingabe skalieren; negativ → UNDEF; reale negative Temperatur prüfen. | Bestehende Temperatur-Channels oben. |
| smagrid_consumption.js / smagrid_feedin.js | ÷ 1000 plus privater Offset | Historische kumulative Zählerfortsetzung; Abhängigkeiten/Einheit aus Items bestimmen. | Noch keine neue Property; bestehende Historienkontinuität erhalten. |
| sma_undef.js | unverändert | Numerische 0 wird UNDEF; echte Null von nicht verfügbar trennen. | Item-Verwendung noch offen. |

## Berechnete Werte und Diagnose

Berechnungen sind A/K. M01 belegt die oben beschriebenen bestehenden Regeln; die folgende Tabelle enthält zusätzliche mögliche Bridge-Berechnungen, **keinen Auftrag zur Verlagerung oder Ersetzung der openHAB-Logik**. Erst nach elektrischem Anlagenabgleich und vollständiger Prüfung bestehender Regeln festlegen. Alle Eingangswerte müssen denselben Bilanzpunkt, kompatible Vorzeichen und hinreichend nahe Zeitstempel haben. Den Speicherwechselrichter nicht zu PV-Wechselrichtern addieren. Wallboxleistung ist bereits Teil des Hausverbrauchs und darf nicht nochmals addiert werden.

| Berechnung | Unit | Kurzbeschreibung / Voraussetzung | MQTT-Topic (A/K) |
| --- | --- | --- | --- |
| PV-Gesamtleistung | W | Summe bestätigter AC-Erzeugungsleistungen von Tripower und Sunny Boy; Speicher ausschließen. | `homie/sma-home-manager/calculated/pv-power` |
| Netzleistung mit Vorzeichen | W | Netzbezug minus Einspeisung; positiv = Bezug, negativ = Export. | `homie/sma-home-manager/calculated/grid-net-power` |
| Batterieleistung mit Vorzeichen | W | Entladeleistung minus Ladeleistung; positiv = Versorgung aus Speicher. | `homie/sma-home-manager/calculated/battery-net-power` |
| Hausverbrauch | W | PV + Netzbezug − Einspeisung + Batterieentladung − Batterieladung; Zählerplatz und Verluste prüfen. | `homie/sma-home-manager/calculated/consumption-power` |
| Verbrauch ohne Wallbox | W | Hausverbrauch minus lokale Wallboxleistung; negative Differenzen als Bilanzproblem kennzeichnen. | `homie/sma-home-manager/calculated/consumption-without-charger` |
| Momentaner nutzbarer PV-Überschuss | W | Bilanzabhängige Planungsgröße; Formel und Reserven erst mit bestehender Regel abstimmen. | `homie/sma-home-manager/calculated/pv-surplus-power` |
| Netzbezugsenergie heute | kWh | Differenz kumulativer Bezugswerte seit lokalem Tagesbeginn; Neustart/Reset/Offset behandeln. | `homie/sma-home-manager/calculated/grid-import-energy-day` |
| Einspeiseenergie heute | kWh | Differenz kumulativer Exportwerte seit lokalem Tagesbeginn. | `homie/sma-home-manager/calculated/grid-export-energy-day` |
| PV-Erzeugung heute | kWh | Summe passender PV-Tageszähler; Speicherertrag nicht addieren. | `homie/sma-home-manager/calculated/pv-energy-day` |
| Batterieladung / -entladung heute | kWh | Aus bestätigten kumulativen Zählern, sonst Integration mit Lückenkennzeichnung. | `homie/sma-home-manager/calculated/battery-charge-energy-day`; `homie/sma-home-manager/calculated/battery-discharge-energy-day` |
| Wallboxenergie heute | kWh | Gesamtzählerdifferenz über den Tag; Sessionenergie allein reicht nicht. | `homie/sma-home-manager/calculated/charger-energy-day` |
| Autarkie über Zeitraum | % | 100 × (1 − Netzbezugsenergie / Verbrauchsenergie); nur nach bestätigter Bilanzdefinition, Nenner > 0. | `homie/sma-home-manager/calculated/self-sufficiency` |
| Eigenverbrauchsquote über Zeitraum | % | 100 × lokal verwendete PV-Energie / PV-Erzeugung; Batterie-/Netzladung und Zeitverschiebung berücksichtigen. | `homie/sma-home-manager/calculated/self-consumption-ratio` |

Tagesgrenzen mit `Europe/Berlin`, Sommer-/Winterzeit und Persistenz abgleichen. Zeitstempel der Baseline dauerhaft speichern; fehlende Tagesanfangswerte oder Zählerreset erzeugen eine Diagnose statt erfundener Null. Bestehende private Zähleroffsets niemals als allgemeine feste Werte in den Adapter einbauen.

Für jedes der fünf vorgesehenen Homie-Geräte werden dieselben Quelldiagnosen geplant. `<device>` expandiert zu `sma-inverter1`, `sma-inverter2`, `sma-inverter3`, `sma-home-manager` oder `sma-echarger`; das ist ein Tabellenplatzhalter, kein wörtlicher Topic-Bestandteil. eCharger-SEMP-, lokale API- und Portaldiagnosen sind zusätzlich im Item-Mapping getrennt erfasst.

| Diagnose / Metadatum | Typ / Unit | Kurzbeschreibung | MQTT-Topic je Gerät |
| --- | --- | --- | --- |
| Homie-Gerätezustand | string/enum; — | init/ready/disconnected/lost usw.; MQTT-Verbindung und Quelle getrennt bewerten. | `homie/<device>/$state` |
| Quelle verfügbar | boolean; — | Ob die zuständige lokale Quelle aktuell verwertbare Daten liefert. | `homie/<device>/diagnostics/source-available` |
| Quelle veraltet | boolean; — | Alter liegt über festgelegter Frischegrenze. | `homie/<device>/diagnostics/stale` |
| Datenalter | integer; s | Zeit seit letzter gültiger Stichprobe, keine künstliche Aktualisierung durch republizierten Cache. | `homie/<device>/diagnostics/source-age` |
| Letzte gültige Stichprobe | string; ISO 8601 | Messzeitpunkt; Empfangszeit separat behandeln, falls Gerätezeit fehlt. | `homie/<device>/diagnostics/sample-time` |
| Letzter erfolgreicher Zugriff | string; ISO 8601 | Erfolg der Quelle unabhängig vom MQTT-Publish. | `homie/<device>/diagnostics/last-success` |
| Fehlerklasse | string/enum; — | Bereinigte Fehlerursache, z. B. timeout/auth/invalid/unsupported. | `homie/<device>/diagnostics/error` |
| Fehler in Folge | integer; Anzahl | Aufeinanderfolgende Quellenausfälle; keinen ganzen Dienst blind neu starten. | `homie/<device>/diagnostics/consecutive-errors` |
| Unterstützte Properties | string; bereinigtes JSON | Nur freigegebene Fähigkeiten/Einheiten; keine ungefilterten Geräte-/Auth-Antworten. | `homie/<device>/diagnostics/capabilities` |
| Property-Typ | string; — | Homie integer/float/boolean/string/enum/color gemäß tatsächlicher Nutzlast. | `homie/<device>/<node>/<property>/$datatype` |
| Property-Einheit | string; — | Physikalische Einheit der normierten Nutzlast, z. B. W, kWh, A, V, Hz, °C, %. | `homie/<device>/<node>/<property>/$unit` |
| Property-Format | string; — | Enum-Optionen oder erlaubter Zahlenbereich, soweit bestätigt. | `homie/<device>/<node>/<property>/$format` |
| Property schreibbar | boolean; — | Nur bei freigegebener und implementierter Befehlsfunktion true. | `homie/<device>/<node>/<property>/$settable` |

Diagnose-Gesundheit und MQTT-Last-Will müssen unabhängig von fehlenden einzelnen Sensorwerten bleiben. Die zulässigen Frischegrenzen und das Verhalten der Docker-Zustandsprüfung sind unter Q08 im Projekttagebuch offen. `/set` akzeptiert nur freigegebene Aktionen, validierte Werte und nicht retained gesendete Befehle. Zustands-Topics enthalten erst nach Rücklesen bestätigte Gerätestände; Bridge-Befehlsdiagnosen dürfen ausdrücklich `pending` oder `uncertain` melden.

## Offene Prüfungen und Pflege

- [x] Alle 13 unterschiedlichen gelieferten PDF-Inhalte gelesen; deutsche Modbus-HTML vollständig mit 198 Zeilen ausgewertet. Doppelablagen per SHA-256 abgeglichen.
- [x] 85 lokale eCharger-Metadaten und 25 SEMP-Parameter vollständig erfasst, vorhandene 41 Wechselrichter-Channels und 45 Wallbox-/Portal-Items zugeordnet.
- [x] Angemeldeten ennexOS-Tab lesend geprüft; exakte Modellcodes und Firmwarestände gefunden. Zugangsdaten mussten nicht geteilt werden. Keine Gerätebefehle gesendet.
- [x] Alle 458 Parameterzeilen aus den fünf aktuellen Portalexporten mit Kanal, Unit und Zugriffskennzeichnung ergänzt; keine aktuellen Werte übernommen.
- [ ] Passende vollständige Registerlisten für **STP8.0-3AV-40 / 4.10.10.R**, **SBS3.7-10 / 4.07.31.R** und **SB4.0-1AV-41 / 4.10.10.R** nachreichen bzw. mit den Ergebnissen des anderen Chats abgleichen. S01 ist dafür noch kein geprüfter Ersatz.
- [ ] Modbus-Hosts privat mit Portalidentitäten abgleichen; historische Sunny-Boy-Bezeichnung korrigieren, ohne die bestehenden Topic-/Item-IDs automatisch umzubenennen.
- [ ] Batterie-Register, 30777, gültige negative Messwerte, NaN-Kennwerte und vorzeichenbehaftete Typen mit den tatsächlich passenden Profilen prüfen.
- [x] M01 mit 34 Wechselrichter-Itemlinks, vier Home-Manager-Items und zehn abgeleiteten Fähigkeiten übernommen; ihre Historie/Offsets und Berechnungsabhängigkeiten erhalten.
- [ ] Noch fehlende sieben Itemlinks sowie vollständige abhängige Regeln, Maps, Persistenz und UI-Abhängigkeiten prüfen. Vorhandene Tageswerte, Shelly-Zähler und private Versatzprofile erhalten.
- [ ] Home-Manager-UDP-Telegramm privat erfassen: OBIS-Umfang, Skalierung/Leistungsfaktor, Phasenreihenfolge, Messpunkt, Zeitbezug, Verschlüsselung und Multicast-/Direktzustellung prüfen.
- [x] Portal zeigt NSD-Vorgaben über Modbus als ausgeschaltet. Auch der Modbus-Client ist ausgeschaltet. Die Dashboard-Quellenanzeige „Modbus“ allein ist kein Aktivierungsnachweis.
- [ ] Lokale NSD-Erreichbarkeit und aktuelle Firmwaregeltung der Grid-Guard-Anforderungen prüfen; keinen Zugangscode setzen oder Netzschutz-/Batterieregler zum bloßen Auslesen aktivieren.
- [ ] Vorhandene 3-/5-s-Poller gegen die Herstellerempfehlungen prüfen; keine Pollraten pauschal erhöhen. Timeout, Verbindungslimits und Blockgrößen festlegen.
- [ ] Rohunit/Grenzen der Zielenergie und epoch-/Zeitzonenbehandlung der Planendzeit bestätigen; atomare Planübernahme entwerfen. RFID-/Fahrzeug-SoC-Kanäle nicht als vorhanden behaupten.
- [ ] Alle weiteren Portal-Kandidaten nur nach bereinigten lesenden API-Belegen ergänzen. Für reine UI-Werte weder Endpunkte noch Schreibrechte erfinden. PV-Setter bleibt zunächst die einzige Portal-Schreibfunktion.
- [ ] Kanonische Einheit und Homie-Payload pro Property festlegen, insbesondere Enum-Text vs. Rohcode, nullable-Felder, Zeiten, 32-/64-Bit-Energie und JSON-Diagnosen. Topic-Doppelbelegungen nur bei identischer Bedeutung/Einheit zulassen.
- [ ] Frischegrenzen, Quellenausfallverhalten und periodische/ausdrückliche Cloudaktualisierung abstimmen. Historische Portaldaten nicht als Live-Messung behandeln.

Bei jeder neuen Unterlage die Quelle/Version und Modellgeltung ergänzen, Register/Kanal, Zugriff, Datentyp, Skalierung, Unit, deutsche Bedeutung und Topic gemeinsam prüfen. Bestehende Topics möglichst stabil halten; erforderliche Änderungen ausdrücklich mit Migrationshinweis dokumentieren. Einen Kandidaten erst nach Nachweis zu D/B bzw. nach Adapter-/Live-Prüfung zu verifiziertem Laufzeitbestand hochstufen. Schreibfähigkeiten separat freigeben und rücklesen. Die ursprünglichen Dateien unter `private/` bleiben unverändert.

Änderungsverlauf: 2026-10-10 — erster vollständiger Quellenkatalog mit lokaler/Portal-Trennung, Einheitenlücken, Topic-Vorschlägen und Firmware-/Modellabgleich. Laufzeitimplementierung und Geräte-Schreibtests sind weiterhin ausstehend.

## Python-Lesestand vom 10.10.2026

- Implementiert: Konfiguration/Profilprüfung, generischer Modbus-Leser, Home-Manager-Zählerdekodierung für die vier Bilanzwerte, lokale eCharger-API/SEMP, optionales ennexOS-Lesen und Homie 4. Synthetische Tests belegen Formatprüfung, Identitätsgrenzen, Missing-/Stale-Verhalten und MQTT-Lebenszyklus; keine Hardwareabnahme.
- Wechselrichter: Alle 41 Channels bleiben im Ledger. Ohne validierte Modell-/Firmware-/Identitätszuordnung keinerlei Polling. Zusätzliche Register aus dieser Tabelle werden nicht automatisch aktiviert.
- Home Manager: Bezugs-/Einspeiseleistung in W, Gesamtenergie in kWh. Private openHAB-Versatzprofile bleiben dort; keine doppelten Offsets oder Tageszählerrücksetzungen. Weitere OBIS-/Phasenwerte sowie verschlüsselte Telegramme bleiben offen.
- eCharger: SEMP und API separat aktivierbar; Topic-IDs und bekannte Status-Maps erhalten. Lokal `Plan.En` und `StpWhenFlTm` mit passender API-Unit oder der verifizierten Modell-/Firmwarezuordnung veröffentlichen. Die Portal-Unit bestätigt keine lokale Rohskalierung. Fehlende/veraltete Messzeitstempel machen Messwerte unverfügbar.
- Portal: Mindest-PV-Anteil, daraus berechneter erlaubter Netzanteil, Rechte und Einstellmodus lesend implementiert. `pollIntervalSeconds=0` meldet sich nicht automatisch an; `--refresh-portal` fordert einmaliges Lesen an. Portal-Lesen bleibt unabhängig von API/SEMP.
- Alle Properties bleiben `$settable=false`, ohne `/set`-Abonnement. Schreib-/Komfortbefehle, zusätzliche Diagnosezusammenfassungen und vollständige openHAB-Abnahme bleiben offen. Herkunftskennzeichen und Inventarzeilen werden durch Offline-Unterstützung nicht zu Live-Nachweisen.

Siehe `docs/migration-coverage.csv` für den zeilenweisen Stand. Berechnungen, Regeln, Shelly-Quellen und InfluxDB-Historien bleiben in openHAB.

## Geräte- und MQTT-Lesetest am 10.10.2026

Die drei Standardprofile unter `ressources/profiles/` enthalten jetzt alle 41 bestehenden Wechselrichterkanäle und jeweils Modell, Firmware und Seriennummer. Grundlage sind passende offizielle SMA-Listen, lokale FC04-Identitätsabfragen und Offline-Decodiertests; Quellen und Abweichungen stehen in [REGISTER_VALIDATION.md](REGISTER_VALIDATION.md). Am echten Broker wurden 39 Messwerte und neun Identitätswerte geprüft. Die zwei Sunny-Boy-Phasenwerte 30777/30783 liefern SMA-NaN und werden bis zum Tagesvergleich ausgelassen.

Wichtige Korrektur: Alle drei gebündelten Wechselrichterprofile veröffentlichen 30531/30537 in ganzen kWh. Beim Storage ist dies eine bewusste Abweichung von den Wh-Angaben der offiziellen V13-Liste: Andreas bestätigt am 11.10.2026 Tageswert 2 entsprechend 2 kWh Batterieentladung und zur kWh-Einheit passende Gesamtenergie. Rohwerte bleiben unskaliert; siehe REGISTER_VALIDATION.md. Dokumentierte U32-Werte werden unsigned decodiert; Zähler oberhalb 2³¹ bleiben gültig. Statusstrings und Intervalle bleiben erhalten. Alte negative-zu-Null-Filter ersetzen keine Sentinelprüfung; gültige negative Messwerte bleiben vorzeichenbehaftet und benötigen den Parallelabgleich.

SEMP liefert zusätzlich die belegten Einstellungen und Rohdiagnosen: Phasencode, Geräte-/Fahrzeug-/Ereigniscodes, Moduswechsel, Registrierung und Anlagen-Sollwerte. Alle sind `$settable=false`. Die Einheiten der normierten Sollwerte sind weiterhin offen; es wird keine Prozent-Unit behauptet. `parameters/chrg-plan-en-raw` und `parameters/chrg-stpwhenfltm-raw` zeigen die Rohzahlen ohne Unit; `settings/plan-energy` und `settings/stop-delay` bleiben ohne verifizierte Skalierung unverfügbar. Standortname sowie sensible Konto-/Netzwerkdaten werden nicht veröffentlicht. Mess- und Sollwerte mit veralteten Quellzeitstempeln bleiben unverfügbar. Mit erweiterten SEMP-Lesewerten wurden insgesamt 69 Werte am Broker geprüft.

Home Manager bleibt auf dem Mac ausdrücklich deaktiviert, da dieser in einem anderen Netz liegt. Serienselektor/Multicast werden auf dem Pi geprüft. Authentifizierte lokale Zusatzmessungen, Portal-Mindest-PV-Anteil, Schreibfunktionen und vollständiger openHAB-/Persistenzabgleich bleiben offen.

## Home Manager Modbus implementation status, 2026-10-10

The optional Modbus TCP transport now implements the complete readable inventory from HM-20-Modbus-NSD-TI-de-12, with documentation-backed mappings and deterministic offline tests. The authoritative implemented topic/type/unit table is [HOME_MANAGER_MODBUS.md](HOME_MANAGER_MODBUS.md): 16 core values, all 245 assignment slots and 16 parameter templates per valid assigned inverter. Earlier candidate topics in this catalogue remain planning evidence; use that table for current adapter discovery. Source RW entries remain read-only. Pure WO entries and undocumented phase-register guesses are excluded. Grid Guard access and firmware-specific live availability remain pending; no Home Manager value is accepted as migrated by this implementation alone.
