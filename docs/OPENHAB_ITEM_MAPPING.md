# openHAB old and new Item mapping

Updated 2026-10-15. The inverter/Home Manager inventory was observed on
2026-10-14; nine plant Item names, labels, units and channel links were read
in the live openHAB UI on 2026-10-15. Scope: three inverters, Home Manager and
related plant/household calculations. Andreas excludes Wallbox Items from
comparison. Grafana and its prerequisites are step two.

There are **46 recorded Item pairs**, **2 old calculations without a bridge
counterpart**, and **33 observed new-only Items**. All eight previously missing
new plant Item names are now confirmed. No missing new Item names remain in
this scoped mapping. Value equivalence remains a separate comparison.

The [complete CSV](openhab-item-mapping.csv) carries status, exact Homie topic
and comparison notes. [New-only CSV](openhab-new-only-items.csv) and
[unmatched old Items CSV](openhab-unmatched-old-items.csv) provide separate views.
Item names and German labels below preserve the recorded installation spelling.
Groups are excluded because they are not measurement/state counterparts.

## Old Items without a bridge counterpart

- **Strom_Durchschnitt_Tagesverbrauch_Number_Result** (Stromverbrauch Tagesdurchschnitt): Seven-day average excluding Wallbox ON days retained in openHAB for Smart-Grid; no bridge replacement selected.
- **TotalPowerEarnings** (Gesamt Stromverdienst): Tariff calculation retained in openHAB; no bridge replacement selected.

## Recorded Item pairs

A pair confirms the recorded channel association, not numerical equivalence.

### Plant and household calculations

| Old Item | Old label | New Item | New label | Unit |
| --- | --- | --- | --- | --- |
| PowerConsumptionBatIncl | Gesamtstromverbrauch inkl. Batterieladung | smaplant_Hausverbrauchsleistung_inklusive_Batterieladung | Hausverbrauchsleistung inklusive Batterieladung | W |
| Strom_Tagesbezug | Strom Tagesbezug | smaplant_Tagesbezug | Tagesbezug | kWh |
| Strom_Tageseinspeisung | Strom Tageseinspeisung | smaplant_Tageseinspeisung | Tageseinspeisung | kWh |
| Strom_Tagesverbrauch_Number_Result | Strom Tagesverbrauch | smaplant_HausTagesverbrauch | Haus-Tagesverbrauch | kWh |
| TotalPowerConsumption | Gesamtstromverbrauch | smaplant_Berechnete_Hausverbrauchsleistung | Berechnete Hausverbrauchsleistung | W |
| inverterActivePower | PV Produktion | smaplant_PVGesamtwirkleistung | PV-Gesamtwirkleistung | W |
| inverterDailyYield | Tagesertrag | smaplant_PVGesamttagesertrag | PV-Gesamttagesertrag | kWh |
| inverterTotalYield | Gesamtertrag | smaplant_PVGesamtertrag | PV-Gesamtertrag | kWh |

### Home Manager

| Old Item | Old label | New Item | New label | Unit |
| --- | --- | --- | --- | --- |
| SMAEnergyMeter_BezogeneEnergie | Bezogene Energie | smahomemanager_Bezogene_Energie | Bezogene Energie | kWh |
| SMAEnergyMeter_BezogeneLeistung | Leistung Bezug | smahomemanager_Netzbezugsleistung | Netzbezugsleistung | W |
| SMAEnergyMeter_EingespeisteEnergie | Eingespeiste Energie | smahomemanager_Eingespeiste_Energie | Eingespeiste Energie | kWh |
| SMAEnergyMeter_EingespeisteLeistung | Leistung Einspeisung | smahomemanager_Einspeiseleistung | Einspeiseleistung | W |

### Inverter 1 roof

| Old Item | Old label | New Item | New label | Unit |
| --- | --- | --- | --- | --- |
| inverter1ActivePower | PV Produktion | smainv1roof_Leistung | Leistung | W |
| inverter1DC1Cur_input | DC Strom Eingang SO | smainv1roof_Measurements_Currentainput | DC-Eingangsstrom | A |
| inverter1DC1Volt_input | DC Spannung Eingang SO | smainv1roof_Measurements_Voltageainput | DC-Eingangsspannung | V |
| inverter1DC2Cur_input | DC Strom Eingang NW | smainv1roof_Measurements_Currentbinput | DC-Eingangsstrom | A |
| inverter1DC2Volt_input | DC Spannung Eingang NW | smainv1roof_Measurements_Voltagebinput | DC-Eingangsspannung | V |
| inverter1DailyYield | Tagesertrag | smainv1roof_Tagesertrag | Tagesertrag | kWh |
| inverter1GridContactor | Netzrelais | smainv1roof_NetzrelaisSchutz | Netzrelais/Schütz | — |
| inverter1InternalTemperature | STP-8.0 Temperatur | smainv1roof_Interne_Temperatur | Interne Temperatur | °C |
| inverter1PowerA | DC Leistung Eingang SO | smainv1roof_Measurements_Powerainput | DC-Eingangsleistung | W |
| inverter1PowerB | DC Leistung Eingang NW | smainv1roof_Measurements_Powerbinput | DC-Eingangsleistung | W |
| inverter1PowerDrawn | Leistung Bezug | smainv1roof_Bezogene_Leistung | Bezogene Leistung | W |
| inverter1PowerGridFeedIn | Leistung Einspeisung | smainv1roof_Netzeinspeiseleistung | Netzeinspeiseleistung | W |
| inverter1Status | Geräte Status | smainv1roof_Zustand | Zustand | — |
| inverter1TotalYield | Gesamtertrag | smainv1roof_Gesamtertrag | Gesamtertrag | kWh |

