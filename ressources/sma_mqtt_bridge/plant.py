"""Plant sums and counter balances from current local sources, without device I/O."""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from .energy_balances import EnergyBalances
from .energy_profile_compat import released_energy_layout
from .errors import ConfigError
from .model import Property, SampleValues, SourceState, number, payload
from .plant_debug import PlantDebug
from .plant_price import PlantPrice
from .plant_profiles import FIELDS

WALLBOX_OUTPUTS = {
    "wallbox/daily-consumption": "measurements/daily-consumption",
    "diagnostics/wallbox-day-status": "diagnostics/wallbox-day-status",
    "diagnostics/wallbox-energy-time": "diagnostics/wallbox-energy-time",
}


@dataclass(frozen=True)
class Input:
    source: str
    key: str

    @property
    def identity(self):
        return self.source + "/" + self.key


def energy_binding_profile(profile):
    """Preserve energy identity across approved sentinel and exact telemetry additions."""
    if profile is None:
        return None
    return released_energy_layout(
        profile
        | {
            "properties": [
                {
                    key: value
                    for key, value in prop.items()
                    if key not in ("invalidAsZero", "invalidAsZeroWhen")
                }
                for prop in profile["properties"]
            ]
        }
    )


def plant_plan(config):
    """Validate contribution inventories before network connections."""
    from .adapters.home_manager_modbus import HomeManagerModbusReader
    from .adapters.meter import MeterReader
    from .adapters.modbus import ModbusReader

    settings = config.plant
    if config.feed_in_tariff_configured and settings.grid_source != "home-manager":
        raise ConfigError("Feed-in remuneration requires the Home Manager grid source")
    if (
        not 0 < settings.boundary_tolerance_seconds <= 900
        or not 0 < settings.max_skew_seconds <= 3600
    ):
        raise ConfigError("Plant boundary tolerance must be <= 900 s and sample skew <= 3600 s")
    groups = {"pv": [], "battery": []}
    identities = []
    grid = None
    boundaries = []
    for device in config.inverters:
        if not device.enabled:
            continue
        profile = config.profiles[device.id]
        mapping = profile.get("plant", {})
        selected = (
            ("pv", "battery")
            if device.role == "hybrid"
            else (device.role,)
            if device.role != "none"
            else ()
        )
        if device.role == "hybrid" and not mapping.get("hybridSeparated"):
            raise ConfigError("Hybrid role requires verified separated profile contributions")
        reader = ModbusReader(device, profile, device.id in config.interval_overrides)
        available = {p.key for p in reader.properties}
        wanted = set(selected) | ({"grid"} if settings.grid_source == device.id else set())
        selected_refs = [
            mapping[group][k] for group in wanted if group in mapping for k in FIELDS[group]
        ]
        if len(selected_refs) != len(set(selected_refs)):
            raise ConfigError("Selected plant contribution groups overlap")
        for group in wanted:
            if group not in mapping or any(
                mapping[group][k] not in available for k in FIELDS[group]
            ):
                raise ConfigError("Plant role references missing or filtered profile contributions")
            refs = {k: Input(device.id, mapping[group][k]) for k in FIELDS[group]}
            if group == "grid":
                grid = refs
            else:
                groups[group].append(refs)
                if group == "battery":
                    boundaries.append(mapping[group]["energyBoundary"])
        if wanted:
            identities.append(
                {
                    "source": device.id,
                    "host": device.host,
                    "port": device.port,
                    "unit": device.unit_id,
                    "expectedSerial": device.expected_serial,
                    "role": device.role,
                    "profile": energy_binding_profile(profile),
                }
            )
    if settings.grid_source == "home-manager" and config.home_manager.enabled:
        grid = {
            key: Input("home-manager", "measurements/" + value)
            for key, value in {
                "powerimport": "power-import",
                "powerexport": "power-export",
                "energyimport": "energy-import",
                "energyexport": "energy-export",
            }.items()
        }
        hm = config.home_manager
        hm_profile = config.profiles.get("home-manager")
        reader = (
            HomeManagerModbusReader(hm, hm_profile, "home-manager" in config.interval_overrides)
            if hm.transport == "modbus-tcp"
            else MeterReader(hm)
        )
        available = {p.key: p for p in reader.properties}
        if any(
            ref.key not in available
            or available[ref.key].unit != FIELDS["grid"][metric]
            or available[ref.key].datatype not in ("integer", "float")
            for metric, ref in grid.items()
        ):
            raise ConfigError("Plant grid source requires matching numeric power and energy units")
        identities.append(
            {
                "source": "home-manager",
                "serial": config.home_manager.serial,
                "host": config.home_manager.host,
                "transport": config.home_manager.transport,
                "profile": energy_binding_profile(hm_profile),
            }
        )
    if grid is None:
        raise ConfigError(
            "Plant requires an enabled explicitly selected grid source with power and energy mappings"
        )
    if len(set(boundaries)) > 1:
        raise ConfigError("Battery contribution energy boundaries must match")
    signature = hashlib.sha256(
        json.dumps(
            {
                "identities": identities,
                "grid": settings.grid_source,
                "timezone": config.runtime.timezone,
                "initial": settings.initial_consumption_kwh,
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    return groups, grid, boundaries[0] if boundaries else "none", signature


class PlantState(SourceState):
    def __init__(self, *args, publish_diagnostics=True, **kwargs):
        self.publish_diagnostics = publish_diagnostics
        self.deadlines = {}
        self.sources = {}
        self.guards = {}
        self.max_skew = 0
        self.expected_units = {}
        super().__init__(*args, **kwargs)

    @property
    def published_properties(self):
        if self.publish_diagnostics:
            return self.properties
        return tuple(p for p in self.properties if p.channel_group != "diagnostics")

    def fresh_values(self, now=None):
        now = time.monotonic() if now is None else now
        available = {
            key: source.fresh_values(now) if not source.error else {}
            for key, source in self.sources.items()
        }
        return {
            key: value
            for key, value in super().fresh_values(now).items()
            if now <= self.deadlines.get(key, now) and self.inputs_valid(key, available)
        }

    def inputs_valid(self, key, available):
        inputs = self.guards.get(key, ())
        if any(ref.key not in available.get(ref.source, {}) for ref in inputs):
            return False
        if any(
            self.sources[ref.source].property_index()[ref.key].unit != self.expected_units[ref]
            or self.sources[ref.source].property_index()[ref.key].datatype
            not in ("integer", "float")
            for ref in inputs
        ):
            return False
        stamps = [self.sources[ref.source].values[ref.key][1] for ref in inputs]
        return not stamps or max(stamps) - min(stamps) <= self.max_skew


class PlantEngine:
    def __init__(self, config, states):
        self.config = config
        self.debug = PlantDebug(
            config.plant.debug_interval_seconds if config.plant.debug_enabled else 0
        )
        self.sources = {s.id: s for s in states}
        self.groups, self.grid, self.boundary, signature = plant_plan(config)
        if self.boundary == "unverified" and config.plant.assume_ac_battery_energy:
            self.boundary = "assumed-ac"
        self.zone = ZoneInfo(config.runtime.timezone)
        self.ledger = EnergyBalances(config, signature, self.zone)
        self.changed = asyncio.Event()
        self.price = PlantPrice(config, self.changed)
        self.feed_in_price = PlantPrice(config, self.changed, feed_in=True)
        self.nonnegative = {
            ref
            for group in self.groups.values()
            for member in group
            for metric, ref in member.items()
            if metric != "activepower"
        }
        self.nonnegative.update(self.grid.values())
        self.expected_units = {
            ref: FIELDS[group][metric]
            for group, members in self.groups.items()
            for member in members
            for metric, ref in member.items()
        }
        self.expected_units.update(
            {ref: FIELDS["grid"][metric] for metric, ref in self.grid.items()}
        )
        self.wallbox = (
            Input("api", "measurements/total-energy") if config.echarger.enabled else None
        )
        if self.wallbox is not None:
            self.expected_units[self.wallbox] = "kWh"
            self.nonnegative.add(self.wallbox)
        self.recipes = {}
        self.last_packet = None
        self.last_wallbox_packet = None
        self.account_frames = {}
        self.committed_times = {}
        self.add_sums()
        self.add_house_power()
        self.recipes["pv/total-earnings"] = (
            "Total feed-in remuneration",
            config.plant.currency,
            ((self.grid["energyexport"], Decimal(1)),),
        )
        properties = [
            Property(
                *key.split("/"),
                label,
                unit=unit,
                required_for_ready=key == "house/consumption",
                channel_group="basic",
            )
            for key, (label, unit, _) in self.recipes.items()
        ]
        self.daily_tariffs = {}
        self.daily_tariffs["grid/daily-costs"] = ("import", None, "Daily grid import costs")
        self.daily_tariffs["grid/daily-earnings"] = ("export", None, "Daily feed-in remuneration")
        properties += [
            Property(*key.split("/"), label, unit=config.plant.currency, channel_group="basic")
            for key, (_, _, label) in self.daily_tariffs.items()
        ]
        properties += [
            Property(
                "house",
                "average-daily-consumption",
                "Seven-day average house consumption",
                unit="kWh",
                channel_group="basic",
            ),
            Property(
                "diagnostics",
                "average-day-status",
                "Seven-day coverage",
                "string",
                channel_group="basic",
            ),
            Property(
                "grid",
                "daily-energy-import",
                "Daily grid import",
                unit="kWh",
                channel_group="basic",
            ),
            Property(
                "grid",
                "daily-energy-export",
                "Daily grid export",
                unit="kWh",
                channel_group="basic",
            ),
            Property(
                "house",
                "daily-consumption",
                "Daily house consumption",
                unit="kWh",
                channel_group="basic",
            ),
            Property(
                "diagnostics",
                "import-day-status",
                "Import day coverage",
                "string",
                channel_group="basic",
            ),
            Property(
                "diagnostics",
                "export-day-status",
                "Export day coverage",
                "string",
                channel_group="basic",
            ),
            Property(
                "diagnostics",
                "house-energy-status",
                "House energy coverage",
                "string",
                channel_group="basic",
            ),
            Property(
                "diagnostics",
                "local-date",
                "Local accounting date",
                "string",
                channel_group="diagnostics",
            ),
            Property(
                "diagnostics",
                "battery-energy-boundary",
                "Battery energy boundary",
                "string",
                channel_group="diagnostics",
            ),
            Property(
                "diagnostics",
                "power-input-status",
                "Power input availability",
                "string",
                channel_group="diagnostics",
            ),
        ]
        if self.wallbox is not None:
            properties += [
                Property(
                    "house",
                    "average-daily-consumption-without-wallbox",
                    "Seven-day average house consumption without wallbox",
                    unit="kWh",
                    channel_group="basic",
                ),
                Property(
                    "diagnostics",
                    "average-without-wallbox-day-status",
                    "Seven-day coverage without wallbox",
                    "string",
                    channel_group="basic",
                ),
                Property(
                    "house",
                    "daily-consumption-without-wallbox",
                    "Daily house consumption without wallbox",
                    unit="kWh",
                    channel_group="basic",
                ),
                Property(
                    "diagnostics",
                    "house-without-wallbox-day-status",
                    "House without wallbox day coverage",
                    "string",
                    channel_group="basic",
                ),
                Property(
                    "diagnostics",
                    "housewithoutwallbox-energy-time",
                    "Energy snapshot time (UTC)",
                    "string",
                    channel_group="diagnostics",
                ),
            ]
        properties += [
            Property(
                "diagnostics",
                name + "-energy-time",
                "Energy snapshot time (UTC)",
                "string",
                channel_group="diagnostics",
            )
            for name in ("import", "export", "house")
        ]
        properties.append(
            Property(
                "diagnostics",
                "house-energy-start",
                "House energy start (UTC)",
                "string",
                channel_group="diagnostics",
            )
        )
        properties.append(
            Property(
                "diagnostics",
                "valid-properties",
                "Available plant properties",
                "string",
                channel_group="diagnostics",
            )
        )
        # Exact input deadlines below also cover slow pollers without renewing their ages.
        ttl = 2 * config.plant.checkpoint_interval_seconds + max(
            [s.stale_seconds for s in states]
            + [p.stale_seconds or 0 for s in states for p in s.properties]
            + [1]
        )
        self.state = PlantState(
            "plant",
            config.plant.homie_id,
            tuple(properties),
            ttl,
            diagnostics_enabled=config.plant.diagnostics_enabled,
            publish_diagnostics=config.plant.diagnostics_enabled,
        )
        self.all_properties = self.state.properties
        self.update_tariff_inventory()
        self.wallbox_state = None
        if self.wallbox is not None:
            self.wallbox_state = PlantState(
                "wallbox-day",
                config.echarger.homie_id,
                (
                    Property(
                        "measurements",
                        "daily-consumption",
                        "Daily wallbox consumption",
                        unit="kWh",
                        channel_group="basic",
                    ),
                    Property(
                        "diagnostics",
                        "wallbox-day-status",
                        "Wallbox day coverage",
                        "string",
                        channel_group="basic",
                    ),
                    Property(
                        "diagnostics",
                        "wallbox-energy-time",
                        "Energy snapshot time (UTC)",
                        "string",
                        channel_group="diagnostics",
                    ),
                ),
                ttl,
                diagnostics_enabled=False,
                publish_diagnostics=config.echarger.diagnostics_enabled,
                contributes_availability=False,
            )
            self.wallbox_state.max_payload_bytes = config.runtime.max_payload_bytes
            self.wallbox_state.max_skew = config.plant.max_skew_seconds
            self.wallbox_state.expected_units = self.expected_units
            self.wallbox_state.sources = {"api": self.sources["api"]}
            self.wallbox_state.guards["measurements/daily-consumption"] = (self.wallbox,)
        self.state.max_payload_bytes = config.runtime.max_payload_bytes
        self.state.max_skew = config.plant.max_skew_seconds
        self.state.expected_units = self.expected_units
        self.state.guards = {
            key: tuple(ref for ref, _ in inputs) for key, (_, _, inputs) in self.recipes.items()
        }
        self.state.guards["grid/daily-energy-import"] = (self.grid["energyimport"],)
        self.state.guards["grid/daily-energy-export"] = (self.grid["energyexport"],)
        for key, (direction, _, _) in self.daily_tariffs.items():
            self.state.guards[key] = (self.grid["energy" + direction],)
        energy_inputs = [m["totalyield"] for m in self.groups["pv"]]
        energy_inputs += [self.grid["energyimport"], self.grid["energyexport"]]
        energy_inputs += [
            m[k]
            for m in self.groups["battery"]
            for k in ("batterychargeenergy", "batterydischargeenergy")
        ]
        self.state.guards["house/daily-consumption"] = tuple(energy_inputs)
        if self.wallbox is not None:
            prop = self.sources["api"].property_index().get(self.wallbox.key)
            if prop is None or prop.unit != "kWh" or prop.datatype not in ("integer", "float"):
                raise ConfigError(
                    "Plant wallbox requires the local API total energy counter in kWh"
                )
            self.state.guards["house/daily-consumption-without-wallbox"] = (
                *energy_inputs,
                self.wallbox,
            )
        selected_sources = {ref.source for refs in self.state.guards.values() for ref in refs}
        self.state.sources = {source: self.sources[source] for source in selected_sources}

    @property
    def output_states(self):
        return (self.state, self.price.state, self.feed_in_price.state) + (
            (self.wallbox_state,) if self.wallbox_state is not None else ()
        )

    def update_tariff_inventory(self):
        """Expose remuneration only once a configured or saved tariff exists."""
        properties = tuple(
            prop
            for prop in self.all_properties
            if self.feed_in_price.price is not None
            or prop.key not in ("pv/total-earnings", "grid/daily-earnings")
        )
        if properties != self.state.properties:
            self.state.properties = properties

    def update_wallbox_output(self, packet, observed, deadlines, now, wall):
        """Publish the same committed account through the existing charger device."""
        if self.wallbox_state is None:
            return
        values = {new: packet.pop(old, None) for old, new in WALLBOX_OUTPUTS.items()}
        ages = {new: observed.pop(old) for old, new in WALLBOX_OUTPUTS.items() if old in observed}
        expires = {
            new: deadlines.pop(old) for old, new in WALLBOX_OUTPUTS.items() if old in deadlines
        }
        snapshot = (values, ages, expires)
        if snapshot != self.last_wallbox_packet:
            self.wallbox_state.deadlines = expires
            self.wallbox_state.update(
                SampleValues(values, ages), now=now, timestamp=wall.isoformat()
            )
            self.last_wallbox_packet = snapshot

    def add_sums(self):
        labels = {
            "activepower": "Total PV active power",
            "dayyield": "Total PV daily yield",
            "totalyield": "Total PV lifetime yield",
            "presbatcharge": "Total battery charging power",
            "presbattdischarge": "Total battery discharging power",
            "batterychargeenergy": "Total battery charge energy",
            "batterydischargeenergy": "Total battery discharge energy",
        }
        for group, members in self.groups.items():
            if len(members) < 2:
                continue
            for metric, unit in FIELDS[group].items():
                prop = "total" + metric if metric != "totalyield" else metric
                self.recipes[group + "/" + prop] = (
                    labels[metric],
                    unit,
                    tuple((m[metric], 1) for m in members),
                )

    def add_house_power(self):
        inputs = [(m["activepower"], 1) for m in self.groups["pv"]]
        inputs += [(self.grid["powerimport"], 1), (self.grid["powerexport"], -1)]
        for member in self.groups["battery"]:
            inputs += [(member["presbattdischarge"], 1), (member["presbatcharge"], -1)]
        self.recipes["house/consumption"] = ("Calculated house consumption", "W", tuple(inputs))
        charging = {m["presbatcharge"] for m in self.groups["battery"]}
        self.recipes["house/consumptionwithcharging"] = (
            "House consumption including battery charging",
            "W",
            tuple((ref, 0 if ref in charging else sign) for ref, sign in inputs),
        )

    def frame(self, inputs, now):
        values, stamps, expires, hardware = {}, [], [], []
        for ref, sign in inputs:
            source = self.sources[ref.source]
            if source.error:
                return None
            fresh = source.fresh_values(now)
            value = number(fresh.get(ref.key))
            if value is None or (ref in self.nonnegative and value < 0):
                return None
            prop = source.property_index().get(ref.key)
            received = source.values[ref.key][1]
            if (
                prop is None
                or prop.unit != self.expected_units[ref]
                or prop.datatype not in ("integer", "float")
            ):
                return None
            values[ref.identity] = value * sign
            stamps.append(received)
            expires.append(
                received
                + (prop.stale_seconds if prop.stale_seconds is not None else source.stale_seconds)
            )
            token = getattr(source, "identity_fingerprint", "")
            if ref.source == "home-manager":
                token = hashlib.sha256(self.config.home_manager.serial.encode()).hexdigest()
            elif ref.source == "api" and token:
                token = hashlib.sha256(
                    json.dumps(
                        (token, self.config.echarger.host, self.config.echarger.port)
                    ).encode()
                ).hexdigest()
            hardware.append((ref.source, token))
        if max(stamps) - min(stamps) > self.config.plant.max_skew_seconds:
            return None
        fingerprint = hashlib.sha256(json.dumps(sorted(set(hardware))).encode()).hexdigest()
        return values, min(stamps), min(expires), fingerprint, max(stamps)

    def account(self, name, inputs, now, wall):
        frame = self.frame(tuple((ref, 1) for ref, _ in inputs), now)
        if frame is None:
            return None, None, "unavailable", None
        values, oldest, deadline, hardware, latest = frame
        signs = {ref.identity: Decimal(sign) for ref, sign in inputs}
        if any(v < 0 for v in values.values()):
            return None, None, "invalid", None
        if any(
            ref.source != "home-manager"
            and not getattr(self.sources[ref.source], "identity_fingerprint", "")
            for ref, _ in inputs
        ):
            return None, None, "init", None
        record = self.ledger.data["accounts"].get(name)
        # Never calibrate a replacement device or a regressed clock into old baselines.
        if record is not None and (
            record["hardware"] != hardware or set(record["last"]) != set(values)
        ):
            return None, None, "configuration-changed", None
        if record is not None and wall < datetime.fromisoformat(record["lastTime"]):
            return None, None, "clock-error", None
        paired = {}
        for ref, _ in inputs:
            source = self.sources[ref.source]
            pair = getattr(source, "legacy_counters", {}).get(ref.key)
            if pair is not None and pair[1] == source.values[ref.key][1]:
                paired[ref.identity] = pair[0]
        values = self.ledger.precise_values(values, paired)
        if values is None:
            return None, None, "unavailable", None
        oldest_wall = wall - timedelta(seconds=now - oldest)
        token = (
            tuple(sorted(values.items())),
            oldest,
            latest,
            hardware,
            wall.astimezone(self.zone).date(),
        )
        cached = self.account_frames.get(name)
        record = self.ledger.data["accounts"].get(name)
        if (
            cached is not None
            and cached[0] == token
            and cached[1][2] != "synchronizing"
            and (record is None or wall >= datetime.fromisoformat(record["lastTime"]))
        ):
            return cached[1]
        daily, total, status = self.ledger.observe(
            name,
            values,
            signs,
            hardware,
            wall,
            oldest_wall,
            sample_wall=wall - timedelta(seconds=now - latest),
            sample_times={
                ref.identity: wall
                - timedelta(seconds=now - self.sources[ref.source].values[ref.key][1])
                for ref, _ in inputs
            },
            daily_only=name in ("wallbox", "housewithoutwallbox"),
        )
        result = (daily, total, status, (oldest, deadline))
        self.account_frames[name] = (token, result)
        return result

    def power_input_problems(self, now):
        """Identify blocked power inputs without exposing device identities or addresses."""
        problems, stamps = {}, {}
        for ref, _ in self.recipes["house/consumption"][2]:
            source = self.sources[ref.source]
            prop = source.property_index().get(ref.key)
            if source.error:
                reason = "source-error"
            elif ref.key not in source.values:
                reason = "missing-or-invalid"
            elif (
                prop is None
                or prop.unit != self.expected_units[ref]
                or prop.datatype not in ("integer", "float")
            ):
                reason = "unit-or-type-mismatch"
            elif ref.key not in source.fresh_values(now):
                reason = "stale"
            elif (value := number(source.values[ref.key][0])) is None:
                reason = "invalid"
            elif ref in self.nonnegative and value < 0:
                reason = "negative-directional-flow"
            else:
                stamps[ref.identity] = source.values[ref.key][1]
                continue
            problems[ref.identity] = reason
        if stamps:
            latest = max(stamps.values())
            problems.update(
                {
                    key: "sample-skew"
                    for key, stamp in stamps.items()
                    if latest - stamp > self.state.max_skew
                }
            )
        return problems

    def refresh(self, now=None, wall=None):
        now = time.monotonic() if now is None else now
        wall = datetime.now(timezone.utc) if wall is None else wall
        self.update_tariff_inventory()
        packet = {p.key: None for p in self.state.properties}
        observed, deadlines = {}, {}
        accounts = {}
        power_problems = self.power_input_problems(now)
        for key, (_, _, inputs) in self.recipes.items():
            frame = self.frame(inputs, now)
            if frame is not None:
                values, oldest, deadline, _, _ = frame
                value = sum(values.values(), Decimal(0))
                if key == "pv/total-earnings":
                    if self.feed_in_price.price is None:
                        continue
                    ref = self.grid["energyexport"]
                    raw = number(self.sources[ref.source].values[ref.key][0])
                    corrected = raw + Decimal(
                        str(self.config.home_manager.energy_export_offset_kwh)
                    )
                    if corrected < 0:
                        continue
                    value = corrected * self.feed_in_price.price
                if value >= 0 or not (key.startswith("house/") or key == "pv/total-earnings"):
                    packet[key], observed[key], deadlines[key] = value, oldest, deadline
                else:
                    power_problems[key] = "negative-balance"
        packet["diagnostics/power-input-status"] = json.dumps(
            power_problems or {"status": "ready"}, sort_keys=True, separators=(",", ":")
        )
        for name, metric in (("import", "energyimport"), ("export", "energyexport")):
            daily, _, status, age = self.account(name, [(self.grid[metric], 1)], now, wall)
            key = "grid/daily-energy-" + name
            packet[key] = daily
            if age:
                observed[key], deadlines[key] = age
            packet["diagnostics/" + name + "-day-status"] = status
            accounts[name] = {key: daily}
        if self.boundary in ("ac", "assumed-ac", "none"):
            inputs = [(m["totalyield"], 1) for m in self.groups["pv"]]
            inputs += [(self.grid["energyimport"], 1), (self.grid["energyexport"], -1)]
            for member in self.groups["battery"]:
                inputs += [
                    (member["batterydischargeenergy"], 1),
                    (member["batterychargeenergy"], -1),
                ]
            daily, _, status, age = self.account("house", inputs, now, wall)
            packet["house/daily-consumption"] = daily
            accounts["house"] = {"house/daily-consumption": daily}
            if age:
                observed["house/daily-consumption"], deadlines["house/daily-consumption"] = age
        else:
            status = "unsupported-battery-boundary"
        packet["diagnostics/house-energy-status"] = status
        if self.wallbox is not None:
            daily, _, wallbox_status, age = self.account("wallbox", [(self.wallbox, 1)], now, wall)
            key = "wallbox/daily-consumption"
            packet[key] = daily
            accounts["wallbox"] = {key: daily}
            if age:
                observed[key], deadlines[key] = age
            packet["diagnostics/wallbox-day-status"] = wallbox_status
            if self.boundary in ("ac", "assumed-ac", "none"):
                # One counter vector gives both terms the same baseline and coverage.
                daily, _, without_status, age = self.account(
                    "housewithoutwallbox", [*inputs, (self.wallbox, -1)], now, wall
                )
                key = "house/daily-consumption-without-wallbox"
                packet[key] = daily
                accounts["housewithoutwallbox"] = {key: daily}
                if age:
                    observed[key], deadlines[key] = age
            else:
                without_status = "unsupported-battery-boundary"
            packet["diagnostics/house-without-wallbox-day-status"] = without_status
        packet["diagnostics/local-date"] = wall.astimezone(self.zone).date().isoformat()
        packet["diagnostics/battery-energy-boundary"] = self.boundary
        # A critical state transition is durable before its derived value reaches MQTT.
        self.ledger.persist(now)
        # Only durable energy snapshots are published; power sums remain immediate.
        for name, candidates in accounts.items():
            record = self.ledger.committed.get(name)
            if record is None:
                continue
            recorded_at = datetime.fromisoformat(record["oldestTime"])
            if self.committed_times.get(name, (None,))[0] != record["oldestTime"]:
                self.committed_times[name] = (
                    record["oldestTime"],
                    now - (wall - recorded_at).total_seconds(),
                )
            received = self.committed_times[name][1]
            packet["diagnostics/" + name + "-energy-time"] = record["oldestTime"]
            if name == "house":
                packet["diagnostics/house-energy-start"] = record["start"]
            for key, candidate in candidates.items():
                text = record["dailyValue"]
                packet[key] = Decimal(text) if candidate is not None and text is not None else None
                observed[key] = received
        # Value and lifetime come from the published durable day-energy snapshot.
        for key, (direction, _, _) in self.daily_tariffs.items():
            if key not in packet:
                continue
            energy_key = "grid/daily-energy-" + direction
            energy = packet[energy_key]
            rate = self.price.price if key == "grid/daily-costs" else self.feed_in_price.price
            packet[key] = energy * rate if energy is not None and rate is not None else None
            if energy_key in observed:
                observed[key] = observed[energy_key]
            if energy_key in deadlines:
                deadlines[key] = deadlines[energy_key]
        self.update_averages(packet, wall)
        self.update_wallbox_output(packet, observed, deadlines, now, wall)
        packet["diagnostics/valid-properties"] = ",".join(
            sorted(
                key.replace("-", "")
                for key, value in packet.items()
                if not key.startswith("diagnostics/")
                and value is not None
                and payload(value, self.state.property_index()[key], self.state.max_payload_bytes)
                is not None
                and 0 <= now - observed.get(key, now) <= self.state.stale_seconds
                and now <= deadlines.get(key, now)
            )
        )
        snapshot = (packet, observed, deadlines)
        if snapshot != self.last_packet:
            self.state.deadlines = deadlines
            self.state.update(SampleValues(packet, observed), now=now, timestamp=wall.isoformat())
            self.last_packet = snapshot
        self.debug.report(self, now, wall)

    def update_averages(self, packet, wall):
        """Average completed days, with a two-calendar-day startup preview."""
        today = wall.astimezone(self.zone).date()
        days = {(today - timedelta(days=i)).isoformat() for i in range(1, 8)}
        accounts = [("house", "house/average-daily-consumption", "average-day-status")]
        if self.wallbox is not None:
            accounts.append(
                (
                    "housewithoutwallbox",
                    "house/average-daily-consumption-without-wallbox",
                    "average-without-wallbox-day-status",
                )
            )
        for name, key, diagnostic in accounts:
            record = self.ledger.committed.get(name, {})
            history = record.get("history", {})
            valid = (
                not self.ledger.binding_changed
                and record.get("date", "9999-12-31") <= today.isoformat()
                and all(day < record["date"] for day in history)
            )
            values = [Decimal(history[d]) for d in days if d in history] if valid else []
            # Once history exists, current source availability cannot change the divisor.
            if valid and not values and record.get("date") == today.isoformat():
                start_day = datetime.fromisoformat(record["start"]).astimezone(self.zone).date()
                elapsed = (today - start_day).days
                startup = (elapsed == 0 and record.get("dailyStatus") == "partial") or (
                    elapsed == 1
                    and record.get("dailyStatus") == "complete"
                    and record.get("totalStatus") == "ready"
                )
                if startup:
                    inputs = [(m["totalyield"], 1) for m in self.groups["pv"]]
                    inputs += [(self.grid["energyimport"], 1), (self.grid["energyexport"], -1)]
                    for member in self.groups["battery"]:
                        inputs += [
                            (member["batterydischargeenergy"], 1),
                            (member["batterychargeenergy"], -1),
                        ]
                    if name == "housewithoutwallbox":
                        inputs.append((self.wallbox, -1))
                    signs = {ref.identity: Decimal(sign) for ref, sign in inputs}
                    if signs.keys() == record.get("last", {}).keys():
                        counters = {k: Decimal(v) for k, v in record["last"].items()}
                        current = self.ledger.balance(counters, signs, record["totalBase"])
                        daily = self.ledger.balance(counters, signs, record["dailyBase"])
                        if (
                            current.is_finite()
                            and current >= 0
                            and self.ledger.accept(daily, record.get("dailyValue"))
                        ):
                            values.append(current / (elapsed + 1))
            packet[key] = sum(values, Decimal(0)) / len(values) if values else None
            packet["diagnostics/" + diagnostic] = (
                "complete" if len(values) == 7 else "partial" if values else "insufficient-history"
            )

    async def run(self, stop):
        try:
            while not stop.is_set():
                self.changed.clear()
                self.refresh()
                waits = [asyncio.create_task(self.changed.wait()), asyncio.create_task(stop.wait())]
                try:
                    await asyncio.wait(
                        waits,
                        timeout=self.config.plant.update_interval_seconds,
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                finally:
                    for task in waits:
                        task.cancel()
                    await asyncio.gather(*waits, return_exceptions=True)
        finally:
            self.ledger.persist(time.monotonic(), force=True)
