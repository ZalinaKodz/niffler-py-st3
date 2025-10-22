from typing import List

import pytest
from faker import Faker

from clients.soap_client import SoapClient
from databases.userdata_db import UserdataDb
from models.enums import Currency
from models.user import UserData


@pytest.fixture
def soap_client() -> SoapClient:
    """Фикстура для SOAP клиента"""
    return SoapClient()

@pytest.fixture
def userdata_db() -> UserdataDb:
    """Фикстура для базы данных пользователей"""
    return UserdataDb()

@pytest.fixture
def faker() -> Faker:
    """Фикстура для генерации тестовых данных"""
    return Faker()

@pytest.fixture
def user_with_id() -> str:
    """Фикстура для пользователя с ID"""
    return "qwerty"  # ✅ Единственный пользователь с ID

@pytest.fixture
def user_without_id() -> str:
    """Фикстура для пользователя без ID"""
    return "test_user"  # ✅ Любой пользователь без ID

@pytest.fixture
def soap_user(user_with_id: str) -> str:
    """Фикстура для имени тестового пользователя"""
    return user_with_id

@pytest.fixture
def soap_friends_user(user_with_id: str) -> str:
    """Фикстура для имени пользователя с друзьями"""
    return user_with_id

@pytest.fixture
def soap_actions_user(user_with_id: str) -> str:
    """Фикстура для имени пользователя для действий с друзьями"""
    return user_with_id

@pytest.fixture
def soap_friend_user(user_without_id: str) -> str:
    """Пользователь-друг (может быть без ID)"""
    return user_without_id

@pytest.fixture
def mock_users(faker: Faker) -> List[UserData]:
    """Фикстура для mock пользователей"""
    return [
        UserData(
            id=faker.uuid4(),
            username=faker.user_name(),
            currency=Currency.RUB
        ) for _ in range(5)
    ]

@pytest.fixture
def mock_friends(faker: Faker) -> List[UserData]:
    """Фикстура для mock друзей"""
    return [
        UserData(
            id=faker.uuid4(),
            username=f"friend_{i}",
            currency=Currency.RUB
        ) for i in range(3)
    ]

@pytest.fixture
def mock_friends_actions(faker: Faker) -> List[UserData]:
    """Фикстура для mock пользователей для тестирования действий с друзьями"""
    return [
        UserData(
            id=faker.uuid4(),
            username=f"action_friend_{i}",
            currency=Currency.RUB
        ) for i in range(5)
    ]


@pytest.fixture
def existing_soap_users(soap_client: SoapClient) -> List[str]:
    """Фикстура возвращает список реально существующих пользователей в системе"""
    test_usernames = ["test_user", "qwerty", "user1"]

    existing_users = []
    for username in test_usernames:
        user_data, status = soap_client.get_current_user(username)
        if status == 200:
            existing_users.append(username)

    if len(existing_users) < 2:
        pytest.skip("Need at least 2 existing users in system for friendship tests")

    return existing_users


@pytest.fixture
def soap_actions_user(existing_soap_users: List[str]) -> str:
    """Фикстура для имени реально существующего пользователя"""
    return existing_soap_users[0]  # Первый существующий пользователь


@pytest.fixture
def soap_friend_user(existing_soap_users: List[str]) -> str:
    """Фикстура для имени реально существующего друга"""
    return existing_soap_users[1]  # Второй существующий пользователь

@pytest.fixture(autouse=True)
def cleanup():
    """Фикстура для очистки тестовых данных"""
    yield