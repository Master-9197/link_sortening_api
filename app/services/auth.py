from fastapi import HTTPException, status
from sqlalchemy import select
from dotenv import load_dotenv
from passlib.context import CryptContext
from authx import AuthX, AuthXConfig
from datetime import timedelta
import os
import logging

from app.models.tables import Users
from app.db.database import new_session, redis_client
from app.schemas.user import UserCreate, UserBase


logger = logging.getLogger(__name__)

pass_mngr = CryptContext(schemes=["bcrypt"], deprecated="auto")

load_dotenv()

config = AuthXConfig()
config.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
config.JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)
config.JWT_ACCESS_COOKIE_NAME = "access_token_cookie"
config.JWT_TOKEN_LOCATION = ["cookies"]
auth = AuthX(config=config)

AuthRequired = auth.access_token_required


class AuthService:
    @classmethod
    async def add_user(cls, user_data: UserCreate):
        async with new_session() as session:
            # Получаем модель данных пользователя
            user_info = user_data.model_dump()

            # Поулчаем хэш пароля
            hashed_password = pass_mngr.hash(user_data.password)

            # Сохраняем хэш пароля
            user_info["hashed_password"] = hashed_password

            # Удаляем поле пароля, т.к. оно не хранится
            user_info.pop("password")

            # Создаем запись в бд
            user = Users(**user_info)

            # Закидываем запись в бд
            session.add(user)
            await session.flush()

            # Сохраняем кэш хэша и id
            async with redis_client.pipeline(transaction=True) as pipe:
                await pipe.set(
                    f"user:{user.login}:hashed_password", hashed_password, ex=3600
                )
                await pipe.set(f"user:{user.login}:id", str(user.id), ex=3600)
                await pipe.execute()

            # Сохраняем изменения в бд
            await session.commit()
            return user.id

    @classmethod
    async def verify_user(cls, user_data: UserBase) -> str:
        """Возвращает JWT токен"""
        async with new_session() as session:
            # Формируем ключи Redis один раз
            password_key = f"user:{user_data.login}:hashed_password"
            user_id_key = f"user:{user_data.login}:id"

            # Атомарно получаем данные из Redis
            cache_hashed_password, cache_user_id = await redis_client.mget(
                password_key, user_id_key
            )

            if cache_hashed_password and cache_user_id:
                # Проверяем пароль
                if not pass_mngr.verify(user_data.password, cache_hashed_password):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid credentials",
                    )
                # Конвертируем user_id из строки (Redis хранит все как строки)
                user_id = int(cache_user_id)
                # Создаем токен
                return auth.create_access_token(uid=str(user_id))

            # Если нет в кэше, ищем в БД
            result = await session.execute(
                select(Users.hashed_password, Users.id).filter_by(login=user_data.login)
            )
            user = result.first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            hashed_password, user_id = user

            if not pass_mngr.verify(user_data.password, hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                )

            # Обновляем кэш
            async with redis_client.pipeline(transaction=True) as pipe:
                await pipe.set(password_key, hashed_password, ex=3600)
                await pipe.set(user_id_key, str(user_id), ex=3600)
                await pipe.execute()

            return auth.create_access_token(uid=str(user_id))
