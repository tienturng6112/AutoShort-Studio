class DomainException(Exception):
    """Base domain exception for AutoShort Studio."""
    pass

class AIProviderException(DomainException):
    """Raised when external AI providers encounter connectivity, throttling, or parsing errors."""
    pass

class TTSException(DomainException):
    """Raised when speech synthesis voice generation fails."""
    pass

class TimelineRenderException(DomainException):
    """Raised when the render engine fails to stitch, composite, or burn subtitles."""
    pass

class PluginSecurityException(DomainException):
    """Raised when a plugin violates sandbox permissions or tries dynamic file tampering."""
    pass

class TimelineSynchronizationError(DomainException):
    """Raised when timeline durations do not sync properly."""
    pass
