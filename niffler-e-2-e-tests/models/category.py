import uuid
from typing import Optional

from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship


class CategoryModel(BaseModel):
    id: str
    name: str
    username: str
    archived: bool

class Category(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        nullable=False
    )
    name: str
    username: str
    archived: bool = False

    spends: list["Spend"] = Relationship(back_populates="category")