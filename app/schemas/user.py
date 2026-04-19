from typing import Optional
from pydantic import BaseModel


class UserBase(BaseModel):
    login: str
    password: str


class UserCreate(UserBase):
    username: str


class UserInDB(UserBase):
    hashed_password: str


class User(UserBase):
    id: Optional[str] = None


class AddUserResponce(BaseModel):
    user_id: int


class LoginResponce(BaseModel):
    message: str = "Login successful"
