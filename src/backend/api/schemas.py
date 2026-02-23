from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any

class SpeakerProfile(BaseModel):
    role: str
    type: str
    value: str
    image_url: Optional[str] = None

class MixRequest(BaseModel):
    name: str
    voices: List[Dict[str, Any]]

class VoiceLibrary(BaseModel):
    voices: List[Dict[str, Any]]

class ScriptLine(BaseModel):
    role: str
    text: str
    start_time: Optional[float] = 0.0
    language: Optional[str] = "auto"
    pause_after: Optional[float] = 0.5

class PodcastRequest(BaseModel):
    profiles: List[Dict[str, Any]]
    script: List[ScriptLine]
    bgm_mood: Optional[str] = None

class S2SRequest(BaseModel):
    source_audio: str
    target_voice: Dict[str, Any]
    preserve_prosody: bool = False

class DubRequest(BaseModel):
    source_audio: str
    target_lang: str

class ProjectBlock(BaseModel):
    id: str
    role: str
    text: str
    status: str
    language: Optional[str] = "auto"
    pause_after: Optional[float] = 0.5
    image_url: Optional[str] = None

class ProjectData(BaseModel):
    name: str
    blocks: List[ProjectBlock]
    script_draft: Optional[str] = ""
    voices: Optional[List[Dict[str, Any]]] = []

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Project name cannot be empty')
        return v.strip()

class DownloadRequest(BaseModel):
    repo_id: str


class VideoRequest(BaseModel):
    project_name: str
    aspect_ratio: str = "16:9"
    include_subtitles: bool = True
    font_size: int = 40
    font_type: str = "DejaVuSans-Bold.ttf"