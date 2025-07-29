import uuid

from sqlalchemy import create_engine, Engine
from sqlmodel import Session, select
from models.spend import Category, Spend


class SpendDb:
    engine: Engine

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)

    def get_categories(self, username: str):
        with Session(self.engine) as session:
            statement = select(Category).where(Category.username == username)
            return session.exec(statement).all()

    def get_category_by_id(self, category_id):
        with Session(self.engine) as session:
            statement = select(Category).where(Category.id == category_id)
            return session.exec(statement).first()

    def get_category_by_name(self, category_name):
        with Session(self.engine) as session:
            statement = select(Category).where(Category.name == category_name)
            return session.exec(statement).first()

    def delete_category(self, category_id: int):
        with Session(self.engine) as session:
            category = session.get(Category, category_id)
            session.delete(category)
            session.commit()

    def delete_category_by_name(self, category_name: str):
        with Session(self.engine) as session:
            statement = select(Category).where(Category.name == category_name)
            category = session.exec(statement).first()
            if category:
                session.delete(category)
                session.commit()

    def get_spend_by_id(self, spend_id):
        with Session(self.engine) as session:
            statement = select(Spend).where(Spend.id == spend_id)
            return session.exec(statement).first()

    def delete_spend(self, spend_id: int):
        with Session(self.engine) as session:
            spend = session.get(Spend, spend_id)
            if spend:
                session.delete(spend)
                session.commit()

    def update_category(self, category_id: uuid.UUID, new_name: str) -> None:
        """Обновляет название категории"""
        with Session(self.engine) as session:
            category = session.get(Category, category_id)
            if category:
                category.name = new_name
                session.commit()