from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db, PipelineRun
from .graph import run_workflow
from .models import ApprovalRequest
from .agents.repair import RepairAgent
from .adapters import get_vcs_adapter, get_ci_adapter
from .adapters.llm import get_llm_provider
from .notifications import get_notification_provider
import logging
import asyncio
import hmac
import hashlib

logger = logging.getLogger(__name__)

app = FastAPI()

# Global instances (set after config load)
vcs = None
ci = None
llm = None
notifier = None

@app.on_event("startup")
async def startup():
    global vcs, ci, llm, notifier
    vcs = get_vcs_adapter()
    ci = get_ci_adapter()
    llm = get_llm_provider()
    notifier = get_notification_provider()
    # Start background polling
    asyncio.create_task(monitor_polling())

async def monitor_polling():
    while True:
        try:
            runs = await ci.list_runs(status="completed", limit=10)
            db = next(get_db())
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

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    if not settings.webhook_secret:
        return True
    mac = hmac.new(settings.webhook_secret.encode(), msg=payload, digestmod=hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(expected, signature)

@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    payload_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_webhook_signature(payload_bytes, signature):
        raise HTTPException(403, "Invalid signature")

    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")
    if event != "workflow_run":
        return {"status": "ignored"}

    run = payload.get("workflow_run")
    if run and run.get("status") == "completed" and run.get("conclusion") == "failure":
        background_tasks.add_task(run_workflow, run["id"])
        return {"status": "processing"}
    return {"status": "ignored"}

@app.post("/approve")
async def approve(req: ApprovalRequest, db: Session = Depends(get_db)):
    run = db.query(PipelineRun).filter_by(run_id=req.run_id).first()
    if not run:
        raise HTTPException(404, "Run not found")

    if req.approved:
        if not run.fix_plan:
            raise HTTPException(400, "No fix plan available for this run")
        # Reuse repair agent to apply fix
        agent = RepairAgent(llm, vcs, ci, notifier)
        pr_url = await agent._apply_fix(run.fix_plan, run.branch or "main")
        run.approval_status = "approved"
        run.pr_url = pr_url
        db.commit()
        return {"status": "approved", "pr_url": pr_url}
    else:
        run.approval_status = "rejected"
        db.commit()
        return {"status": "rejected"}

@app.post("/slack/actions")
async def slack_actions(request: Request):
    form = await request.form()
    payload = form.get("payload")
    if not payload:
        raise HTTPException(400, "Missing payload")
    import json
    data = json.loads(payload)
    action = data["actions"][0]
    value = action["value"]
    if value.startswith("approve_"):
        run_id = int(value.split("_")[1])
        # Call internal approve endpoint
        async with httpx.AsyncClient() as client:
            await client.post("http://localhost:8000/approve", json={"run_id": run_id, "approved": True, "user": "slack"})
    elif value.startswith("reject_"):
        run_id = int(value.split("_")[1])
        async with httpx.AsyncClient() as client:
            await client.post("http://localhost:8000/approve", json={"run_id": run_id, "approved": False, "user": "slack"})
    return JSONResponse(content={"text": "Received"})

@app.get("/health")
async def health():
    return {"status": "ok"}