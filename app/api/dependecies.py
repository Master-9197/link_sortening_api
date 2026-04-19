from fastapi import HTTPException, Request, status
import jwt

from app.services.auth import config


async def get_current_user(requests: Request):
    jwt_token = requests.cookies.get(config.JWT_ACCESS_COOKIE_NAME)
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        paload: dict = jwt.decode(
            jwt_token, key=config.JWT_SECRET_KEY, algorithms=config.JWT_ALGORITHM
        )
        return paload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invailid token"
        )
