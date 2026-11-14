"""Known BYD HVS fields, explicit byte order, units and historical event scope."""

import json
import struct
from datetime import datetime

from .errors import ProtocolError

BMU_ERRORS = (
    "high-temperature-charging",
    "low-temperature-charging",
    "discharge-overcurrent",
    "charge-overcurrent",
    "main-circuit-failure",
    "short-circuit",
    "cell-imbalance",
    "current-sensor-failure",
    "battery-overvoltage",
    "battery-undervoltage",
    "cell-overvoltage",
    "cell-undervoltage",
    "voltage-sensor-failure",
    "temperature-sensor-failure",
    "high-temperature-discharging",
    "low-temperature-discharging",
)
BMS_ERRORS = (
    "cell-voltage-sensor-failure",
    "temperature-sensor-failure",
    "bic-communication-failure",
    "pack-voltage-sensor-failure",
    "current-sensor-failure",
    "charge-mos-failure",
    "discharge-mos-failure",
    "precharge-mos-failure",
    "main-relay-failure",
    "precharge-failure",
    "heating-failure",
    "radiator-failure",
    "balancing-failure",
    "cell-failure",
    "pcb-temperature-sensor-failure",
    "functional-safety-failure",
)
BMS_WARNINGS = (
    "battery-overvoltage",
    "battery-undervoltage",
    "cell-overvoltage",
    "cell-undervoltage",
    "cell-imbalance",
    "high-temperature-charging",
    "low-temperature-charging",
    "high-temperature-discharging",
    "low-temperature-discharging",
    "charge-overcurrent",
    "discharge-overcurrent",
    "hardware-charge-overcurrent",
    "short-circuit",
    "inverse-connection",
    "interlock-abnormal",
    "air-switch-abnormal",
)
WARNINGS3 = (
    "battery-overvoltage",
    "battery-undervoltage",
    "cell-overvoltage",
    "cell-undervoltage",
    "voltage-sensor-failure",
    "temperature-sensor-failure",
    "high-temperature-discharging",
    "low-temperature-discharging",
    "high-temperature-charging",
    "low-temperature-charging",
    "discharge-overcurrent",
    "charge-overcurrent",
    "main-circuit-failure",
    "short-circuit",
    "cell-imbalance",
    "current-sensor-failure",
)
BMS_EVENT_NAMES = {
    0: "power-on",
    1: "power-off",
    2: "event-record",
    3: "periodic-record",
    4: "start-charging",
    5: "stop-charging",
    6: "start-discharging",
    7: "stop-discharging",
    8: "soc-calibration-rough",
    9: "soc-calibration-detail",
    10: "stop-soc-calibration",
    11: "can-communication-failure",
    12: "serial-communication-failure",
    13: "precharge-request",
    14: "precharge-success",
    15: "precharge-failure",
    16: "start-end-soc-calibration",
    17: "start-balancing",
    18: "stop-balancing",
    19: "address-registered",
    20: "functional-safety-event",
    21: "event-additional-info",
    101: "start-firmware-update",
    102: "firmware-update-complete",
    103: "firmware-update-failure",
    104: "firmware-bank-jump",
    105: "parameter-table-update",
    106: "serial-number-change",
    107: "current-calibration",
    108: "battery-voltage-calibration",
    109: "pack-voltage-calibration",
    110: "soc-soh-calibration",
    111: "clock-calibration",
}
BMU_EVENT_NAMES = {
    **{i: BMS_EVENT_NAMES[i] for i in (0, 1, 2, 101, 102, 103, 104, 105, 106, 111)},
    22: "start-firmware-update",
    23: "firmware-update-complete",
    24: "firmware-update-failure",
    25: "serial-number-change",
    26: "current-calibration",
    27: "battery-voltage-calibration",
    28: "pack-voltage-calibration",
    29: "soc-soh-calibration",
    32: "state-change",
    33: "erase-bms-firmware",
    34: "start-bms-update",
    35: "bms-update-complete",
    36: "functional-safety-info",
    38: "operating-limits-info",
    39: "bcu-hardware-failure",
    40: "bms-firmware-list",
    41: "bms-mcu-list",
    112: "bms-bmu-disconnected",
    113: "bmu-firmware-reset",
    114: "bmu-watchdog-reset",
    115: "precharge-failure",
    116: "address-registration-failure",
    117: "parameter-table-load-failure",
    118: "periodic-system-record",
    120: "parameter-table-update-complete",
}
INVERTERS = {
    0: "Fronius HV",
    1: "Goodwe HV/Viessmann HV",
    3: "KOSTAL HV",
    5: "SMA SBS3.7/5.0/6.0 HV",
    9: "Sungrow HV",
    16: "SMA SBS2.5 HV",
    19: "SMA STP 5.0-10.0 SE HV",
}


