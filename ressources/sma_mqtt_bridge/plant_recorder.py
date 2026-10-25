"""Bounded, opt-in calculation frames for power and accounting-time investigations."""

import json
import logging
from decimal import Decimal
from pathlib import Path

from .model import number
from .plant_debug import numeric
from .timestamp_diagnostics import TimestampDiagnostics

LOG = logging.getLogger(__name__)


class PlantRecorder(TimestampDiagnostics):
    """Reuse the restricted rotating JSONL writer, without timestamp filtering."""

    def __init__(self, config):
        super().__init__(
            config.runtime.state_dir,
            config.plant.recorder_max_bytes,
            config.runtime.failure_log_interval_seconds,
        )
        self.enabled = config.plant.recorder_enabled
        self.path = Path(config.runtime.state_dir) / "plant-frames.jsonl"

    def observe(self, engine, now, wall, packet):
        if not self.enabled or now < self.retry_after:
            return
        try:
            self.append(
                json.dumps(
                    self.frame(engine, now, wall, packet), allow_nan=False, sort_keys=True
                ).encode("utf-8")
                + b"\n"
            )
        except Exception as error:
            self.retry_after = now + self.summary_interval
            LOG.warning("Plant recorder unavailable; error=%s", type(error).__name__)

    @staticmethod
    def input_record(engine, ref, unit, observation, now):
        source = engine.sources[ref.source]
        prop = source.property_index().get(ref.key)
        cached = engine.sample_walls.get(ref)
        lifetime = (
            prop.stale_seconds if prop and prop.stale_seconds is not None else source.stale_seconds
        )
        return {
            "value": numeric(observation[0]) if observation else None,
            "expectedUnit": unit,
            "unit": prop.unit if prop else None,
            "observedMonotonic": observation[1] if observation else None,
            "ageSeconds": now - observation[1] if observation else None,
            "staleSeconds": lifetime,
            "fresh": bool(
                observation
                and not source.error
                and ref.key in source.fresh_values(now)
                and 0 <= now - observation[1] <= lifetime
            ),
            "sampleWall": cached[1].isoformat()
            if cached and observation and cached[0] == observation[1]
            else None,
        }

    @staticmethod
    def account_record(engine, name, record):
        signs = engine.account_signs.get(name, {})
        matching = signs.keys() == record["last"].keys()
        values = {key: Decimal(value) for key, value in record["last"].items()}
        pending = engine.ledger.synchronizing.get(name)
        return {
            **{key: record[key] for key in ("lastTime", "oldestTime", "dailyStatus")},
            "lastVectorDayKwh": str(engine.ledger.balance(values, signs, record["dailyBase"]))
            if matching
            else None,
            "confirmedDayKwh": record["dailyValue"],
            "committedDayKwh": engine.ledger.committed.get(name, {}).get("dailyValue"),
            "synchronization": {
                "sinceUtc": pending[0].isoformat(),
                "cutoffUtc": pending[1].isoformat(),
                "waitingFor": sorted(pending[2]),
            }
            if pending
            else None,
        }

    def frame(self, engine, now, wall, packet):
        inputs = {
            ref.identity: self.input_record(
                engine, ref, unit, engine.sources[ref.source].values.get(ref.key), now
            )
            for ref, unit in engine.expected_units.items()
        }
        observations = engine.power_observations(now) or {}
        power_inputs = {
            ref.identity: self.input_record(engine, ref, "W", observations.get(ref), now)
            for ref, unit in engine.expected_units.items()
            if unit == "W"
        }
        power_frames = {}
        for key, (_, unit, terms) in engine.recipes.items():
            if unit != "W":
                continue
            snapshot = engine.power_observations(now, key) or {}
            cycle = engine.recipe_cycles.get(key)
            power_frames[key] = {
                "inputs": {
                    ref.identity: self.input_record(engine, ref, "W", snapshot.get(ref), now)
                    for ref, _ in terms
                },
                "cycle": cycle.evidence(now) if cycle is not None else None,
            }
        latest_balances = {}
        for key, (_, unit, terms) in engine.recipes.items():
            if unit == "W":
                values = [number(inputs[ref.identity]["value"]) for ref, _ in terms]
                latest_balances[key] = (
                    str(sum(value * sign for value, (_, sign) in zip(values, terms)))
                    if all(value is not None for value in values)
                    else None
                )
        available = engine.state.fresh_values(now)
        outputs = {
            key: {
                "candidate": numeric(packet.get(key)),
                "available": numeric(available.get(key)),
            }
            for key, (_, unit, _) in engine.recipes.items()
            if unit == "W"
        }
        return {
            "schemaVersion": 2,
            "timeUtc": wall.isoformat(),
            "monotonic": now,
            "maxSkewSeconds": engine.config.plant.max_skew_seconds,
            "powerMaxSkewSeconds": engine.power_skew,
            "inputs": inputs,
            "powerInputs": power_inputs,
            "powerFrames": power_frames,
            "latestPowerBalances": latest_balances,
            "powerCycle": engine.power_cycles.evidence(now)
            if engine.power_cycles is not None
            else None,
            "powerRecipes": {
                key: [{"input": ref.identity, "sign": sign} for ref, sign in terms]
                for key, (_, unit, terms) in engine.recipes.items()
                if unit == "W"
            },
            "outputs": outputs,
            "powerProblems": json.loads(packet["diagnostics/power-input-status"]),
            "status": {key: value for key, value in packet.items() if key.endswith("status")},
            "sources": {
                name: {
                    "status": source.status(now),
                    "missingCritical": sorted(source.missing_critical(now)),
                }
                for name, source in engine.state.sources.items()
            },
            "plantStatus": engine.state.status(now),
            "plantMissingCritical": sorted(engine.state.missing_critical(now)),
            "accounts": {
                name: self.account_record(engine, name, record)
                for name, record in engine.ledger.data["accounts"].items()
            },
        }
