"""Custom exceptions for the tax app."""

class RateScheduleNotFoundError(Exception):
    """Raised when no active rate schedule can be resolved for a given context."""
    pass


class TurnoverRequiredError(Exception):
    """Raised when an assessment calculation requires a turnover but none was provided."""
    pass
