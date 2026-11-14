"""Durable local electricity-price preference; never writes to an SMA device."""

import math
import re
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from .errors import ConfigError, StateError
from .model import Property, SourceState
from .storage import MISSING, read_state, write_state

PRICE_KEY = "settings/electricity-price"
RESULT_KEY = "settings/electricity-price-result"
PRICE = Property(
    "settings",
    "electricity-price",
    "Electricity price per kWh",
    unit="€",
    settable=True,
    stale_seconds=float("inf"),
    channel_group="basic",
)
RESULT = Property(
    "settings",
    "electricity-price-result",
    "Electricity price command result",
    "string",
    stale_seconds=float("inf"),
    channel_group="basic",
)

FEED_IN_PRICE = replace(PRICE, id="feed-in-price", name="Feed-in price per kWh")
FEED_IN_RESULT = replace(RESULT, id="feed-in-price-result", name="Feed-in price command result")


def parse_price(text):
    """Accept plain decimal currency/kWh with a dot and no quantity suffix."""
    if not isinstance(text, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", text):
        raise ValueError
    value = Decimal(text)
    if not math.isfinite(float(value)):
        raise ValueError
    return value


class PlantPrice:
    def __init__(self, config, changed, *, feed_in=False):
        self.config = config
        self.changed = changed
        self.property = replace(
            FEED_IN_PRICE if feed_in else PRICE,
            unit=config.plant.currency,
            settable=not feed_in or config.plant.grid_source == "home-manager",
        )
        self.result_property = FEED_IN_RESULT if feed_in else RESULT
        source_id = "plant-feed-in-price" if feed_in else "plant-price"
        self.path = Path(config.runtime.state_dir) / (source_id + ".json")
        rate = (
            config.plant.feed_in_tariff_per_kwh
            if feed_in
            else config.plant.electricity_price_per_kwh
        )
        configured = (
            config.feed_in_tariff_configured if feed_in else config.electricity_price_configured
        )
        self.price = Decimal(str(rate)) if configured else None
        self.state = SourceState(
            source_id,
            config.plant.homie_id,
            (self.property, self.result_property),
            1,
            diagnostics_enabled=False,
            contributes_availability=False,
            max_payload_bytes=config.runtime.max_payload_bytes,
        )
        data = read_state(self.path, config.runtime.max_state_bytes)
        if data is not MISSING:
            try:
                if (
                    not isinstance(data, dict)
                    or set(data) != {"schemaVersion", "device", "currency", "price"}
                    or type(data["schemaVersion"]) is not int
                    or data["schemaVersion"] != 1
                    or data["device"] != config.plant.homie_id
                    or data["currency"] != config.plant.currency
                    or len(data["price"].encode()) > config.runtime.max_payload_bytes
                ):
                    raise ValueError
                self.price = parse_price(data["price"])
            except ValueError, TypeError, KeyError, AttributeError, ArithmeticError:
                raise StateError("Invalid or incompatible plant price state") from None
        if self.price is not None and not self.property.settable:
            raise ConfigError("Feed-in remuneration requires the Home Manager grid source")
        self.state.update({self.property.key: self.price})

    def result(self, status):
        self.state.update({self.result_property.key: status})

    async def handle(self, key, data, retained=False):
        if retained:
            self.result("rejected-retained")
            return
        try:
            if (
                not self.property.settable
                or key != self.property.id
                or not isinstance(data, bytes)
                or len(data) > self.config.runtime.max_payload_bytes
            ):
                raise ValueError
            value = parse_price(data.decode("ascii"))
        except ValueError, UnicodeError, ArithmeticError:
            self.result("rejected")
            return
        record = {
            "schemaVersion": 1,
            "device": self.config.plant.homie_id,
            "currency": self.config.plant.currency,
            "price": format(value, "f"),
        }
        try:
            write_state(self.path, record, self.config.runtime.max_state_bytes)
            if read_state(self.path, self.config.runtime.max_state_bytes) != record:
                raise StateError("Plant price readback mismatch")
        except OSError, StateError:
            self.result("storage-error")
            return
        self.price = value
        self.state.update({self.property.key: value, self.result_property.key: "confirmed"})
        self.changed.set()

    async def close(self):
        pass
