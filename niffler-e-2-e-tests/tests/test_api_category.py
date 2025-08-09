import uuid
import pytest
import requests
import allure
from datetime import datetime


@allure.feature("Category API")
class TestCategoryAPI:
    @allure.title("Create new category - basic validation")
    def test_create_category_basic(self, category_client, verify):
        # Arrange
        category_name = f"TestCategory_{uuid.uuid4().hex[:6]}_{datetime.now().timestamp()}"

        # Act
        response = category_client.add_category(category_name=category_name)

        # Assert
        verify.category_structure(response)
        assert response.name == category_name
        assert response.archived is False

    @allure.title("Create category with user context")
    def test_create_category_for_user(self, category_client, user_with_category_slots, verify):
        # Arrange
        category_name = f"UserCategory_{uuid.uuid4().hex[:6]}"

        # Act
        response = category_client.add_category(category_name=category_name)

        # Assert
        verify.category_structure(response)
        assert response.name == category_name
        if hasattr(response, 'username'):
            assert response.username == user_with_category_slots

    @allure.title("Get all categories - structure validation")
    def test_get_all_categories(self, category_client, verify):
        # Act
        categories = category_client.get_all_categories()

        # Assert
        assert isinstance(categories, list)
        for category in categories[:3]:
            verify.category_structure(category)

    @allure.title("Update category - name change")
    def test_update_category_name(self, category_client, user_with_category_slots, verify):
        # Arrange
        category = category_client.add_category(category_name=f"Original_{uuid.uuid4().hex[:4]}")
        new_name = f"Updated_{uuid.uuid4().hex[:4]}"

        # Act
        updated = category_client.update_category({
            "id": str(category.id),
            "name": new_name,
            "username": user_with_category_slots
        })

        # Assert
        verify.category_structure(updated)
        assert updated.name == new_name
        assert str(updated.id) == str(category.id)

    @allure.title("Negative tests - invalid category names")
    @pytest.mark.parametrize("invalid_name,expected_error", [
        ("", "Category can not be blank"),
        ("   ", "Category can not be blank"),  # Только пробелы
        ("X" * 51, "Allowed category length"),
    ])
    def test_invalid_category_names(self, category_client, invalid_name, expected_error, verify):
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            category_client.add_category(category_name=invalid_name)

        assert exc_info.value.response.status_code == 400
        error_detail = exc_info.value.response.json().get("detail", "")
        assert expected_error in error_detail, f"Expected '{expected_error}' in '{error_detail}'"

    @allure.title("Archive category lifecycle")
    def test_archive_category(self, category_client, user_with_category_slots, verify):
        # Arrange
        category = category_client.add_category(category_name=f"ToArchive_{uuid.uuid4().hex[:4]}")

        # Act - Archive
        archived = category_client.update_category({
            "id": str(category.id),
            "name": category.name,
            "username": user_with_category_slots,
            "archived": True
        })

        # Assert
        verify.category_structure(archived)
        assert archived.archived is True
        assert str(archived.id) == str(category.id)

    @allure.title("Update non-existent category")
    def test_update_nonexistent_category(self, category_client, verify):
        # Arrange
        fake_id = str(uuid.uuid4())

        # Act & Assert
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            category_client.update_category({
                "id": fake_id,
                "name": "Ghost",
                "username": "test_user"
            })

        assert exc_info.value.response.status_code == 404
        assert "not found" in exc_info.value.response.text.lower()