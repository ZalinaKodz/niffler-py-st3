import uuid
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional


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


class Spend(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    amount: float
    currency: str
    spend_date: date = Field(default_factory=date.today)
    description: str
    username: str
    category_id: uuid.UUID = Field(foreign_key="category.id")

    # Добавляем связь с категорией
    category: Category = Relationship(back_populates="spends")


class SpendCreate(SQLModel):
    id: str
    spendDate: datetime
    currency: str
    amount: float
    description: str
    username: str
    category: Category