import hashlib
import hmac
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from config import settings
from database import engine
from models import PullRequest, Repository
from services.github_client import get_installation_token
from sse import subscribe, unsubscribe, event_generator
from worker import review_queue

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = 'sha256=' + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/webhook")
async def webhook_handler(request: Request):
    payload_bytes = await request.body()

    # Validate signature
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")

    if not verify_signature(payload_bytes, signature, settings.GITHUB_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Validate event type
    event = request.headers.get("X-GitHub-Event", "")
    if event != "pull_request":
        return {"status": "ignored", "reason": f"event={event}"}

    payload = await request.json()
    action = payload.get("action", "")

    # Only process these actions
    if action not in ("opened", "synchronize", "reopened"):
        return {"status": "ignored", "reason": f"action={action}"}

    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})
    installation_data = payload.get("installation", {})

    installation_id = installation_data.get("id")
    if not installation_id:
        logger.error("No installation_id in webhook payload")
        return {"status": "error", "reason": "no installation_id"}

    repo_full_name = repo_data.get("full_name", "")
    pr_number = pr_data.get("number")
    head_sha = pr_data.get("head", {}).get("sha", "")

    # Get installation token
    try:
        installation_token = get_installation_token(installation_id)
    except Exception as e:
        logger.error(f"Failed to get installation token: {e}")
        return {"status": "error", "reason": "token_fetch_failed"}

    # Upsert Repository and PullRequest in DB
    with Session(engine) as session:
        # Upsert repo
        repo = session.exec(
            select(Repository).where(Repository.github_repo_id == repo_data.get("id"))
        ).first()

        if not repo:
            repo = Repository(
                github_repo_id=repo_data.get("id"),
                full_name=repo_full_name,
                owner=repo_full_name.split("/")[0],
                name=repo_full_name.split("/")[1],
                default_branch=repo_data.get("default_branch", "main"),
                webhook_active=True,
            )
            session.add(repo)
            session.flush()

        # Check for duplicate (same PR + same sha already reviewed)
        existing = session.exec(
            select(PullRequest).where(
                PullRequest.repo_id == repo.id,
                PullRequest.pr_number == pr_number,
                PullRequest.head_sha == head_sha,
            )
        ).first()

        if existing and existing.status in ("reviewing", "completed"):
            logger.info(f"PR #{pr_number} sha={head_sha} already processed, skipping")
            return {"status": "skipped", "reason": "already_processed"}

        # Create PR row
        pr_row = PullRequest(
            repo_id=repo.id,
            pr_number=pr_number,
            title=pr_data.get("title", ""),
            author=pr_data.get("user", {}).get("login", ""),
            head_sha=head_sha,
            status="pending",
        )
        session.add(pr_row)
        session.commit()
        session.refresh(pr_row)
        pr_id = pr_row.id

    # Enqueue job
    job = {
        "repo_full_name": repo_full_name,
        "pr_number": pr_number,
        "installation_token": installation_token,
        "pr_id": pr_id,
    }

    await review_queue.put(job)
    logger.info(f"Enqueued review job for PR #{pr_number} in {repo_full_name}")

    return {"status": "ok", "pr_id": pr_id}


@router.get("/events")
async def events():
    q = await subscribe()

    async def stream():
        try:
            async for chunk in event_generator(q):
                yield chunk
        finally:
            unsubscribe(q)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )