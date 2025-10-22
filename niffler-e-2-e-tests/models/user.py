from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel
from sqlmodel import SQLModel, Field

from models.enums import Currency


class UserName(BaseModel):
    username: str


class User(SQLModel, table=True):

    id: str = Field(default=None, primary_key=True)
    username: str
    currency: str = "RUB"
    firstname: str
    surname: str
    photo: str | None = None
    photo_small: str | None = None
    full_name: str


@dataclass
class UserData:
    id: str
    username: str
    currency: Currency
    firstname: Optional[str] = None
    surname: Optional[str] = None
    full_name: Optional[str] = None
    photo: Optional[str] = None
    photo_small: Optional[str] = None