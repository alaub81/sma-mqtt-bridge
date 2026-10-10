"""Non-secret diagnostics and explicitly enabled read-only service."""

import argparse
import asyncio
import json
import logging
import os
from pathlib import Path
import sys

from . import __version__
from .config import DATA, load_config
from .errors import BridgeError, ConfigError
from .health import healthy
from .profiles import load_profile


def main(argv=None):
    parser = argparse.ArgumentParser(description="SMA read-only Homie 4 bridge")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--version", action="store_true")
    group.add_argument("--project-status", action="store_true")
    group.add_argument("--check-config", action="store_true")
    group.add_argument("--check-profile", metavar="PROFILE")
    group.add_argument("--healthcheck", action="store_true")
    parser.add_argument("--refresh-portal", action="store_true", help="Explicitly request one portal read when periodic polling is zero")
    args = parser.parse_args(argv)
    try:
        if args.version:
            print("sma-mqtt-bridge " + __version__)
            return 0
        if args.project_status:
            print(json.dumps({"runtimeImplemented": True, "liveVerified": False, "readOnly": True,
                              "paidSmaApisRequired": False, "bundledPollingProfiles": 3}))
            return 0
        if args.healthcheck:
            # The same JSON/ENV precedence applies, but source configuration does no I/O.
            config = load_config()
            return 0 if healthy(config.runtime.state_dir, config.runtime.health_stale_seconds) else 1
        if args.check_profile:
            profile = load_profile(args.check_profile, os.environ.get("SMAB_PROFILE_DIR", DATA + "/profiles"))
            print(json.dumps({"validSchema": True, "pollingValidated": profile["validation"]["status"] == "validated"}))
            return 0
        config = load_config()
        if args.check_config:
            print(json.dumps({"valid": True, "enabledSources": sum(i.enabled for i in config.inverters)
                              + sum((config.home_manager.enabled, config.echarger.enabled,
                                     config.echarger.semp_enabled, config.portal.enabled)), "readOnly": True}))
            return 0
        if args.refresh_portal and not config.portal.enabled:
            raise ConfigError("--refresh-portal requires an explicitly enabled portal adapter")
        if not config.has_sources and not (Path(config.runtime.state_dir) / "mqtt-topics.json").exists():
            raise ConfigError("No sources enabled; use --check-config for offline validation")
        from .runtime import run
        logging.basicConfig(level=config.runtime.log_level, format="%(levelname)s %(message)s")
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
