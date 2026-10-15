# Battery counter AC/DC comparison, 2026-10-15

## Result and scope

Both battery energy counters are strongly supported as **AC-side counters for the
observed Storage installation**. Their changes match integrated inverter AC power
in both directions; the battery voltage/current product differs by about 13%.
This validates the installation's existing provisional AC accounting assumption.
It is an empirical boundary comparison, not calibrated metering certification,
proof for every firmware/model, or a full household-energy acceptance.

Read-only queries ran in the user's authenticated InfluxDB Data Explorer session.
No device command, database write, persistence/Item change, runtime-profile change,
configuration change or state-volume modification was performed. Only aggregate
results are recorded here; credentials, endpoints, absolute counter readings and
raw time series are excluded.

## Sources and units

| Existing Item | Register | Quantity |
| --- | --: | --- |
| smainv2battery_Leistung | 30775 | Signed inverter AC power, W |
| smainv2battery_Batteriestrom | 30843 | Signed battery DC current, A |
| smainv2battery_Batteriespannung | 30851 | Battery DC voltage, V |
| smainv2battery_BatterieLadeenergie | 31397 | Charge counter, published kWh |
| smainv2battery_BatterieEntladeenergie | 31401 | Discharge counter, published kWh |

All five series now contain data, unlike the 2026-10-14 inventory. The counter
scales remain those in [register validation](REGISTER_VALIDATION.md), including
Wh-to-kWh conversion for 31397/31401. The signed power/current observations are
positive during the selected discharge and negative during the selected charge.

## Aligned comparison

Window boundaries below are the original first/last timestamps of the relevant
energy counter observations, not rounded display times or arbitrary graph bins.
Times use Europe/Berlin (UTC+02:00 on these dates).

| Phase | Interval | Counter change | Integrated AC | Approximate DC, U × I |
| --- | --- | --: | --: | --: |
| Discharge | Oct 14 23:00:26.445 – Oct 15 05:59:27.366 | 1.711000 kWh | 1.711919 kWh | 1.929356 kWh |
| Charge | Oct 15 08:30:46.209 – 08:48:47.647 | 0.106000 kWh | 0.106640 kWh | 0.092495 kWh |

Relative to the counter change, the AC difference is approximately +0.054% during
discharge and +0.603% during charge. The DC differences are +12.762% and -12.740%.
No counter decrease/reset was observed in the evaluated reconstruction. The
charging window is shorter and lower energy, but its AC/DC separation is much
larger than the AC discrepancy and the counters' 1 Wh resolution.

An initial independent partition into 30-minute windows also showed repeated
AC agreement throughout the overnight discharge. The final contiguous interval
avoids omitting the boundaries between those windows.

## Method and limitations

1. Read original counter endpoints and subtract last minus first, separately for
   charge and discharge. Keep their actual timestamps for the power comparison.
2. Independently integrate original AC samples over those ranges with Flux
   `integral(unit: 1h)`, dividing W·h by 1000. Reverse the sign for charge.
   The [official integral reference](https://docs.influxdata.com/flux/v0/stdlib/universe/integral/)
   documents time-based integration of successive non-null samples. Only in-range
   samples are included, so their endpoints can differ by a few seconds from the
   counter endpoints; no exact sub-sample metrology is claimed.
3. For the DC cross-check, reconstruct all five series on a 5-second last-value
   grid, carrying previous observations forward after the first available sample.
   Multiply the corresponding voltage and current, then integrate directionally
   with trapezoids. Restrict to the counter windows. Grid endpoint rounding omits
   a few seconds; use the **original counter endpoint difference**, not a stale
   resampled counter value at an intermediate grid point.
4. Check original sample counts/times separately. The uniform grid itself does
   not establish original recording continuity. Original AC/current gaps are at
   most about 35.1 seconds in discharge and 11.1 seconds in charge. Voltage is
   sparser: maximum recorded gaps are about 667.8 and 30.1 seconds respectively.
   Previous-value voltage reconstruction is therefore an approximation. Counter
   changes arrive roughly every minute while active. Unchanged values/restore
   records must not be mistaken for additional measurements or resets.

The small AC discrepancies can include polling offsets, sample interpolation and
counter quantization. The DC result is approximate, but the opposing charge/
discharge differences and repeated AC agreement provide strong boundary evidence.
These intervals do not measure round-trip efficiency: they cover unequal energy
amounts and do not establish matching state of charge. Fine PV counter precision,
whole-day household comparisons and midnight behavior remain separate questions.

## Configuration follow-up

The bundled profile now declares `energyBoundary=ac` with this comparison as its
energy evidence. The original investigation did not change the running system.
In the subsequent implementation Andreas explicitly accepts new energy baselines.
The full-profile signature changes, so archive only the old energy ledger with
the [offline reset procedure](CONFIGURATION.md#explicit-energy-baseline-restart-after-profile-changes).
Remove the unnecessary AC-assumption override and reconcile host profile copies.
Preserve the backup, topic manifest, journals, entire state volume and histories.
Loading the new build then reports ac and starts new day accounts; no metadata-only
compatibility migration or automatic reset of a mismatched ledger is performed.
