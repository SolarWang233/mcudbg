class McudbgError(Exception):
    """Base exception for mcudbg."""


class ConfigurationError(McudbgError):
    """Raised when required configuration is missing."""


class BackendUnavailableError(McudbgError):
    """Raised when an optional hardware backend is unavailable."""
