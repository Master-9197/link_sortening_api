from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from app.api.authorization import router as auth_router
from app.api.links import router as links_router
from app.db.database import create_tables, run_redis


format_logging = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=format_logging)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    await run_redis()
    logger.info("Database reloaded!")
    yield
    logger.info("Shutting down")


app = FastAPI(lifespan=lifespan, title="Link Shortening API")
app.include_router(auth_router)
app.include_router(links_router)