### Inverter 2 battery

| Old Item | Old label | New Item | New label | Unit |
| --- | --- | --- | --- | --- |
| inverter2BatCapacity | PV-Speicher Batteriekapazität | smainv2battery_Batteriekapazitat | Batteriekapazität | % |
| inverter2BatStateCharge | PV-Speicher Batterieladung | smainv2battery_Batterieladezustand | Batterieladezustand | % |
| inverter2BatTemp | BYD Batterie Temperatur | smainv2battery_Batterietemperatur | Batterietemperatur | °C |
| inverter2BatteryStatus | Batterie Status | smainv2battery_Batteriestatus | Batteriestatus | — |
| inverter2DayYield | Tagesverbrauch | smainv2battery_Tagesertrag | Tagesertrag | kWh |
| inverter2GridRelay | Netzrelais | smainv2battery_Netzschaltzustand | Netzschaltzustand | — |
| inverter2InternalTemperature | SBS-3.7 Temperatur | smainv2battery_Gehausetemperatur | Gehäusetemperatur | °C |
| inverter2PreBatCharge | Momentane Batterieladung | smainv2battery_Batterieladeleistung | Batterieladeleistung | W |
| inverter2PreBatDischarge | Momentane Batterieentladung | smainv2battery_Batterieentladeleistung | Batterieentladeleistung | W |
| inverter2Status | Geräte Status | smainv2battery_Geratezustand | Gerätezustand | — |
| inverter2TotalYield | Gesamtertrag | smainv2battery_Gesamtertrag | Gesamtertrag | kWh |

### Inverter 3 carport

| Old Item | Old label | New Item | New label | Unit |
| --- | --- | --- | --- | --- |
| inverter3ActivePower | PV Produktion | smainv3carport_Leistung | Leistung | W |
| inverter3DC1Cur_input | DC Strom Eingang SW | smainv3carport_DCEingangsstrom | DC-Eingangsstrom | A |
| inverter3DC1Volt_input | DC Spannung Eingang SW | smainv3carport_DCEingangsspannung | DC-Eingangsspannung | V |
| inverter3DailyYield | Tagesertrag | smainv3carport_Tagesertrag | Tagesertrag | kWh |
| inverter3GridContactor | Netzrelais | smainv3carport_NetzrelaisSchutz | Netzrelais/Schütz | — |
| inverter3InternalTemperature | SB-40 Temperatur | smainv3carport_Interne_Temperatur | Interne Temperatur | °C |
| inverter3PowerA | DC Leistung Eingang SW | smainv3carport_DCEingangsleistung | DC-Eingangsleistung | W |
| inverter3Status | Geräte Status | smainv3carport_Zustand | Zustand | — |
| inverter3TotalYield | Gesamtertrag | smainv3carport_Gesamtertrag | Gesamtertrag | kWh |

## New Items without a recorded old counterpart

These are observed Items, not a complete list of every property supported by the
current bridge. The household daily Item without Wallbox was additionally observed on 2026-10-15.
Other later additions and Items outside the recorded scope require
an updated inventory before claiming current installation completeness.

