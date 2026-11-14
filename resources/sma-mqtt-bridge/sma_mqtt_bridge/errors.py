"""Only controlled, non-secret messages may cross the CLI/logging boundary."""


class BridgeError(Exception):
    """An error whose message is safe to display."""


class ConfigError(BridgeError):
    """Invalid configuration or unverified model profile."""


class StateError(BridgeError):
    """Persistent state is unavailable, corrupt or owned by another instance."""


class ProtocolError(BridgeError):
    """Invalid, incomplete or unexpected protocol data."""


class AuthenticationError(ProtocolError):
    """Credentials or an interactive login challenge require user attention."""


class ProtocolTimeout(ProtocolError):
    """A bounded network operation timed out; no remote exception text is retained."""
