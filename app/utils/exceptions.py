class UpstreamServiceError(Exception):
    """Raised when the upstream service cannot be reached or parsed."""


class NoPredictionError(Exception):
    """Raised when upstream returns no usable prediction for a name."""
