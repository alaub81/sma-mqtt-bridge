"""Opt-in, rate-limited numeric evidence for plant calculations and mapped registers."""

import json
import logging

from .model import number

LOG = logging.getLogger(__name__)


def numeric(value):
    value = number(value)
    return str(value) if value is not None else None


class PlantDebug:
    def __init__(self, interval=0):
        self.interval = interval
        self.next_due = {}

    def due(self, key, now):
        if (
            self.interval <= 0
            or not LOG.isEnabledFor(logging.DEBUG)
            or now < self.next_due.get(key, float("-inf"))
        ):
            return False
        self.next_due[key] = now + self.interval
        return True

    def report(self, engine, now, wall):
        if not self.due("balance", now):
            return
        fresh = {name: source.fresh_values(now) for name, source in engine.sources.items()}
        inputs = {}
        for ref, unit in engine.expected_units.items():
            source = engine.sources[ref.source]
            observation = source.values.get(ref.key)
            inputs[ref.identity] = {
                "value": numeric(observation[0]) if observation else None,
                "unit": unit,
                "ageSeconds": round(now - observation[1], 3) if observation else None,
                "fresh": not source.error and ref.key in fresh[ref.source],
                "sourceError": bool(source.error),
            }
        outputs = {}
        for state in engine.output_states:
            for key, value in state.fresh_values(now).items():
                if not key.startswith("diagnostics/"):
                    outputs[state.device + "/" + key.replace("-", "")] = numeric(value)
        recipes = {
            key.replace("-", ""): [{"input": ref.identity, "sign": sign} for ref, sign in terms]
            for key, (_, _, terms) in engine.recipes.items()
            if key != "pv/total-earnings"
        }
        # Copy only numeric baselines and accounting times, never hardware fingerprints.
        accounts = {
            name: {
                field: record[field]
                for field in (
                    "date",
                    "start",
                    "lastTime",
                    "oldestTime",
                    "dailyStatus",
                    "totalStatus",
                    "dailyBase",
                    "totalBase",
                    "last",
                    "dailyValue",
                    "totalValue",
                )
            }
            for name, record in engine.ledger.data["accounts"].items()
        }
        status = {
            key.replace("-", ""): value
            for state in engine.output_states
            for key, value in state.fresh_values(now).items()
            if key.startswith("diagnostics/") and key.endswith("status")
        }
        house_terms = {m["totalyield"].identity: 1 for m in engine.groups["pv"]}
        house_terms.update(
            {engine.grid["energyimport"].identity: 1, engine.grid["energyexport"].identity: -1}
        )
        for member in engine.groups["battery"]:
            house_terms[member["batterydischargeenergy"].identity] = 1
            house_terms[member["batterychargeenergy"].identity] = -1
        energy_recipes = {
            "import": {engine.grid["energyimport"].identity: 1},
            "export": {engine.grid["energyexport"].identity: 1},
            "house": house_terms,
        }
        if engine.wallbox is not None:
            energy_recipes.update(
                {
                    "wallbox": {engine.wallbox.identity: 1},
                    "housewithoutwallbox": {**house_terms, engine.wallbox.identity: -1},
                }
            )
        LOG.debug(
            "Plant calculation debug %s",
            json.dumps(
                {
                    "timeUtc": wall.isoformat(),
                    "batteryBoundary": engine.boundary,
                    "publishPartialDay": engine.config.plant.publish_partial_day,
                    "powerProblems": engine.power_input_problems(now),
                    "inputs": inputs,
                    "powerInputs": {
                        ref.identity: {
                            "value": numeric(observation[0]) if observation else None,
                            "ageSeconds": round(now - observation[1], 3) if observation else None,
                        }
                        for ref, observation in (engine.power_observations(now) or {}).items()
                    },
                    "powerFrames": {
                        key: {
                            ref.identity: numeric(observation[0]) if observation else None
                            for ref, observation in (
                                engine.power_observations(now, key) or {}
                            ).items()
                        }
                        for key, (_, unit, _) in engine.recipes.items()
                        if unit == "W"
                    },
                    "powerCycle": engine.power_cycles.evidence(now)
                    if engine.power_cycles is not None
                    else None,
                    "powerRecipes": recipes,
                    "energyRecipes": energy_recipes,
                    "legacyInitialHouseKwh": engine.config.plant.initial_consumption_kwh,
                    "availableValues": outputs,
                    "status": status,
                    "accounts": accounts,
                    "committedAccounts": {
                        name: {
                            k: record[k] for k in ("date", "oldestTime", "dailyValue", "totalValue")
                        }
                        for name, record in engine.ledger.committed.items()
                    },
                    "checkpointDirty": engine.ledger.dirty,
                    "checkpointIntervalSeconds": engine.config.plant.checkpoint_interval_seconds,
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

    def modbus(self, reader, blocks, selected, now, result):
        if self.interval <= 0 or not LOG.isEnabledFor(logging.DEBUG):
            return
        mapping = reader.profile.get("plant", {})
        allowed = {
            value
            for group in ("pv", "battery", "grid")
            for metric, value in mapping.get(group, {}).items()
            if metric not in ("energyBoundary", "energyEvidence")
        } | {"measurements/status", "measurements/grid-contactor"}
        pollers = {p["id"]: p for p in reader.pollers}
        for prop in reader.definitions:
            key = prop["node"] + "/" + prop["id"]
            if (
                key not in allowed
                or prop["node"] != "measurements"
                or prop["type"] == "string"
                or prop["poller"] not in selected
                or not self.due(key, now)
            ):
                continue
            words = blocks[prop["poller"]][prop["offset"] : prop["offset"] + prop["length"]]
            LOG.debug(
                "Plant register debug %s",
                json.dumps(
                    {
                        "source": reader.settings.id,
                        "property": key,
                        "register": pollers[prop["poller"]]["start"] + prop["offset"],
                        "words": words,
                        "type": prop["type"],
                        "scale": prop["scale"],
                        "wordOrder": prop["wordOrder"],
                        "byteOrder": prop["byteOrder"],
                        "numericValue": numeric(result.get(key)),
                        "valid": result.get(key) is not None,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            )
