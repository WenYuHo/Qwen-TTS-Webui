from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io
from .. import server_state

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("/")
async def list_tasks():
    return server_state.task_manager.list_tasks()

@router.get("/{task_id}")
async def get_task_status(task_id: str):
    task = server_state.task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    response = task.copy()
    result = response.get("result")
    
    # Hide large binary data in status response
    if result:
        if isinstance(result, bytes):
            response["has_result"] = True
            del response["result"]
        elif isinstance(result, dict) and "audio" in result:
            response["has_result"] = True
            # Keep other metadata (like segments) but hide the audio bytes
            response["result"] = {k: v for k, v in result.items() if k != "audio"}
        else:
            response["has_result"] = True
    else:
        response["has_result"] = False

    return response

@router.get("/{task_id}/result")
async def get_task_result(task_id: str, format: str = "wav"):
    task = server_state.task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] != server_state.TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task not completed yet")

    result = task.get("result")
    if not result:
        raise HTTPException(status_code=404, detail="No result found for this task")

    audio_bytes = result if isinstance(result, bytes) else result.get("audio")
    if not audio_bytes:
         raise HTTPException(status_code=404, detail="No audio result found")

    if format.lower() == "wav":
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/wav")
    
    # ⚡ Bolt: On-the-fly conversion for other formats using pydub
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
        
        out_buf = io.BytesIO()
        ext = format.lower()
        if ext == "mp3":
            audio.export(out_buf, format="mp3", bitrate="192k")
            media_type = "audio/mpeg"
        elif ext == "aac" or ext == "m4a":
            audio.export(out_buf, format="adts") # ADTS is the container for raw AAC
            media_type = "audio/aac"
        elif ext == "flac":
            audio.export(out_buf, format="flac")
            media_type = "audio/flac"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
            
        out_buf.seek(0)
        return StreamingResponse(out_buf, media_type=media_type)
    except Exception as e:
        logger.error(f"Format conversion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {e}")
