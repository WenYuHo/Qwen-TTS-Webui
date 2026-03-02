from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..utils import phoneme_manager

router = APIRouter(prefix="/api/system", tags=["system"])

class PhonemeOverride(BaseModel):
    word: str
    phonetic: str

@router.get("/phonemes")
async def get_phonemes():
    return {"overrides": phoneme_manager.overrides}

@router.post("/phonemes")
async def add_phoneme(override: PhonemeOverride):
    try:
        overrides = phoneme_manager.overrides.copy()
        overrides[override.word] = override.phonetic
        phoneme_manager.save(overrides)
        return {"status": "ok", "overrides": phoneme_manager.overrides}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/phonemes/{word}")
async def delete_phoneme(word: str):
    try:
        overrides = phoneme_manager.overrides.copy()
        if word in overrides:
            del overrides[word]
            phoneme_manager.save(overrides)
        return {"status": "ok", "overrides": phoneme_manager.overrides}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
