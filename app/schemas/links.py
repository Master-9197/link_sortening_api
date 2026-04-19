from pydantic import BaseModel


class ShortLink(BaseModel):
    short_link: str
