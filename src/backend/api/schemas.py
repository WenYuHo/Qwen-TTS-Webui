from pydantic import BaseModel

class SpeakerProfile(BaseModel):
    role: str
    type: str
    value: str
