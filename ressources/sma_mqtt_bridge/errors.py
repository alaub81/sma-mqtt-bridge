"""Only controlled, non-secret messages may cross the CLI/logging boundary."""


class BridgeError(Exception):
    """An error whose message is safe to display."""


class ConfigError(BridgeError):
    """Invalid configuration or unverified model profile."""


class ProtocolError(BridgeError):
    """Invalid, incomplete or unexpected protocol data."""


class AuthenticationError(ProtocolError):
    """Credentials or an interactive login challenge require user attention."""
