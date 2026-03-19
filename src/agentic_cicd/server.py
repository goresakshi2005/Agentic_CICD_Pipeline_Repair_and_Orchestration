from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from .config_loader import load_config
from .graph import run_workflow
from .database import SessionLocal, PipelineRun
from .models import ApprovalRequest
from .agents.repair import RepairAgent
from .adapters import get_vcs_adapter, get_ci_adapter
from .notifications.slack import SlackNotifier
import logging
import asyncio

app = FastAPI()
logger = logging.getLogger(__name__)

# These will be set after loading config
vcs = ci = notifier = None

@app.on_event("startup")
async def startup():
    global vcs, ci, notifier
    # Config already loaded by CLI
    from .config import settings
    vcs = get_vcs_adapter()
    ci = get_ci_adapter()
    if settings.slack_token:
        from .notifications.slack import SlackNotifier
        notifier = SlackNotifier(settings.slack_token, settings.slack_channel)
    else:
        notifier = None
    # Start background monitor
    asyncio.create_task(monitor_polling())

async def monitor_polling():
    from .config import settings
    while True:
        try:
            runs = await ci.list_runs(status="completed", limit=10)
            db = SessionLocal()
            for run in runs:
                run_id = run["id"]
                existing = db.query(PipelineRun).filter_by(run_id=run_id).first()
                if not existing and run["conclusion"] == "failure":
                    logger.info(f"Polling found unprocessed failed run {run_id}")
                    asyncio.create_task(run_workflow(run_id))
            db.close()
        except Exception as e:
            logger.error(f"Polling error: {e}")
        await asyncio.sleep(settings.poll_interval)

@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    # Determine provider from headers (e.g., X-GitHub-Event)
    # Simplified: assume GitHub for now
    event = request.headers.get("X-GitHub-Event")
    if event != "workflow_run":
        return {"status": "ignored"}
    payload = await request.json()
    run = payload.get("workflow_run")
    if run and run.get("status") == "completed" and run.get("conclusion") == "failure":
        background_tasks.add_task(run_workflow, run["id"])
        return {"status": "processing"}
    return {"status": "ignored"}

@app.post("/approve")
async def approve(req: ApprovalRequest):
    db = SessionLocal()
    run = db.query(PipelineRun).filter_by(run_id=req.run_id).first()
    if not run:
        raise HTTPException(404, "Run not found")
    if req.approved:
        # Apply fix
        agent = RepairAgent(None, vcs, ci, notifier)  # llm not needed for applying
        pr_url = await agent._apply_fix(run.fix_plan, run.branch or "main")
        run.approval_status = "approved"
        run.pr_url = pr_url
        db.commit()
        return {"status": "approved", "pr_url": pr_url}
    else:
        run.approval_status = "rejected"
        db.commit()
        return {"status": "rejected"}

@app.get("/health")
async def health():
    return {"status": "ok"}