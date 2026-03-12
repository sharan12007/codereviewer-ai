import logging
import time
from datetime import datetime
from sqlmodel import Session, select
from database import engine
from models import PullRequest, Review, ReviewComment
from services.diff_parser import fetch_pr_files, parse_diff_to_chunks
from services.prompt_engine import SYSTEM_PROMPT, build_prompt
from services.llm_client import LLMClient, ReviewPipelineError
from services.noise_filter import filter_comments
from services.github_client import post_review
from sse import broadcast

logger = logging.getLogger(__name__)


async def run_pr_review(job: dict) -> None:
    repo_full_name = job['repo_full_name']
    pr_number = job['pr_number']
    installation_token = job['installation_token']
    pr_id = job['pr_id']

    start_time = time.time()

    try:
        # Step 1 — update PR status to reviewing
        with Session(engine) as session:
            pr = session.get(PullRequest, pr_id)
            if pr:
                pr.status = 'reviewing'
                pr.updated_at = datetime.utcnow()
                session.add(pr)
                session.commit()

        # Step 2 — broadcast SSE
        await broadcast({'type': 'status', 'pr_id': pr_id, 'status': 'reviewing'})

        # Step 3 — fetch PR files
        files = fetch_pr_files(repo_full_name, pr_number, installation_token)
        if not files:
            logger.info(f"No reviewable files for PR {pr_number}")
            _finalize(pr_id, 'completed', start_time, [], "No reviewable files found.", None, repo_full_name, pr_number, installation_token)
            return

        # Step 4 — parse chunks
        chunks = parse_diff_to_chunks(files)
        if not chunks:
            logger.info(f"No chunks for PR {pr_number}")
            _finalize(pr_id, 'completed', start_time, [], "No reviewable changes found.", None, repo_full_name, pr_number, installation_token)
            return

        # Step 5 — call LLM for each chunk
        llm = LLMClient()
        all_raw_comments = []
        summary = ''
        total_tokens = 0

        for chunk in chunks:
            user_prompt = build_prompt(chunk)
            result = await llm.review(SYSTEM_PROMPT, user_prompt)

            chunk_comments = result.get('comments', [])
            for c in chunk_comments:
                c['file_path'] = chunk.file_path

            all_raw_comments.extend(chunk_comments)
            if result.get('summary'):
                summary = result['summary']

        # Step 6+7 — filter comments
        filtered = filter_comments(all_raw_comments)

        # Step 8 — post to GitHub
        github_review_id = None
        try:
            github_review_id = post_review(
                token=installation_token,
                repo_full_name=repo_full_name,
                pr_number=pr_number,
                comments=filtered,
                summary=summary
            )
        except Exception as e:
            logger.error(f"Failed to post GitHub review: {e}")

        # Step 9+10+11 — save and finalize
        _finalize(pr_id, 'completed', start_time, filtered, summary,
                  github_review_id, repo_full_name, pr_number,
                  installation_token, llm.get_model_name(), total_tokens)

    except Exception as e:
        logger.error(f"run_pr_review failed for PR {pr_id}: {e}", exc_info=True)
        with Session(engine) as session:
            pr = session.get(PullRequest, pr_id)
            if pr:
                pr.status = 'failed'
                pr.updated_at = datetime.utcnow()
                session.add(pr)
                session.commit()
        await broadcast({'type': 'error', 'pr_id': pr_id, 'message': str(e)})


def _finalize(pr_id, status, start_time, comments, summary,
              github_review_id, repo_full_name, pr_number,
              installation_token, model_used='gemini-1.5-flash', tokens_used=0):
    duration_ms = int((time.time() - start_time) * 1000)

    with Session(engine) as session:
        # Save Review row
        review = Review(
            pr_id=pr_id,
            model_used=model_used,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
            summary=summary,
            github_review_id=github_review_id,
        )
        session.add(review)
        session.flush()

        # Save ReviewComment rows
        for c in comments:
            rc = ReviewComment(
                review_id=review.id,
                file_path=c.get('file_path', ''),
                line=c.get('position', 0),
                body=c.get('body', ''),
                severity=c.get('severity', 'info'),
                confidence=c.get('confidence', 0.0),
                category=c.get('category', 'style'),
            )
            session.add(rc)

        # Update PR status
        pr = session.get(PullRequest, pr_id)
        if pr:
            pr.status = status
            pr.updated_at = datetime.utcnow()
            session.add(pr)

        session.commit()
        review_id = review.id

    import asyncio
    asyncio.create_task(broadcast({
        'type': 'completed',
        'pr_id': pr_id,
        'review_id': review_id,
        'comment_count': len(comments)
    }))