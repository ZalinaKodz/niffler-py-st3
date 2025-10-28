import json
import uuid
from collections.abc import Sequence
from typing import Optional, List

import allure
from allure_commons.types import AttachmentType
from sqlalchemy import create_engine, Engine, event
from sqlmodel import Session, select

from models.category import Category
from models.spend import Spend
from models.user import UserName


class SpendDb:
    engine: Engine

    def __init__(self, db_url: str):
        with allure.step(f"Initialize database connection to {db_url}"):
            self.engine = create_engine(db_url)
            event.listen(self.engine, "do_execute", self._log_sql_query)

    @staticmethod
    def _log_sql_query(cursor, statement, parameters, context):
        """Логирование SQL запросов в Allure отчет"""
        query = statement % parameters
        allure.attach(
            query,
            name=f"SQL Query to {context.engine.url.database}",
            attachment_type=AttachmentType.TEXT
        )

    @allure.step("Get categories for user '{username}'")
    def get_categories(self, username: str) -> List[Category]:
        with Session(self.engine) as session:
            categories = session.exec(select(Category).where(Category.username == username)).all()
            self._attach_json_result(categories, "Categories")
            return categories

    @allure.step("Get category by ID '{category_id}'")
    def get_category_by_id(self, category_id: uuid.UUID) -> Optional[Category]:
        with Session(self.engine) as session:
            category = session.get(Category, category_id)
            self._attach_json_result(category, "Category")
            return category

    @allure.step("Get category by name '{category_name}'")
    def get_category_by_name(self, category_name: str) -> Optional[Category]:
        with Session(self.engine) as session:
            category = session.exec(select(Category).where(Category.name == category_name)).first()
            self._attach_json_result(category, "Category")
            return category

    @allure.step("Delete category with ID '{category_id}'")
    def delete_category(self, category_id: uuid.UUID) -> None:
        with Session(self.engine) as session:
            category = session.get(Category, category_id)
            if category:
                self._attach_json_result(category, "Category to delete")
                session.delete(category)
                session.commit()
                allure.attach("Category deleted successfully", name="Result")

    @allure.step("Delete category by name '{category_name}'")
    def delete_category_by_name(self, category_name: str) -> None:
        with Session(self.engine) as session:
            category = session.exec(select(Category).where(Category.name == category_name)).first()
            if category:
                self._attach_json_result(category, "Category to delete")
                session.delete(category)
                session.commit()
                allure.attach("Category deleted successfully", name="Result")

    @allure.step("Get spend by ID '{spend_id}'")
    def get_spend_by_id(self, spend_id: uuid.UUID) -> Optional[Spend]:
        with Session(self.engine) as session:
            spend = session.get(Spend, spend_id)
            self._attach_json_result(spend, "Spend")
            return spend

    @allure.step("Delete spend with ID '{spend_id}'")
    def delete_spend(self, spend_id: uuid.UUID) -> None:
        with Session(self.engine) as session:
            spend = session.get(Spend, spend_id)
            if spend:
                self._attach_json_result(spend, "Spend to delete")
                session.delete(spend)
                session.commit()
                allure.attach("Spend deleted successfully", name="Result")

    @allure.step("Update category '{category_id}' with new name '{new_name}'")
    def update_category(self, category_id: uuid.UUID, new_name: str) -> None:
        with Session(self.engine) as session:
            category = session.get(Category, category_id)
            if category:
                self._attach_json_result({
                    "old_name": category.name,
                    "new_name": new_name
                }, "Update data")
                category.name = new_name
                session.commit()
                self._attach_json_result(category, "Updated category")

    @staticmethod
    def _attach_json_result(data, name: str) -> None:
        """Утилита для прикрепления данных в Allure отчет"""
        if data is None:
            return
        if not isinstance(data, (list, dict)):
            data = data.dict()
        allure.attach(
            json.dumps(data, indent=2, default=str),
            name=name,
            attachment_type=AttachmentType.JSON
        )

    def get_user(self, username: str) -> Sequence[UserName]:
        with Session(self.engine) as session:
            statement = select(UserName).where(UserName.username == username)
            return session.exec(statement).one()