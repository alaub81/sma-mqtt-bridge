"""File-based display labels; never translate identifiers or device values."""

from pathlib import Path
import re

from .errors import ConfigError

LANGUAGE = re.compile(r"[a-z]{2,3}(?:-[a-z0-9]{2,8})*\Z")
BUNDLED = Path(__file__).resolve().parent.parent / "translate"


def read_labels(path):
    """Validate bounded, unambiguous UTF-8 dictionaries without logging their contents."""
    from .config import read_json

    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 1048576:
            raise ValueError
        data = read_json(path)
        if (not isinstance(data, dict) or set(data) != {"schemaVersion", "labels"}
                or type(data["schemaVersion"]) is not int or data["schemaVersion"] != 1
                or not isinstance(data["labels"], dict)
                or any(not key or not isinstance(value, str) or not value.strip()
                       or len(key) > 256 or len(value) > 256
                       or any(ord(char) < 32 for char in key + value)
                       for key, value in data["labels"].items())):
            raise ValueError
        return data["labels"]
    except (OSError, ValueError, ConfigError):
        raise ConfigError("Invalid translation file") from None


def load_translation(language, directory):
    """English < bundled selected language < optional host selected language."""
    if not LANGUAGE.fullmatch(language) or not directory:
        raise ConfigError("Invalid translation language or directory")
    labels = read_labels(BUNDLED / "en.json")
    bundled = BUNDLED / (language + ".json")
    host = Path(directory) / (language + ".json")
    found = language == "en"
    for path in (bundled, host):
        if path.exists() or path.is_symlink():
            labels.update(read_labels(path))
            found = True
    if not found:
        raise ConfigError("Selected translation language is unavailable")
    if "{number}" not in labels.get("Device {number}", ""):
        raise ConfigError("Device translation must preserve {number}")
    return labels