def signed(value):
    return value if value < 32768 else value - 65536


def version(word, reverse=False):
    a, b = word >> 8, word & 255
    return f"{b}.{a}" if reverse else f"{a}.{b}"


def low_word_first(words):
    return words[0] | words[1] << 16


def check(value, minimum, maximum):
    if not minimum <= value <= maximum:
        raise ProtocolError("BYD measurement outside supported encoding range")
    return value


def flags(value, names):
    return ",".join(name for bit, name in enumerate(names) if value & (1 << bit)) or "none"


def identity_values(raw, profile, expected_serial=""):
    if len(raw) != 102:
        raise ProtocolError("BYD identity length mismatch")
    try:
        serial = struct.pack(">10H", *raw[:10]).decode("ascii").rstrip("\0 ")
    except UnicodeError, struct.error:
        raise ProtocolError("Invalid BYD identity encoding") from None
    if (
        not serial.startswith(("P03", "E0P3"))
        or not serial.isprintable()
        or raw[17] >> 8 != 2
        or raw[16] & 15 != profile["modules"]
        or (raw[16] >> 4) & 15 != 1
        or (expected_serial and serial != expected_serial)
        or version(raw[12]) not in profile["supportedBmuFirmware"]
        or version(raw[13]) not in profile["supportedBmuFirmware"]
        or raw[12] != raw[13]
        or version(raw[14]) not in profile["supportedBmsFirmware"]
    ):
        raise ProtocolError("BYD identity, topology or firmware mismatch")
    modules = profile["modules"]
    return {
        "identity/manufacturer": "BYD",
        "identity/model": "Battery-Box Premium HVS",
        "identity/serial": serial,
        "identity/bmufirmware": version(raw[12]),
        "identity/bmufirmwarea": version(raw[12]),
        "identity/bmufirmwareb": version(raw[13]),
        "identity/bmsfirmware": version(raw[14]),
        "identity/towers": 1,
        "identity/modules": modules,
        "identity/cellspermodule": profile["cellsPerModule"],
        "identity/temperaturespermodule": profile["temperaturesPerModule"],
        "identity/cellcount": modules * profile["cellsPerModule"],
        "identity/temperaturecount": modules * profile["temperaturesPerModule"],
        "identity/nominalcapacity": round(modules * profile["moduleCapacityKwh"], 6),
        "identity/inverter": INVERTERS.get(raw[16] >> 8, "unknown-" + str(raw[16] >> 8)),
        "identity/application": {0: "off-grid", 1: "on-grid", 2: "backup"}.get(
            raw[17] & 255, "unknown"
        ),
        "identity/phase": {0: "single-phase", 1: "three-phase"}.get(raw[18] >> 8, "unknown"),
        "diagnostics/bmubankcoderaw": raw[15] >> 8,
        "diagnostics/bmsbankcoderaw": raw[15] & 255,
    }


def base_values(r, profile):
    if len(r) != 25 or version(r[14]) not in profile["supportedParameterTables"]:
        raise ProtocolError("BYD status layout/table mismatch")
    soc, soh = check(r[0], 0, 100), check(r[3], 0, 100)
    voltage, output = check(r[5] / 100, 1, 600), check(r[16] / 100, 0, 600)
    current = check(signed(r[4]) / 10, -100, 100)
    temperatures = [check(signed(r[i]), -40, 100) for i in (8, 7, 6)]
    power = round(current * output, 6)
    errors = flags(r[13], BMU_ERRORS)
    return {
        "battery/soc": soc,
        "battery/soh": soh,
        "battery/voltage": voltage,
        "battery/outputvoltage": output,
        "battery/current": current,
        "battery/power": power,
        "battery/chargepower": max(-power, 0),
        "battery/dischargepower": max(power, 0),
        "battery/state": "discharging" if current > 0 else "charging" if current < 0 else "idle",
        "battery/condition": "no-reported-error" if not r[13] else errors,
        "battery/temperature": temperatures[0],
        "battery/temperaturemin": temperatures[1],
        "battery/temperaturemax": temperatures[2],
        "battery/chargeenergy": low_word_first(r[17:19]) / 10,
        "battery/dischargeenergy": low_word_first(r[19:21]) / 10,
        "identity/parametertable": version(r[14]),
        "diagnostics/bmucellvoltagemin": check(r[2] / 100, 0, 5),
        "diagnostics/bmucellvoltagemax": check(r[1] / 100, 0, 5),
        "diagnostics/bmuerrorbits": r[13],
        "diagnostics/bmuerrors": errors,
    }


