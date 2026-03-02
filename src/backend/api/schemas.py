from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any

class SpeakerProfile(BaseModel):
    role: str
    type: str
    value: str

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
    profiles: Dict[str, Dict[str, Any]]
    script: List[ScriptLine]
    bgm_mood: Optional[str] = None
    ducking_level: Optional[float] = 0.0
    eq_preset: Optional[str] = "flat"
    reverb_level: Optional[float] = 0.0
    stream: Optional[bool] = False

class S2SRequest(BaseModel):
    source_audio: str
    target_voice: Dict[str, Any]
    preserve_prosody: bool = False

class DubRequest(BaseModel):
    source_audio: str
    target_lang: str

class StreamingSynthesisRequest(BaseModel):
    text: str
    profile: Dict[str, Any]
    language: Optional[str] = "auto"
    instruct: Optional[str] = None

class ProjectBlock(BaseModel):
    id: str
    role: str
    text: str
    status: str
    language: Optional[str] = "auto"
    pause_after: Optional[float] = 0.5

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

class VideoGenerationRequest(BaseModel):
    prompt: str
    width: Optional[int] = 768
    height: Optional[int] = 512
    num_frames: Optional[int] = 65
    guidance_scale: Optional[float] = 3.5
    num_inference_steps: Optional[int] = 30
    seed: Optional[int] = -1

class NarratedVideoRequest(BaseModel):
    prompt: str
    narration_text: str
    voice_profile: Dict[str, Any]
    width: Optional[int] = 768
    height: Optional[int] = 512
    num_frames: Optional[int] = 65
    guidance_scale: Optional[float] = 3.5
    num_inference_steps: Optional[int] = 30
    seed: Optional[int] = -1
