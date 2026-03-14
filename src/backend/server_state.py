from .podcast_engine import PodcastEngine
from .task_manager import task_manager, TaskStatus

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = PodcastEngine()
    return _engine

# For backward compatibility with existing imports
class EngineProxy:
    def __getattr__(self, name):
        return getattr(get_engine(), name)

engine = EngineProxy()
