import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_db_and_tables
from worker import start_worker
from routers import webhook, reviews, file_review, auth, dashboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== STARTING AI REVIEWER ===")
    create_db_and_tables()
    logger.info("Database tables created")
    await start_worker()
    logger.info("=== STARTUP COMPLETE ===")
    yield
    logger.info("Shutting down")


app = FastAPI(title="AI Code Reviewer", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router)
app.include_router(reviews.router)
app.include_router(file_review.router)
app.include_router(auth.router)
app.include_router(dashboard.router)


@app.get("/health")
async def health():
    try:
        from sqlmodel import Session, text
        from database import engine
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
    return {"status": "ok", "db": db_status}