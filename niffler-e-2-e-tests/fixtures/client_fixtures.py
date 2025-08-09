import logging
import uuid

import pytest

from faker import Faker

from clients.category_client import CategoryClient
from clients.spends_client import SpendClient
from conftest import Settings
from databases.spend_db import SpendDb
from utils.sessions import BaseSession
from utils.test_utils import Verify

logger = logging.getLogger(__name__)
fake = Faker()

@pytest.fixture(scope="session")
def base_session(settings: Settings, auth_token: str) -> BaseSession:
    return BaseSession(gateway_url=settings.GATEWAY_URL, token=auth_token)

@pytest.fixture(scope="session")
def spend_db(settings) -> SpendDb:
    return SpendDb(settings.SPEND_DB_URL)

@pytest.fixture(scope="session")
def category_client(base_session: BaseSession) -> CategoryClient:
    return CategoryClient(session=base_session)

@pytest.fixture(scope="session")
def spend_client(base_session: BaseSession) -> SpendClient:
    return SpendClient(session=base_session)


@pytest.fixture
def user_with_category_slots(category_client, settings):
    """Фикстура создает пользователя с гарантированно <8 категориями"""
    username = settings.TEST_USERNAME  # Используем из настроек

    # Остальная реализация фикстуры без изменений
    all_categories = category_client.get_all_categories()
    user_categories = [c for c in all_categories if getattr(c, 'username', None) == username]

    for category in user_categories[7:]:
        category_id = uuid.UUID(str(category.id)) if not isinstance(category.id, uuid.UUID) else category.id
        category_client.archive_category(category_id, category.name, username)

    yield username

    # Очистка
    all_categories = category_client.get_all_categories()
    user_categories = [c for c in all_categories if getattr(c, 'username', None) == username]
    for category in user_categories:
        category_id = uuid.UUID(str(category.id)) if not isinstance(category.id, uuid.UUID) else category.id
        category_client.archive_category(category_id, category.name, username)


@pytest.fixture(scope="session", autouse=True)
def global_cleanup(spend_client):
    """Глобальная очистка тестовых данных после всех тестов"""
    yield
    try:
        # Удаляем все тестовые траты
        spends = spend_client.get_all_spends(params={"username": "testuser_"})
        if spends:
            spend_client.delete_spend([s.id for s in spends])
    except Exception as e:
        logging.warning(f"Ошибка при глобальной очистке: {str(e)}")


@pytest.fixture
def verify():
    """Фикстура для проверок"""
    return Verify