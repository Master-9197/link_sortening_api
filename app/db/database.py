from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.tables import Base
from app.db.config import settings
import redis.asyncio as redis
import logging


logger = logging.getLogger(__name__)


engine = create_async_engine(settings.db_url)
new_session = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)

redis_client = redis.Redis.from_url(url=settings.redis_url, decode_responses=True)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def delete_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def run_redis():
    try:
        await redis_client.ping()
        await redis_client.flushall()
        logger.info("Connection to Redis is successful")
    except redis.ConnectionError as e:
        logger.error(f"Error connection to Redis! Error: {e}")
