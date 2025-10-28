from typing import Generator

import pytest
from faker import Faker

from conftest import Settings
from databases.user_db import UsersDb

from sqlmodel import create_engine, text
from models.user import User

@pytest.fixture
def users_db(settings: Settings) -> UsersDb:
    """Клиент для работы с БД пользователей"""
    return UsersDb(settings.USER_DB_URL)


@pytest.fixture
def fake() -> Faker:
    """Фикстура Faker для генерации тестовых данных"""
    return Faker()


@pytest.fixture(autouse=True)
def clean_test_data(users_db: UsersDb) -> Generator[list[str], None, None]:
    """
    Автоматическая очистка тестовых данных
    """
    test_usernames: list[str] = []
    yield test_usernames

    # Очистка данных - адаптируем под реальный API UsersDb
    if test_usernames:
        for username in test_usernames:
            try:
                # Предполагаем, что есть метод delete_user или аналогичный
                if hasattr(users_db, 'delete_user'):
                    users_db.delete_user(username)
                elif hasattr(users_db, 'execute'):
                    users_db.execute(f"DELETE FROM userdata WHERE username = '{username}'")
            except Exception as e:
                print(f"⚠️  Failed to clean user {username}: {e}")
