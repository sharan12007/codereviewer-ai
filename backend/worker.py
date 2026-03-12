import asyncio
import logging
from services.review_pipeline import run_pr_review

logger = logging.getLogger(__name__)

review_queue: asyncio.Queue = asyncio.Queue(maxsize=100)


async def worker_loop():
    logger.info("Worker loop started")
    while True:
        job = await review_queue.get()
        try:
            logger.info(f"Processing job: PR #{job.get('pr_number')} in {job.get('repo_full_name')}")
            await run_pr_review(job)
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
        finally:
            review_queue.task_done()


async def start_worker():
    asyncio.create_task(worker_loop())
    logger.info("Worker started")