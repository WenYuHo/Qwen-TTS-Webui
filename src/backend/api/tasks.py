from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io
from .. import server_state

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("/{task_id}")
async def get_task_status(task_id: str):
    task = server_state.task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    response = task.copy()
    if response["result"] and isinstance(response["result"], bytes):
        response["has_result"] = True
        del response["result"]
    else:
        response["has_result"] = False

    return response

@router.get("/{task_id}/result")
async def get_task_result(task_id: str):
    task = server_state.task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] != server_state.TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task not completed yet")

    if not task["result"]:
        raise HTTPException(status_code=404, detail="No result found for this task")

    return StreamingResponse(io.BytesIO(task["result"]), media_type="audio/wav")
