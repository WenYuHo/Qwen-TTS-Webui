from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any, Union

class SpeakerProfile(BaseModel):
    role: Optional[str] = None
    type: str
    value: str
    preview_text: Optional[str] = None
    ref_text: Optional[str] = None

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
    instruct: Optional[str] = None
    pan: Optional[float] = 0.0
    temperature: Optional[float] = None

class PodcastRequest(BaseModel):
    profiles: Union[List[SpeakerProfile], Dict[str, SpeakerProfile]]
    script: List[ScriptLine]
    bgm_mood: Optional[str] = None
    ducking_level: Optional[float] = 0.0
    eq_preset: Optional[str] = "flat"
    reverb_level: Optional[float] = 0.0
    stream: Optional[bool] = False
    master_acx: Optional[bool] = False
    temperature: Optional[float] = None
    temperature_preset: Optional[str] = "balanced"

class S2SRequest(BaseModel):
    source_audio: str
    target_voice: Dict[str, Any]
    preserve_prosody: bool = True
    instruct: Optional[str] = None
    target_lang: Optional[str] = None
    stream: Optional[bool] = False

class BatchS2SRequest(BaseModel):
    source_audios: List[str]
    target_voice: Dict[str, Any]
    preserve_prosody: bool = True
    instruct: Optional[str] = None

class DubRequest(BaseModel):
    source_audio: str
    target_lang: str

class DetectLanguageRequest(BaseModel):
    source_audio: str

class StreamingSynthesisRequest(BaseModel):
    text: str
    profile: Dict[str, Any]
    language: Optional[str] = "auto"
    instruct: Optional[str] = None
    temperature: Optional[float] = None

TEMPERATURE_PRESETS = {
    "consistent": {"temperature": 0.3, "top_k": 20, "top_p": 0.8, "repetition_penalty": 1.2},
    "balanced":   {"temperature": 0.9, "top_k": 50, "top_p": 0.95, "repetition_penalty": 1.0},
    "creative":   {"temperature": 1.2, "top_k": 80, "top_p": 0.98, "repetition_penalty": 0.9},
}

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
    max_shift: Optional[float] = None
    base_shift: Optional[float] = None
    terminal: Optional[float] = None

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
    max_shift: Optional[float] = None
    base_shift: Optional[float] = None
    terminal: Optional[float] = None
