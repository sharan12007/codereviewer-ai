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

    logger.info("=== WEBHOOK RECEIVED ===")

    # Validate signature
    signature = request.headers.get("X-Hub-Signature-256", "")
    logger.info(f"Signature present: {bool(signature)}")

    if not signature:
        logger.warning("Missing signature")
        raise HTTPException(status_code=401, detail="Missing signature")

    if not verify_signature(payload_bytes, signature, settings.GITHUB_WEBHOOK_SECRET):
        logger.warning("Invalid signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    logger.info("Signature valid")

    # Validate event type
    event = request.headers.get("X-GitHub-Event", "")
    logger.info(f"GitHub event: {event}")

    if event != "pull_request":
        logger.info(f"Ignoring event: {event}")
        return {"status": "ignored", "reason": f"event={event}"}

    payload = await request.json()
    action = payload.get("action", "")
    logger.info(f"PR action: {action}")

    if action not in ("opened", "synchronize", "reopened"):
        logger.info(f"Ignoring action: {action}")
        return {"status": "ignored", "reason": f"action={action}"}

    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})
    installation_data = payload.get("installation", {})

    installation_id = installation_data.get("id")
    repo_full_name = repo_data.get("full_name", "")
    pr_number = pr_data.get("number")
    head_sha = pr_data.get("head", {}).get("sha", "")

    logger.info(f"Repo: {repo_full_name} | PR: #{pr_number} | SHA: {head_sha}")
    logger.info(f"Installation ID: {installation_id}")

    if not installation_id:
        logger.error("No installation_id in webhook payload")
        return {"status": "error", "reason": "no installation_id"}

    # Get installation token
    try:
        logger.info("Fetching installation token...")
        installation_token = get_installation_token(installation_id)
        logger.info("Installation token fetched OK")
    except Exception as e:
        logger.error(f"Failed to get installation token: {e}", exc_info=True)
        return {"status": "error", "reason": f"token_fetch_failed: {e}"}

    # Upsert Repository and PullRequest in DB
    try:
        with Session(engine) as session:
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
                logger.info(f"Created repository record: {repo_full_name}")

            # Check for duplicate
            existing = session.exec(
                select(PullRequest).where(
                    PullRequest.repo_id == repo.id,
                    PullRequest.pr_number == pr_number,
                    PullRequest.head_sha == head_sha,
                )
            ).first()

            if existing and existing.status in ("reviewing", "completed"):
                logger.info(f"PR #{pr_number} already processed, skipping")
                return {"status": "skipped", "reason": "already_processed"}

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
            logger.info(f"Created PR record with id={pr_id}")

    except Exception as e:
        logger.error(f"DB error: {e}", exc_info=True)
        return {"status": "error", "reason": f"db_error: {e}"}

    # Enqueue job
    job = {
        "repo_full_name": repo_full_name,
        "pr_number": pr_number,
        "installation_token": installation_token,
        "pr_id": pr_id,
    }

    try:
        await review_queue.put(job)
        logger.info(f"Job enqueued. Queue size: {review_queue.qsize()}")
    except Exception as e:
        logger.error(f"Failed to enqueue job: {e}", exc_info=True)

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