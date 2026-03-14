import asyncio
import logging
from services.review_pipeline import run_pr_review

logger = logging.getLogger(__name__)

review_queue: asyncio.Queue = asyncio.Queue(maxsize=100)


async def worker_loop():
    logger.info("=== WORKER LOOP STARTED ===")
    while True:
        try:
            logger.info("Worker waiting for job...")
            job = await review_queue.get()
            logger.info(f"=== JOB RECEIVED: PR #{job.get('pr_number')} in {job.get('repo_full_name')} ===")
            try:
                await run_pr_review(job)
            except Exception as e:
                logger.error(f"Worker job error: {e}", exc_info=True)
            finally:
                review_queue.task_done()
                logger.info("Job done")
        except Exception as e:
            logger.error(f"Worker loop error: {e}", exc_info=True)
            await asyncio.sleep(1)


async def start_worker():
    logger.info("Starting worker...")
    asyncio.create_task(worker_loop())
    logger.info("Worker task created")