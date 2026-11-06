"""Homie metadata for the verified BYD layout, independent publication filters."""

from .model import Property, channel_group_enabled


def properties(settings, profile):
    result = []

    def add(
        group,
        node,
        identifier,
        name,
        unit="",
        datatype="float",
        format="",
        stage="base",
        critical=False,
    ):
        if not channel_group_enabled(
            group,
            advanced=settings.advanced_channels_enabled,
            diagnostics=settings.diagnostics_enabled,
        ):
            return
        lifetime = {
            "base": settings.stale_seconds,
            "detail": settings.detail_stale_seconds,
            "log": settings.log_stale_seconds,
        }[stage]
        result.append(
            Property(
                node,
                identifier,
                name,
                datatype,
                unit,
                format,
                stale_seconds=lifetime,
                required_for_ready=critical,
                channel_group=group,
            )
        )

    for identifier, name, unit in (
        ("soc", "Battery state of charge", "%"),
        ("soh", "Reported battery state of health", "%"),
        ("voltage", "Battery voltage", "V"),
        ("outputvoltage", "Battery output voltage", "V"),
        ("current", "Battery current (positive discharge)", "A"),
        ("power", "Calculated DC battery power (positive discharge)", "W"),
        ("chargepower", "Calculated DC charging power", "W"),
        ("dischargepower", "Calculated DC discharging power", "W"),
        ("temperature", "Battery management unit temperature", "°C"),
        ("temperaturemin", "Reported minimum battery temperature", "°C"),
        ("temperaturemax", "Reported maximum battery temperature", "°C"),
        ("chargeenergy", "Battery-side charge energy (100 Wh resolution)", "kWh"),
        ("dischargeenergy", "Battery-side discharge energy (100 Wh resolution)", "kWh"),
    ):
        add(
            "basic",
            "battery",
            identifier,
            name,
            unit,
            critical=identifier in ("soc", "voltage", "current", "outputvoltage"),
        )
    add(
        "basic",
        "battery",
        "state",
        "Battery state from current direction",
        datatype="enum",
        format="charging,discharging,idle",
    )
    add("basic", "battery", "condition", "BMU reported condition", datatype="string")
    for identifier, name in (
        ("manufacturer", "Manufacturer"),
        ("model", "Battery model"),
        ("serial", "Serial number"),
        ("bmufirmware", "Active BMU firmware"),
        ("bmufirmwarea", "BMU firmware bank A"),
        ("bmufirmwareb", "BMU firmware bank B"),
        ("bmsfirmware", "Active BMS firmware"),
        ("bmsfirmwarea", "BMS firmware bank A"),
        ("bmsfirmwareb", "BMS firmware bank B"),
        ("parametertable", "Active parameter table version"),
        ("parametertablea", "Parameter table A"),
        ("parametertableb", "Parameter table B"),
        ("inverter", "Configured inverter family"),
        ("application", "Configured battery application"),
        ("phase", "Configured phase arrangement"),
    ):
        detail = identifier in (
            "bmsfirmwarea",
            "bmsfirmwareb",
            "parametertablea",
            "parametertableb",
        )
        enum = {
            "application": "off-grid,on-grid,backup,unknown",
            "phase": "single-phase,three-phase,unknown",
        }.get(identifier, "")
        add(
            "advanced",
            "identity",
            identifier,
            name,
            datatype="enum" if enum else "string",
            format=enum,
            stage="detail" if detail else "base",
        )
    for identifier, name in (
        ("towers", "Battery tower count"),
        ("modules", "Modules per tower"),
        ("cellspermodule", "Cells per module"),
        ("temperaturespermodule", "Temperature sensors per module"),
        ("cellcount", "Cell count"),
        ("temperaturecount", "Temperature sensor count"),
    ):
        add("advanced", "identity", identifier, name, datatype="integer")
    add(
        "advanced", "identity", "nominalcapacity", "Nominal energy from module specification", "kWh"
    )
    for node in ["tower1"] + [f"tower1module{i}" for i in range(1, profile["modules"] + 1)]:
        for identifier, name, unit in (
            ("cellvoltagemin", "Minimum sampled cell voltage", "V"),
            ("cellvoltagemax", "Maximum sampled cell voltage", "V"),
            ("cellvoltagemean", "Mean sampled cell voltage", "V"),
            ("cellvoltagespread", "Sampled cell voltage spread", "mV"),
            ("temperaturemin", "Minimum sampled sensor temperature", "°C"),
            ("temperaturemax", "Maximum sampled sensor temperature", "°C"),
            ("temperaturemean", "Mean sampled sensor temperature", "°C"),
            (
                "voltagecellsum" if node == "tower1" else "voltage",
                "Sum of sampled cell voltages",
                "V",
            ),
        ):
            add("advanced", node, identifier, name, unit, stage="detail")
        add(
            "advanced",
            node,
            "balancingcount",
            "Reported balancing cell count",
            datatype="integer",
            stage="detail",
        )
        add(
            "advanced",
            node,
            "balancingactive",
            "Reported balancing active",
            datatype="boolean",
            stage="detail",
        )
    for identifier, name, unit in (
        ("soc", "BMS state of charge (0.1 percent resolution)", "%"),
        ("chargeenergy", "Tower charge energy (1 Wh resolution)", "kWh"),
        ("dischargeenergy", "Tower discharge energy (1 Wh resolution)", "kWh"),
    ):
        add("advanced", "tower1", identifier, name, unit, stage="detail")
    for identifier, name in (
        ("cellvoltageminindex", "Reported minimum voltage cell number"),
        ("cellvoltagemaxindex", "Reported maximum voltage cell number"),
    ):
        add("advanced", "tower1", identifier, name, datatype="integer", stage="detail")
    for module in range(1, profile["modules"] + 1):
        node = f"tower1module{module}"
        for cell in range(1, profile["cellsPerModule"] + 1):
            add(
                "diagnostics",
                node,
                f"cell{cell:02d}voltage",
                f"Cell {cell} voltage",
                "V",
                stage="detail",
            )
            add(
                "diagnostics",
                node,
                f"cell{cell:02d}balancing",
                f"Cell {cell} balancing",
                datatype="boolean",
                stage="detail",
            )
        for sensor in range(1, profile["temperaturesPerModule"] + 1):
            add(
                "diagnostics",
                node,
                f"temperature{sensor:02d}",
                f"Temperature sensor {sensor}",
                "°C",
                stage="detail",
            )
    for identifier, name, unit in (
        ("bmucellvoltagemin", "Coarse BMU minimum cell voltage", "V"),
        ("bmucellvoltagemax", "Coarse BMU maximum cell voltage", "V"),
        ("tower1reportedcellvoltagemin", "BMS header minimum cell voltage", "V"),
        ("tower1reportedcellvoltagemax", "BMS header maximum cell voltage", "V"),
        ("tower1reportedtemperaturemin", "BMS header minimum temperature", "°C"),
        ("tower1reportedtemperaturemax", "BMS header maximum temperature", "°C"),
        ("tower1current", "Additional BMS current", "A"),
        ("tower1voltage", "Additional BMS voltage", "V"),
        ("tower1outputvoltage", "Additional BMS output voltage", "V"),
        ("tower1soh", "Additional BMS state of health", "%"),
    ):
        add(
            "diagnostics",
            "diagnostics",
            identifier,
            name,
            unit,
            stage="base" if identifier.startswith("bmu") else "detail",
        )
    for identifier, name in (
        ("bmuerrorbits", "BMU error bits"),
        ("bmubankcoderaw", "Raw BMU firmware bank code"),
        ("bmsbankcoderaw", "Raw BMS firmware bank code"),
        ("tower1errorbits", "BMS error bits"),
        ("tower1warningbits1", "BMS warning bits 1"),
        ("tower1warningbits2", "BMS warning bits 2"),
        ("tower1warningbits3", "BMS warning bits 3"),
        ("tower1switchbitsraw", "Uninterpreted BMS switch word"),
        ("tower1temperatureminindexraw", "Raw reported minimum temperature index"),
        ("tower1temperaturemaxindexraw", "Raw reported maximum temperature index"),
    ):
        add(
            "diagnostics",
            "diagnostics",
            identifier,
            name,
            datatype="integer",
            stage="detail" if identifier.startswith("tower") else "base",
        )
    for identifier, name in (
        ("bmuerrors", "Reported BMU errors"),
        ("tower1errors", "Reported BMS errors"),
        ("tower1warnings", "Reported BMS warnings"),
    ):
        add(
            "diagnostics",
            "diagnostics",
            identifier,
            name,
            datatype="string",
            stage="base" if identifier.startswith("bmu") else "detail",
        )
    for unit in ("bmu", "tower1"):
        for i in range(1, 21):
            add(
                "diagnostics",
                "events",
                f"{unit}entry{i:02d}",
                f"{unit.upper()} recent event {i}",
                datatype="string",
                stage="log",
            )
        add(
            "diagnostics",
            "diagnostics",
            f"{unit}logrecords",
            f"{unit.upper()} fetched event count",
            datatype="integer",
            stage="log",
        )
    for kind, stage in (("detail", "detail"), ("log", "log")):
        add(
            "diagnostics",
            "diagnostics",
            f"byd{kind}lastsuccess",
            f"Last successful BYD {kind} receipt (UTC)",
            datatype="string",
            stage=stage,
        )
    return tuple(result)