def summary(node, cells, temperatures, balancing):
    return {
        node + "/cellvoltagemin": min(cells),
        node + "/cellvoltagemax": max(cells),
        node + "/cellvoltagemean": round(sum(cells) / len(cells), 6),
        node + "/cellvoltagespread": round((max(cells) - min(cells)) * 1000, 3),
        node + ("/voltagecellsum" if node == "tower1" else "/voltage"): round(sum(cells), 3),
        node + "/temperaturemin": min(temperatures),
        node + "/temperaturemax": max(temperatures),
        node + "/temperaturemean": round(sum(temperatures) / len(temperatures), 6),
        node + "/balancingcount": sum(balancing),
        node + "/balancingactive": any(balancing),
    }


def detail_values(d, profile, identity):
    if len(d) != 256:
        raise ProtocolError("BYD detail payload length mismatch")
    bank = identity["diagnostics/bmsbankcoderaw"]
    if bank not in (0, 1) or version(d[30 + bank], True) != identity["identity/bmsfirmware"]:
        raise ProtocolError("BYD BMS firmware bank mismatch")
    if any(version(d[i], True) not in profile["supportedParameterTables"] for i in (45, 46)):
        raise ProtocolError("BYD detail parameter table mismatch")
    count = profile["modules"] * profile["cellsPerModule"]
    tcount = profile["modules"] * profile["temperaturesPerModule"]
    cells = [check(value / 1000, 0.001, 5) for value in d[48 : 48 + count]]
    # One reserved word follows the voltage array; unused sensor bytes are padding.
    temperatures = list(struct.unpack("64b", struct.pack(">32H", *d[177:209])))[:tcount]
    for value in temperatures:
        check(value, -40, 100)
    balance = [bool(d[6 + i // 16] & (1 << (i % 16))) for i in range(count)]
    result = summary("tower1", cells, temperatures, balance)
    for module in range(profile["modules"]):
        node = f"tower1module{module + 1}"
        start, tstart = (
            module * profile["cellsPerModule"],
            module * profile["temperaturesPerModule"],
        )
        c, t, b = (
            cells[start : start + profile["cellsPerModule"]],
            temperatures[tstart : tstart + profile["temperaturesPerModule"]],
            balance[start : start + profile["cellsPerModule"]],
        )
        result.update(summary(node, c, t, b))
        result.update({f"{node}/cell{i:02d}voltage": v for i, v in enumerate(c, 1)})
        result.update({f"{node}/cell{i:02d}balancing": v for i, v in enumerate(b, 1)})
        result.update({f"{node}/temperature{i:02d}": v for i, v in enumerate(t, 1)})
    warnings = [flags(d[i], BMS_WARNINGS if i != 29 else WARNINGS3) for i in (27, 28, 29)]
    result.update(
        {
            "tower1/soc": check(signed(d[24]) / 10, 0, 100),
            "tower1/chargeenergy": low_word_first(d[14:16]) / 1000,
            "tower1/dischargeenergy": low_word_first(d[16:18]) / 1000,
            "tower1/cellvoltagemaxindex": check(d[2] >> 8, 1, count),
            "tower1/cellvoltageminindex": check(d[2] & 255, 1, count),
            "identity/bmsfirmwarea": version(d[30], True),
            "identity/bmsfirmwareb": version(d[31], True),
            "identity/parametertablea": version(d[45], True),
            "identity/parametertableb": version(d[46], True),
            "diagnostics/tower1reportedcellvoltagemin": check(d[1] / 1000, 0.001, 5),
            "diagnostics/tower1reportedcellvoltagemax": check(d[0] / 1000, 0.001, 5),
            "diagnostics/tower1reportedtemperaturemin": check(signed(d[4]), -40, 100),
            "diagnostics/tower1reportedtemperaturemax": check(signed(d[3]), -40, 100),
            "diagnostics/tower1temperatureminindexraw": d[5] & 255,
            "diagnostics/tower1temperaturemaxindexraw": d[5] >> 8,
            "diagnostics/tower1current": check(signed(d[26]) / 10, -100, 100),
            "diagnostics/tower1voltage": check(signed(d[20]) / 10, 1, 600),
            "diagnostics/tower1outputvoltage": check(signed(d[23]) / 10, 0, 600),
            "diagnostics/tower1soh": check(signed(d[25]), 0, 100),
            "diagnostics/tower1errorbits": d[47],
            "diagnostics/tower1errors": flags(d[47], BMS_ERRORS),
            "diagnostics/tower1warningbits1": d[27],
            "diagnostics/tower1warningbits2": d[28],
            "diagnostics/tower1warningbits3": d[29],
            "diagnostics/tower1warnings": ",".join(w for w in warnings if w != "none") or "none",
            "diagnostics/tower1switchbitsraw": d[22],
        }
    )
    return result


def event_fields(unit, code, raw):
    """Only previously verified event payload classes gain interpreted fields."""

    def u16(offset, order="big", signed_value=False):
        return int.from_bytes(raw[offset : offset + 2], order, signed=signed_value)

    if unit == "bmu":
        if code == 2:
            return dict(
                event_present=bool(raw[0]),
                error_code=raw[1],
                warning_bits=u16(2),
                cell_voltage_max_mv=u16(4),
                cell_voltage_min_mv=u16(6),
                temperature_max_c=raw[8],
                temperature_min_c=raw[9],
                battery_voltage_v=u16(10) / 10,
                soc_percent=raw[12],
                soh_percent=raw[13],
            )
        if code == 32:
            return dict(previous_state_code=raw[1], new_state_code=raw[0])
        if code == 38:
            return dict(
                max_charge_current_a=u16(0) / 10,
                max_discharge_current_a=u16(2) / 10,
                max_charge_voltage_v=u16(4) / 10,
                min_discharge_voltage_v=u16(6) / 10,
                state_code=raw[8],
                battery_temperature_c=raw[9],
                inverter_code=raw[10],
                tower_count=raw[11],
            )
    elif code in (2, 4, 5, 6, 13, 14, 21):
        result = dict(
            warning_bits=[u16(i, "little") for i in (0, 2, 4)],
            error_bits=u16(6, "little"),
            switch_status_bits=raw[8],
            soc_percent=raw[9],
            soh_percent=raw[10],
            battery_voltage_v=u16(11, "little") / 10,
            output_voltage_v=u16(13, "little") / 10,
            current_a=u16(15, "little", True) / 10,
        )
        if code == 21:
            result.update(
                cell_voltage_max_index_raw=raw[17],
                cell_voltage_min_index_raw=raw[18],
                temperature_max_index_raw=raw[20],
                temperature_min_index_raw=raw[21],
            )
        else:
            result.update(
                cell_voltage_max_mv=u16(17, "little"),
                cell_voltage_min_mv=u16(19, "little"),
                temperature_max_c=raw[21],
                temperature_min_c=raw[22],
            )
        return result
    elif code in (17, 18):
        result = dict(cell_voltage_min_mv=u16(21, "little"))
        if code == 17:
            result["balancing_cells_one_based"] = [
                i + 1 for i in range(128) if raw[i // 8] & (1 << (i % 8))
            ]
        return result
    return {}


def log_values(data, unit, max_payload_bytes):
    if len(data) != 320 or unit not in ("bmu", "tower1"):
        raise ProtocolError("BYD event buffer layout mismatch")
    result = {f"events/{unit}entry{i:02d}": "null" for i in range(1, 21)}
    count = 0
    for i in range(20):
        raw = struct.pack(">15H", *data[i * 15 : (i + 1) * 15])
        if not any(raw[:4]) or all(v == 255 for v in raw):
            break
        try:
            timestamp = datetime(2000 + raw[1], *raw[2:7]).isoformat()
        except ValueError:
            raise ProtocolError("BYD event timestamp invalid") from None
        code, payload = raw[0], raw[7:]
        record = {
            "timestamp_device_local": timestamp,
            "time_basis": "device-local-offset-unverified",
            "code": code,
            "description_reference": (BMU_EVENT_NAMES if unit == "bmu" else BMS_EVENT_NAMES).get(
                code, "unknown-event"
            ),
            "data_hex": payload.hex(),
            "values_at_event": event_fields(unit, code, payload),
        }
        encoded = json.dumps(record, separators=(",", ":"), ensure_ascii=True)
        if len(encoded.encode()) > max_payload_bytes:
            raise ProtocolError("BYD event exceeds configured payload limit")
        result[f"events/{unit}entry{i + 1:02d}"] = encoded
        count += 1
    result[f"diagnostics/{unit}logrecords"] = count
    return result
