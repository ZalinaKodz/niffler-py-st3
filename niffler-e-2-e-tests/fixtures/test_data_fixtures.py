import logging
import uuid
from typing import Any

import pytest
import random
import time
from faker import Faker
from datetime import datetime, timedelta

from clients.category_client import CategoryClient
from clients.spends_client import SpendClient
from models.spend import SpendModelAdd, SpendModel
from collections.abc import Generator

logger = logging.getLogger(__name__)
fake = Faker()

@pytest.fixture
def random_category() -> str:
    return f"{fake.word(part_of_speech='noun')} {fake.word(part_of_speech='noun')}"

@pytest.fixture
def random_amount() -> int:
    return fake.random_int(100, 9999)

@pytest.fixture
def new_spending_data(random_category: str, random_amount: int) -> dict:
    return {
        "amount": str(random_amount),
        "category": random_category,
    }

@pytest.fixture
def fake_name() -> str:
    return fake.first_name()

def get_past_date(days: int = 1) -> str:
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


DEFAULT_CURRENCY = "USD"
DEFAULT_USERNAME = "test_user"
MAX_AMOUNT = 10000.0
MIN_AMOUNT = 0.01

# Фикстуры данных
@pytest.fixture
def random_username() -> str:
    return f"user_{fake.user_name()}_{int(time.time())}"

@pytest.fixture
def random_category_name() -> str:
    return f"Category_{fake.word().capitalize()}_{uuid.uuid4().hex[:4]}"

@pytest.fixture
def random_spend_description() -> str:
    return f"Spend on {fake.word()} - {fake.sentence(nb_words=3)}"

@pytest.fixture
def random_amount() -> float:
    return round(fake.pyfloat(min_value=MIN_AMOUNT, max_value=MAX_AMOUNT), 2)

@pytest.fixture
def past_date() -> str:
    return (datetime.now() - timedelta(days=fake.random_int(min=1, max=365))).strftime("%Y-%m-%d")

@pytest.fixture
def complete_spending_data():
    return {
        "amount": round(random.uniform(10, 1000), 2),
        "currency": random.choice(["USD", "EUR", "GBP"]),
        "spendDate": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "description": f"Test spend {uuid.uuid4().hex[:6]}",
        "category": {"name": f"TestCategory_{uuid.uuid4().hex[:4]}"},
        "username": f"testuser_{uuid.uuid4().hex[:8]}"
    }

@pytest.fixture
def test_category(category_client: CategoryClient, random_category_name: str) -> Generator[Any, None, None]:
    """Фикстура создает тестовую категорию и возвращает её, удаляет после теста"""
    category = category_client.add_category(category_name=random_category_name)
    yield category
    try:
        category_client.archive_category(category.id)
    except Exception as e:
        logger.warning(f"Failed to cleanup category: {str(e)}")


@pytest.fixture
def test_spend(
        spend_client: SpendClient,
        test_category: Any,
        random_username: str,
        random_spend_description: str,
        random_amount: float,
        past_date: str
) -> SpendModel:
    """Фикстура создает тестовый расход и возвращает его, удаляет после теста"""
    spend_data = {
        "amount": random_amount,
        "currency": DEFAULT_CURRENCY,
        "spendDate": past_date,
        "description": random_spend_description,
        "category": {"id": str(test_category.id), "name": test_category.name},
        "username": random_username
    }
    spend = spend_client.add_spend(SpendModelAdd(**spend_data))
    yield spend
    try:
        spend_client.delete_spend([spend.id])
    except Exception as e:
        logger.warning(f"Failed to cleanup spend: {str(e)}")