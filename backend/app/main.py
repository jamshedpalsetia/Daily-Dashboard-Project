import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import scheduler
from app.config import get_settings
from app.db import engine
from app.routers import digest, news, settings, stocks, todos, travel, weather

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown()


app = FastAPI(title="Daily Dashboard", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(weather.router)
app.include_router(stocks.router)
app.include_router(travel.router)
app.include_router(news.router)
app.include_router(todos.router)
app.include_router(settings.router)
app.include_router(digest.router)


@app.get("/api/health")
def health() -> dict:
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
        db_ok = True
    except Exception as exc:  # noqa: BLE001
        log.error("health check db failure: %s", exc)
        db_ok = False

    job = scheduler.scheduler.get_job(scheduler.DIGEST_JOB_ID)
    return {
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
        "smtp_configured": get_settings().smtp_configured,
        "next_digest": job.next_run_time.isoformat() if job and job.next_run_time else None,
    }
