import logging
import time
import uuid
from typing import Any, Generator, Tuple
from faker import Faker
import pytest
import allure
from datetime import datetime, timedelta
import requests
from pydantic import ValidationError
from clients.category_client import CategoryClient
from clients.spends_client import SpendClient
from databases.spend_db import SpendDb
from fixtures.test_data_fixtures import get_past_date
from models.spend import SpendModelAdd, ErrorResponseModel, SpendModelEdit, SpendModel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@pytest.mark.api
@allure.feature("Spend API")
class TestSpendAPI:
    @allure.title("Test spend creation with different scenarios")
    @pytest.mark.parametrize("test_data,expected_status,expected_error", [
        # Успешное создание траты
        (
                {
                    "amount": 100.0,
                    "currency": "USD",
                    "spendDate": "2023-01-01",
                    "description": "Valid spend",
                    "category": {"name": "New Category"},
                },
                201,
                None
        ),
        # Невалидные данные
        (
                {
                    "amount": -100.0,
                    "currency": "USD",
                    "spendDate": "2023-01-03",
                    "description": "",
                    "category": {"name": ""},
                },
                400,
                "Amount should be greater than 0.01"
        ),
        # Граничные значения
        (
                {
                    "amount": 0.01,  # Минимально допустимое значение
                    "currency": "USD",
                    "spendDate": "2023-01-01",
                    "description": "Min amount spend",
                    "category": {"name": "Boundary Check"},
                },
                201,
                None
        )
    ])
    def test_create_spend_with_model(self, random_username: str, test_data: dict[str, Any],
                                     expected_status: int, expected_error: str, spend_client: SpendClient):
        """Test spend creation with various scenarios"""
        test_data["username"] = random_username
        spend_data = SpendModelAdd(**test_data)

        try:
            response = spend_client.add_spend(spend_data)

            if expected_status >= 400:
                assert isinstance(response, ErrorResponseModel)
                assert response.status == expected_status
                if expected_error:
                    assert expected_error in response.detail
            else:
                assert isinstance(response, SpendModel)
                assert response.amount == test_data["amount"]
                assert response.currency == test_data["currency"]
                assert response.description == test_data["description"]
                assert response.category.name == test_data["category"]["name"]

        except Exception as e:
            if expected_status < 400:
                pytest.fail(f"Unexpected error: {str(e)}")
            elif expected_status == 400:
                if hasattr(e, 'response'):
                    error_data = e.response.json()
                    assert error_data.get('status') == 400
                    if expected_error:
                        assert expected_error in error_data.get('detail', '')
                else:
                    pytest.fail(f"Expected HTTP 400 error, got: {str(e)}")

    @allure.title("Get spend by ID with validated data")
    def test_get_spend_by_id(self, test_spend: SpendModel, spend_client: SpendClient):
        """Test retrieving spend by ID using validated data structure"""
        retrieved = spend_client.get_spend_by_id(test_spend.id)

        assert isinstance(retrieved, SpendModel)
        assert retrieved.id == test_spend.id
        assert float(retrieved.amount) == float(test_spend.amount)
        assert retrieved.currency == test_spend.currency
        assert retrieved.description == test_spend.description
        assert retrieved.category.name == test_spend.category.name

    @allure.title("Edit existing spend with valid data")
    def test_edit_spend(self, test_spend: SpendModel, spend_client: SpendClient, random_username: str):
        """Test editing existing spend with validated data structure"""
        updated_data = {
            "id": str(test_spend.id),
            "amount": float(test_spend.amount) + 100,
            "currency": "EUR",
            "spendDate": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "description": f"Updated {test_spend.description}",
            "category": {
                "id": str(test_spend.category.id),
                "name": f"Updated {test_spend.category.name}"
            },
            "username": random_username
        }

        logger.debug(f"Attempting to edit spend with data: {updated_data}")
        updated_spend = spend_client.edit_spend(SpendModelEdit(**updated_data))

        assert updated_spend.id == test_spend.id
        assert float(updated_spend.amount) == updated_data["amount"]
        assert updated_spend.currency == updated_data["currency"]
        assert updated_spend.description == updated_data["description"]
        assert updated_spend.category.name == updated_data["category"]["name"]
        assert updated_spend.spendDate.strftime("%Y-%m-%d") == updated_data["spendDate"]

    @allure.title("Create spend with invalid data")
    def test_create_spend_invalid_data(self, spend_client: SpendClient):
        invalid_data = {
            "amount": "not_a_number",
            "currency": "INVALID",
            "spendDate": "invalid_date_format",
            "description": "",
            "category": {
                "id": "123",
                "name": "Test",
                "username": "user"
            }
        }

        error_response = spend_client.add_spend_error(invalid_data)

        assert isinstance(error_response, ErrorResponseModel)
        assert error_response.status == 400

        error_msg = error_response.detail.lower()
        valid_errors = ["validation", "invalid", "failed", "error", "request"]
        assert any(err in error_msg for err in valid_errors), \
            f"Expected message containing one of {valid_errors}, got: '{error_msg}'"

    @allure.title("Test spend creation with SQL injection attempt")
    def test_sql_injection_attempt(self, spend_client: SpendClient, random_username: str):
        """Test that SQL injection attempts are properly handled"""
        malicious_data = {
            "amount": 100.0,
            "currency": "USD",
            "spendDate": "2023-01-01",
            "description": "'; DROP TABLE spends; --",
            "category": {"name": "Test' OR '1'='1"},
            "username": random_username
        }

        response = spend_client.add_spend(SpendModelAdd(**malicious_data))

        # Проверяем что система не упала и обработала запрос
        assert isinstance(response, (SpendModel, ErrorResponseModel))
        if isinstance(response, SpendModel):
            # Если запрос прошел, проверяем что данные сохранены как есть (без выполнения инъекции)
            assert response.description == malicious_data["description"]
            assert response.category.name == malicious_data["category"]["name"]


@allure.feature("Integration Tests")
class TestIntegration:
    @allure.title("Full user flow")
    def test_full_flow(
            self,
            category_client: CategoryClient,
            spend_client: SpendClient,
            spend_db: SpendDb
    ):
        # 1. Create category
        category_name = f"FlowCategory_{uuid.uuid4().hex[:6]}"
        category = category_client.add_category(category_name=category_name)

        # 2. Create spend
        spend_data = {
            "amount": 100.0,
            "currency": "USD",
            "spendDate": get_past_date(),
            "description": "Integration test",
            "category": {
                "id": str(category.id),
                "name": category.name
            },
            "username": "test_user"
        }
        spend = spend_client.add_spend(SpendModelAdd(**spend_data))

        # 3. Verify
        retrieved = spend_client.get_spend_by_id(spend.id)
        assert retrieved.category.id == category.id

        # 4. Cleanup
        spend_client.delete_spend([spend.id])
        spend_db.delete_category(category.id)