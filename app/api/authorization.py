from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


from app.schemas.user import AddUserResponce, LoginResponce, UserBase, UserCreate
from app.services.auth import AuthService, config


router = APIRouter(prefix="/api", tags=["Авторизация"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def add_user(user_data: Annotated[UserCreate, Depends()]) -> AddUserResponce:
    try:
        user_id = await AuthService.add_user(user_data)
        return JSONResponse(status_code=201, content={"user_id": user_id})
    except IntegrityError:
        # Ошибка, которую отправляет база данных, о том, что это значение
        # не уникально, т.е. логин должен быть в базе один
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This login is already in use"
        )


@router.get("/login", status_code=status.HTTP_200_OK)
async def verify(
    user_data: Annotated[UserBase, Depends()], response: Response
) -> LoginResponce:
    token = await AuthService.verify_user(user_data)
    response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, value=token)
    return {"message": "Login successful"}
