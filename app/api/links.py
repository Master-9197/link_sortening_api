from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import AnyUrl

from app.schemas.links import ShortLink
from app.services.link_shortening import LinkShorteningService
from .dependecies import get_current_user

router = APIRouter(tags=["Сокращение ссылок"])


@router.post("/api/short", status_code=status.HTTP_201_CREATED)
async def short_link(
    url: AnyUrl, user_id: int = Depends(get_current_user)
) -> ShortLink:

    link = await LinkShorteningService.short_link(url=str(url), user_id=user_id)
    data = {"short_link": link}
    return JSONResponse(status_code=201, content=data)


@router.get("/{link_hash}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_user(link_hash: str) -> RedirectResponse:
    url = await LinkShorteningService.get_link_from_hash(hash=link_hash)
    return RedirectResponse(url)
