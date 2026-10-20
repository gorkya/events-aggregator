from fastapi import APIRouter, BackgroundTasks, Request

router = APIRouter()


@router.post("/sync/trigger")
async def trigger_sync(
    request: Request, background_tasks: BackgroundTasks
) -> dict[str, str]:
    runner = request.app.state.sync_runner
    if runner.is_running:
        return {"status": "already_running"}
    background_tasks.add_task(runner.run)
    return {"status": "started"}
