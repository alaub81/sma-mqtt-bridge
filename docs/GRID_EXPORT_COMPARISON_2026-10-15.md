# Grid-export source comparison, 2026-10-15

## Read-only evidence

Andreas requested comparison before replacing production-based remuneration with
actual grid-export remuneration. He then explicitly selected one common tariff
for all exported electricity, with Home Manager preferred as the source.

MQTT Explorer showed the inverter grid-feed-in properties in W, whereas Home
Manager also exposes a cumulative grid-energy export counter in kWh. A bounded
read-only comparison around 16:03:43–16:04:44 Europe/Berlin used the configured,
independently enabled inverter1, inverter3 and Home Manager endpoints. Existing
profile identity guards remained active. Only selected existing measurements and
the previously audited read-only inverter candidate 30583 were read with FC04.
The candidate was not added to runtime profiles or MQTT. No credentials, endpoints,
serials, raw frames or private offsets/tariffs are reproduced here.

Both PV inverters returned exactly the same 30583 U32 counter in all five
inverter samples, including a shared increment of one raw unit between samples.
In the final comparison, dividing either raw counter by 1000 exactly matched
the Home Manager's existing kWh export reading. This strongly supports duplicate
plant grid-export views, rather than per-inverter export allocations, for this
installation. It is not generic unit/profile acceptance for every SMA firmware;
the inverter1 source catalog does not explicitly declare its unit.

The inverters' own production counters were different, and their active powers
were approximately 1.4 and 1.3 kW. Inverter grid-export power was only 0–14 W in
the initial samples. The final inverter readings were both 2 W; Home Manager
returned 23 W about four seconds later. These sequential values near the control
boundary are not a synchronized power-equivalence test. Do not add their duplicate
grid readings or infer per-inverter exported-energy shares from them.

The first Home Manager sample in each initial round returned only its highest
priority due poller (import power); those rounds do not establish a simultaneous
Home Manager counter comparison. A final identity-checked, paced targeted read
explicitly retrieved export energy, export power and import power. No fictional
missing Home Manager counter value is substituted for the initial partial reads.

## Resulting calculation

Use the Home Manager and its verified `energyexport` mapping. Calculate the
plant `grid/totalearnings` property as `(raw export kWh + configured historical export offset kWh) × common
tariff`. Do not sum inverter grid views, use PV lifetime production or automatically
fail over to another source. Home Manager input loss makes remuneration unavailable.

Following the subsequent offset request, the private Home Manager export offset
corrects its published cumulative total and feeds remuneration exactly once. It
does not modify raw readings, daily baselines or stored averages. The previous individual
inverter tariff settings remain accepted for compatibility but are ignored. An
explicit common tariff, including zero, is required to publish the channel.
The currency label remains configurable. Changing source, tariff or offset does
not reconstruct tariff periods or repair previous monetary history automatically.

The source comparison performed no device settings, MQTT publications, portal
requests, configuration writes, state-volume changes or service restarts. New
calculation deployment and monetary value acceptance remain separate tasks.