| Old Item | Old label | New Item | New label | Unit |
| --- | --- | --- | --- | --- |
| — | — | smahomemanager_Anlagenstatus | Anlagenstatus | — |
| — | — | smahomemanager_Anlagenzeit | Anlagenzeit | s |
| — | — | smahomemanager_Anlagenzeit_DateTime | Anlagenzeit (Datum/Uhrzeit) | — |
| — | — | smahomemanager_Verfugbarkeit_der_Datenquelle | Verfügbarkeit der Datenquelle | — |
| — | — | smainv1roof_Netzfrequenz | Netzfrequenz | Hz |
| — | — | smainv1roof_Netzstrom_Phase_L1 | Netzstrom Phase L1 | A |
| — | — | smainv1roof_Netzstrom_Phase_L2 | Netzstrom Phase L2 | A |
| — | — | smainv1roof_Netzstrom_Phase_L3 | Netzstrom Phase L3 | A |
| — | — | smainv1roof_Verfugbarkeit_der_Datenquelle | Verfügbarkeit der Datenquelle | — |
| — | — | smainv2battery_BatterieEntladeenergie | Batterie-Entladeenergie | kWh |
| — | — | smainv2battery_BatterieLadeenergie | Batterie-Ladeenergie | kWh |
| — | — | smainv2battery_Batteriespannung | Batteriespannung | V |
| — | — | smainv2battery_Batteriestrom | Batteriestrom | A |
| — | — | smainv2battery_Leistung | Leistung | W |
| — | — | smainv2battery_Netzfrequenz | Netzfrequenz | Hz |
| — | — | smainv2battery_Netzstrom_Phase_L1 | Netzstrom Phase L1 | A |
| — | — | smainv2battery_Verfugbarkeit_der_Datenquelle | Verfügbarkeit der Datenquelle | — |
| — | — | smainv3carport_Bezogene_Leistung | Bezogene Leistung | W |
| — | — | smainv3carport_DCLeistung_Eingang_B | DC-Leistung Eingang B | W |
| — | — | smainv3carport_DCSpannung_Eingang_B | DC-Spannung Eingang B | V |
| — | — | smainv3carport_DCStrom_Eingang_B | DC-Strom Eingang B | A |
| — | — | smainv3carport_Leistung_Phase_L1 | Leistung Phase L1 | W |
| — | — | smainv3carport_Leistung_Phase_L2 | Leistung Phase L2 | W |
| — | — | smainv3carport_Leistung_Phase_L3 | Leistung Phase L3 | W |
| — | — | smainv3carport_Netzeinspeiseleistung | Netzeinspeiseleistung | W |
| — | — | smainv3carport_Netzfrequenz | Netzfrequenz | Hz |
| — | — | smainv3carport_Netzspannung_Phase_L1 | Netzspannung Phase L1 | V |
| — | — | smainv3carport_Netzspannung_Phase_L2 | Netzspannung Phase L2 | V |
| — | — | smainv3carport_Netzspannung_Phase_L3 | Netzspannung Phase L3 | V |
| — | — | smainv3carport_Netzstrom_Phase_L2 | Netzstrom Phase L2 | A |
| — | — | smainv3carport_Netzstrom_Phase_L3 | Netzstrom Phase L3 | A |
| — | — | smainv3carport_Verfugbarkeit_der_Datenquelle | Verfügbarkeit der Datenquelle | — |
| — | — | smaplant_HausTagesverbrauch_ohne_Wallbox | Haus-Tagesverbrauch ohne Wallbox | kWh |

This daily household balance excluding Wallbox energy is not matched to the
seven-day average, which excludes entire charging days and averages remaining days.

## Comparison conditions

- Home Manager cumulative energy may contain legacy offsets. Align interval
  deltas or verified initial values before comparing absolute levels.
- Legacy daily energy uses power integrals; new household/grid day values use
  counters. Compare equal time coverage. Initial partial days and energy-baseline
  resets do not represent a complete calendar day.
- Status Items require state/MAP comparison rather than numeric curves.
- `inverter2DayYield` has the old label Tagesverbrauch and the new label
  Tagesertrag. Preserve the register association; the label alone does not settle
  its physical interpretation.
- `smahomemanager_Anlagenzeit_DateTime` was recorded against numeric `planttime`.
  Its link needs review against `planttimeiso`; no correction is included here.

## Sources

- [Plant Item and link verification on 2026-10-15](plant-item-links-2026-10-15.csv)
- [Item inventory](pv-item-inventory-2026-10-14.csv)
- [Homie link inventory](pv-homie-links-2026-10-14.csv)
- [Original comparison manifest](pv-comparison-2026-10-14.csv)
- [Rules](pv-rule-inventory-2026-10-14.csv) and [queries](pv-query-inventory-2026-10-14.csv)
- [Migration decisions](MIGRATION.md) and [plant design](PV_AGGREGATION_DESIGN.md)
- Official openHAB [Items](https://www.openhab.org/docs/configuration/items.html)
  and [Homie binding](https://www.openhab.org/addons/bindings/homie/) documentation

## Home Manager power target rename, 2026-10-15

The maintained CSV targets now use measurements/powerdrawn for the existing
smahomemanager_Netzbezugsleistung Item and measurements/powergridfeedin for
smahomemanager_Einspeiseleistung. The recorded old live links used powerimport
and powerexport. This is a documented migration target, not a new observation
or a performed live relink; preserve these Item identities and histories.

## Canonical naming targets and energy corrections

The maintained CSV targets incorporate the approved 2026-10-15 renames from
[the full map](topic-renames-2026-10-15.csv), including battery/phase/day-yield and
house-power names. This is a migration target, not performed live relinking.
Home Manager energyimport/energyexport retain their IDs and now include configured
private offsets; remove equivalent legacy link/rule corrections before switching
to these corrected totals. Keep existing Item names, units, rules and history.
