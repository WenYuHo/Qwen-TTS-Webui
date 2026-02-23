class StudioError(Exception):
    """Base class for all studio exceptions."""
    pass

class SynthesisError(StudioError):
    """Raised when audio synthesis fails."""
    pass

class VideoError(StudioError):
    """Raised when video generation fails."""
    pass

class ProjectNotFoundError(StudioError):
    """Raised when a project file cannot be found."""
    pass

class VoiceNotFoundError(StudioError):
    """Raised when a required voice profile is missing."""
    pass
