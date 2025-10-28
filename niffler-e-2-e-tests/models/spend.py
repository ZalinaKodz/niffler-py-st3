import uuid
from datetime import datetime, date, timezone

from pydantic import BaseModel, field_serializer
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

from models.category import CategoryModel, Category


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

class SpendModel(BaseModel):
    id: str
    amount: float
    description: str
    category: CategoryModel
    username: str
    spendDate: datetime
    currency: str

class SpendModelAdd(BaseModel):
    amount: float
    currency: str
    spendDate: str
    description: str
    category: dict

class SpendModelEdit(BaseModel):
    id: str
    amount: float
    description: str
    currency: str
    spendDate: datetime
    category: dict

    @field_serializer('spendDate')
    def serialize_spend_date(self, dt: datetime, _info):
        """Сериализует datetime в строку для JSON"""
        return dt.strftime("%Y-%m-%d")

    @classmethod
    def parse_date(cls, v):
        """Парсит строку в datetime при создании модели"""
        if isinstance(v, str):
            return datetime.strptime(v, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return v

class ErrorResponseModel(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str

class SpendCreate(BaseModel):
    id: uuid.UUID
    spendDate: str
    category: Category
    currency: str
    amount: str
    description: str
    username: str

class SpendResponseModel(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str

def add_spend(self, spend: SpendModelAdd) -> SpendResponseModel:
    response = self.session.post(
        "/api/spends/add",
        json=spend.model_dump()
    )
    return SpendResponseModel.model_validate(response.json())