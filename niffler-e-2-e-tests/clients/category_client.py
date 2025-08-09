from typing import Optional
import uuid

import allure

from models.category import  CategoryModel
from utils.sessions import BaseSession


class CategoryClient:
    session: BaseSession

    def __init__(self, session: BaseSession) -> None:
        self.session = session

    @allure.step('[API] Get all categories: exclude_archived={exclude_archived}')
    def get_all_categories(self, exclude_archived: bool = False) -> list[CategoryModel]:
        response = self.session.get(
            "/api/categories/all",
            params={"excludeArchived": exclude_archived}
        )
        return [CategoryModel.model_validate(item) for item in response.json()]

    @allure.step('[API] Add category: category_name={category_name}')
    def add_category(self, category_name: str) -> CategoryModel:
        payload = {"name": category_name}
        response = self.session.post(
            "/api/categories/add",
            json=payload
        )
        return CategoryModel.model_validate(response.json())

    @allure.step("Update category")
    def update_category(self, category: dict) -> CategoryModel:
        """Обновление существующей категории"""
        required_fields = ["id", "name", "username"]
        for field in required_fields:
            if field not in category:
                raise ValueError(f"Missing required field: {field}")

        response = self.session.patch(
            "/api/categories/update",
            json=category
        )
        response.raise_for_status()
        return CategoryModel.model_validate(response.json())


    @allure.step("Archive category {category_id}")
    def archive_category(
            self,
            category_id: uuid.UUID,
            name: str,
            username: Optional[str] = None
    ) -> CategoryModel:
        """Архивация категории"""
        username = username or self.settings.TEST_USERNAME
        payload = {
            "id": str(category_id),
            "name": name,
            "username": username,
            "archived": True  # Главное изменение - устанавливаем флаг archived=True
        }

        response = self.session.patch(
            "/api/categories/update",
            json=payload
        )
        response.raise_for_status()
        return CategoryModel.model_validate(response.json())