from typing import Optional

from models.enums import Currency
from models.user import UserData


class UserdataDb:
    """Mock класс для работы с базой данных пользователей"""

    def __init__(self, connection_string: str = None):
        # В реальном проекте здесь была бы инициализация подключения к БД
        pass

    def get_user_by_name(self, username: str) -> Optional[UserData]:
        """Получение пользователя по имени (mock реализация)"""
        # В реальном проекте здесь был бы SQL запрос
        return UserData(
            id="test-uuid-123",
            username=username,
            currency=Currency.RUB,
            firstname="Test",
            surname="User",
            full_name="Test User"
        )

    def update_user(self, user_data: UserData) -> bool:
        """Обновление пользователя (mock реализация)"""
        return True