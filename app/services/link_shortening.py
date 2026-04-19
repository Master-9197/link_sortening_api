from fastapi import HTTPException
from sqids import Sqids

from app.models.tables import Links
from app.db.database import new_session, redis_client
from sqlalchemy import select


sqids = Sqids(min_length=7)
HOST = "http://127.0.0.1:8000"


class LinkShorteningService:
    @classmethod
    async def short_link(cls, url: str, user_id: int):
        async with new_session() as session:
            result = await session.execute(
                select(Links.id).filter_by(uid=int(user_id)).order_by(Links.id.desc())
            )
            id = result.scalar()
            if id:
                hash_id = sqids.encode([id + 1])
            else:
                hash_id = sqids.encode([1])
            new_link = Links(uid=int(user_id), url=url, hash=hash_id)

            # Добавляем в кеш url
            key = f"link:{hash_id}:url"
            await redis_client.setex(key, 48 * 3600, url)

            # Сохраняем записть в бд
            session.add(new_link)
            await session.flush()
            await session.commit()

            return f"{HOST}/{new_link.hash}"

    @classmethod
    async def get_link_from_hash(cls, hash: str):
        key = f"link:{hash}:url"
        url = await redis_client.get(key)
        if not url:
            async with new_session() as session:
                result = await session.execute(select(Links.url).filter_by(hash=hash))
                if not url:
                    raise HTTPException(
                        status_code=404, detail="This short url not found"
                    )
                else:
                    url = result.scalar()

        return url
