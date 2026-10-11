"""Non-secret diagnostics and bridge runtime with independently gated optional writes."""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from . import __version__
from .config import DATA, load_config
from .errors import BridgeError, ConfigError
from .health import healthy
from .profiles import load_profile


class TimestampFormatter(logging.Formatter):
    """Render each record in the configured timezone, including its UTC offset."""

    def __init__(self, timezone):
        super().__init__("%(asctime)s %(levelname)s %(message)s")
        self.timezone = ZoneInfo(timezone)

    def formatTime(self, record, datefmt=None):
        return datetime.fromtimestamp(record.created, self.timezone).isoformat(
            timespec="milliseconds"
        )


def main(argv=None):
    parser = argparse.ArgumentParser(description="SMA Homie 4 bridge")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--version", action="store_true")
    group.add_argument("--project-status", action="store_true")
    group.add_argument("--check-config", action="store_true")
    group.add_argument("--check-profile", metavar="PROFILE")
    group.add_argument("--check-home-manager-profile", metavar="PROFILE")
    group.add_argument("--healthcheck", action="store_true")
    parser.add_argument(
        "--refresh-portal",
        action="store_true",
        help="Explicitly request one portal read when periodic polling is zero",
    )
    args = parser.parse_args(argv)
    try:
        if args.version:
            print("sma-mqtt-bridge " + __version__)
            return 0
        if args.project_status:
            # Static code capabilities, independent of installation configuration or acceptance.
            print(
                json.dumps(
                    {
                        "runtimeImplemented": True,
                        "liveVerified": False,
                        "readOnly": False,
                        "commandsEnabledByDefault": False,
                        "paidSmaApisRequired": False,
                        "bundledPollingProfiles": 3,
                    }
                )
            )
            return 0
        if args.healthcheck:
            # Resolve local configuration/files with normal precedence, without device connections.
            config = load_config()
            return (
                0 if healthy(config.runtime.state_dir, config.runtime.health_stale_seconds) else 1
            )
        if args.check_home_manager_profile:
            from .home_manager_profile import load_home_manager_profile

            load_home_manager_profile(
                args.check_home_manager_profile,
                os.environ.get("SMAB_PROFILE_DIR", DATA + "/profiles"),
            )
            print(
                json.dumps(
                    {"validSchema": True, "documentedReadMappings": True, "liveVerified": False}
                )
            )
            return 0
        if args.check_profile:
            profile = load_profile(
                args.check_profile, os.environ.get("SMAB_PROFILE_DIR", DATA + "/profiles")
            )
            print(
                json.dumps(
                    {
                        "validSchema": True,
                        "pollingValidated": profile["validation"]["status"] == "validated",
                    }
                )
            )
            return 0
        config = load_config()
        if args.check_config:
            print(
                json.dumps(
                    {
                        "valid": True,
                        "enabledSources": sum(i.enabled for i in config.inverters)
                        + sum(
                            (
                                config.home_manager.enabled,
                                config.echarger.enabled,
                                config.echarger.semp_enabled,
                                config.portal.enabled,
                            )
                        ),
                        "readOnly": not (
                            config.commands.enabled
                            and (config.echarger.commands_enabled or config.portal.commands_enabled)
                        ),
                    }
                )
            )
            return 0
        if args.refresh_portal and not config.portal.enabled:
            raise ConfigError("--refresh-portal requires an explicitly enabled portal adapter")
        if (
            not config.has_sources
            and not (Path(config.runtime.state_dir) / "mqtt-topics.json").exists()
        ):
            raise ConfigError("No sources enabled; use --check-config for offline validation")
        from .runtime import run

        handler = logging.StreamHandler()
        handler.setFormatter(TimestampFormatter(config.runtime.timezone))
        logging.basicConfig(level=config.runtime.log_level, handlers=[handler])
        # Third-party diagnostics may contain URLs or tokens, including at DEBUG level.
        for name in ("aiohttp", "aiomqtt", "paho", "asyncio"):
            logging.getLogger(name).setLevel(logging.CRITICAL)
        asyncio.run(run(config, args.refresh_portal))
        return 0
    except BridgeError as error:
        print(str(error), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    except Exception:
        print("Bridge operation failed; no authenticated diagnostics were logged", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
