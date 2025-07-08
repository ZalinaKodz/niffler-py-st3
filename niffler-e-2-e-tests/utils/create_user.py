from faker import Faker
import random
import string
from typing import Dict

fake = Faker()

class UserDataFactory:
    @staticmethod
    def generate_valid_user() -> Dict[str, str]:
        """Генерация валидных тестовых данных"""
        username = f"user_{fake.user_name()}_{random.randint(1000, 9999)}"
        password = "".join(random.choices(
            string.ascii_letters + string.digits + "!@#$%^&*",
            k=random.randint(8, 12)
        ))
        return {
            "username": username,
            "password": password,
            "confirm_password": password
        }

    @staticmethod
    def generate_invalid_password_user() -> Dict[str, str]:
        """Генерация пользователя со слабым паролем"""
        return {
            "username": f"user_{fake.user_name()}",
            "password": "123",
            "confirm_password": "123"
        }

    @staticmethod
    def generate_mismatch_password_user() -> Dict[str, str]:
        """Генерация пользователя с несовпадающими паролями"""
        return {
            "username": f"user_{fake.user_name()}",
            "password": fake.password(),
            "confirm_password": fake.password()
        }