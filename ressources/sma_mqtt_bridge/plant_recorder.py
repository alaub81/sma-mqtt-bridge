"""Bounded, opt-in calculation frames for power and accounting-time investigations."""

import json
import logging
from pathlib import Path

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

    def frame(self, engine, now, wall, packet):
        inputs = {}
        for ref, unit in engine.expected_units.items():
            source = engine.sources[ref.source]
            observation = source.values.get(ref.key)
            prop = source.property_index().get(ref.key)
            cached = engine.sample_walls.get(ref)
            inputs[ref.identity] = {
                "value": numeric(observation[0]) if observation else None,
                "expectedUnit": unit,
                "unit": prop.unit if prop else None,
                "observedMonotonic": observation[1] if observation else None,
                "ageSeconds": now - observation[1] if observation else None,
                "staleSeconds": (
                    prop.stale_seconds
                    if prop and prop.stale_seconds is not None
                    else source.stale_seconds
                ),
                "fresh": not source.error and ref.key in source.fresh_values(now),
                "sampleWall": cached[1].isoformat()
                if cached and observation and cached[0] == observation[1]
                else None,
            }
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
            "schemaVersion": 1,
            "timeUtc": wall.isoformat(),
            "monotonic": now,
            "maxSkewSeconds": engine.config.plant.max_skew_seconds,
            "powerMaxSkewSeconds": engine.power_skew,
            "inputs": inputs,
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
                name: {key: record[key] for key in ("lastTime", "oldestTime", "dailyStatus")}
                for name, record in engine.ledger.data["accounts"].items()
            },
        }
