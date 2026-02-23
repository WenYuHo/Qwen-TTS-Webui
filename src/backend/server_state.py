from .podcast_engine import PodcastEngine
from .video_engine import VideoEngine
from .task_manager import task_manager

engine = PodcastEngine()
video_engine = VideoEngine(engine)
