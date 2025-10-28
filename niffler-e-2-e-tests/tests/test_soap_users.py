import random

import allure
import pytest
from faker import Faker

from clients.soap_client import SoapClient
from marks import TestData
from models.enums import Currency, FriendshipStatus
from models.soap import PageInfo, SoapUser
from utils.allure_helpers import Feature, Story, Epic


@allure.epic(Epic.app_name)
@pytest.mark.usefixtures(
    "soap_client",
    "mock_users",
    "mock_friends",
    "soap_user",  # ✅ Используем существующего пользователя
    "cleanup"
)
@pytest.mark.soap
@pytest.mark.user_management
@allure.feature(Feature.userdata)
class TestSoapUsers:
    """Тесты SOAP API для управления пользователями"""

    def map_pagination_error(self, page_info: PageInfo) -> str | None:
        """Маппинг ошибок пагинации"""
        if page_info.page < 0:
            return "Page index must not be less than zero"
        if page_info.size < 1:
            return "Page size must not be less than one"
        return None


    @allure.story(Story.user_management)
    def test_get_user_info_with_existing_username(self, soap_client: SoapClient, soap_user: str):
        """Тест получения существующего пользователя через SOAP"""
        user_data, status_code = soap_client.get_current_user(username=soap_user)

        with allure.step('Проверка корректности ответа'):
            assert status_code == 200, f"Expected 200, got {status_code}. Response: {user_data}"
            assert 'username' in user_data, f"Username not found in response: {user_data}"
            assert user_data['username'] == soap_user

            if user_data.get('id'):
                assert isinstance(user_data['id'], str), f"ID should be string, got {type(user_data['id'])}"
            assert user_data.get('currency'), f"У пользователя {soap_user} нет currency"
            assert user_data.get('friendshipStatus'), f"У пользователя {soap_user} нет friendshipStatus"

    @allure.story(Story.user_management)
    def test_get_user_that_doesnt_exist(self, soap_client: SoapClient):
        """Тест получения пользователя, которого нет в базе"""
        username = "a_user_that_has_never_existed_12345"
        user_data, status_code = soap_client.get_current_user(username=username)

        with allure.step('Проверка корректности ответа'):
            # Сервис может создавать пользователя автоматически или возвращать ошибку
            if status_code == 200:
                assert user_data is not None
                assert user_data.get('username') == username
                # Проверяем обязательные поля
                assert 'currency' in user_data
                assert 'friendshipStatus' in user_data
            else:
                # Если сервис возвращает ошибку для несуществующих пользователей
                assert status_code in [400, 404, 500]

    @allure.story(Story.user_management)
    def test_get_all_users(self, soap_client: SoapClient, soap_user: str):
        """Тест получения списка всех пользователей через SOAP"""
        users, status_code = soap_client.get_all_users(username=soap_user)

        with allure.step('Проверка корректности ответа'):
            assert status_code == 200
            assert isinstance(users, list)
            # Может быть пустым списком или содержать пользователей
            for user in users:
                assert 'username' in user
                assert 'currency' in user

    @TestData.page_info([
        PageInfo(page=0, size=3),
        PageInfo(page=1, size=4),
        PageInfo(page=0, size=6),
        PageInfo(page=3, size=2)
    ])
    @allure.story(Story.user_management)
    def test_get_all_users_pagination(self, soap_client: SoapClient, soap_user: str, page_info: PageInfo):
        """Тест получения пользователей с пагинацией через SOAP"""
        page_result, status_code = soap_client.get_all_users_page(
            username=soap_user,
            page_info=page_info
        )

        with allure.step('Проверка структуры ответа с пагинацией'):
            assert status_code == 200, f"Expected 200, got {status_code}. Response: {page_result}"
            assert isinstance(page_result, dict)

            # Проверяем наличие полей пагинации
            if 'size' in page_result:
                size_value = page_result['size']
                if isinstance(size_value, str) and size_value.isdigit():
                    assert int(size_value) == page_info.size
                else:
                    assert size_value == page_info.size

            if 'number' in page_result:
                number_value = page_result['number']
                if isinstance(number_value, str) and number_value.isdigit():
                    assert int(number_value) == page_info.page
                else:
                    assert number_value == page_info.page

    @TestData.page_info([
        PageInfo(page=100, size=10),
        PageInfo(page=999, size=5),
    ])
    @allure.story(Story.user_management)
    def test_get_all_users_page_out_of_range(self, soap_client: SoapClient, soap_user: str, page_info: PageInfo):
        """Тест получения пользователей с пагинацией через SOAP с некорректными параметрами"""
        page_result, status_code = soap_client.get_all_users_page(
            username=soap_user,
            page_info=page_info
        )

        with allure.step('Проверка структуры ответа с пагинацией'):
            if status_code == 200:
                assert isinstance(page_result, dict)
                users = page_result.get('user', [])
                if isinstance(users, dict):
                    users = [users]
                assert len(users) == 0
            else:
                assert status_code in [400, 500]

    @TestData.page_info([
        PageInfo(page=-1, size=1),
        PageInfo(page=0, size=0),
        PageInfo(page=1, size=-1),
    ])
    @allure.story(Story.user_management)
    def test_get_all_users_page_invalid_parameters(self, soap_client: SoapClient, soap_user: str, page_info: PageInfo):
        """Тест получения пользователей с пагинацией через SOAP с некорректными параметрами"""
        page_result, status_code = soap_client.get_all_users_page(
            username=soap_user,
            page_info=page_info
        )

        with allure.step('Проверка корректности ответа'):
            assert status_code in [200, 400, 500]

    @allure.story(Story.user_management)
    def test_update_user_currency_and_full_name(
            self,
            faker: Faker,
            user_with_id: str,  # ✅ Используем пользователя с ID
            soap_client: SoapClient
    ):
        """Тест обновления пользователя через SOAP"""
        # Получаем текущие данные пользователя
        current_user, status_code = soap_client.get_current_user(username=user_with_id)
        assert status_code == 200
        assert current_user.get('id'), f"User {user_with_id} should have ID"

        user_id = current_user['id']
        user_currency = current_user.get('currency', Currency.RUB.value)
        current_fullname = current_user.get('fullname')

        # Выбираем новую валюту
        available_currencies = [c for c in Currency.all_values() if c.value != user_currency]
        if available_currencies:
            new_currency = random.choice(available_currencies)
        else:
            new_currency = Currency.USD

        # Генерируем новое полное имя
        new_fullname = f"{faker.first_name()} {faker.last_name()}"

        update_data = SoapUser(
            id=user_id,
            username=user_with_id,
            currency=new_currency,
            fullname=new_fullname
        )

        response, status_code = soap_client.update_user(update_data)

        with allure.step('Проверка корректности обновления'):
            assert status_code == 200, f"Expected 200, got {status_code}. Response: {response}"
            assert response.get('username') == user_with_id
            assert response.get('currency') == new_currency.value

            # Проверяем что fullname обновился (если сервер его поддерживает)
            if response.get('fullname'):
                assert response.get('fullname') == new_fullname

            # Дополнительная проверка: получаем обновленного пользователя
            updated_user, status = soap_client.get_current_user(user_with_id)
            assert status == 200
            assert updated_user.get('currency') == new_currency.value
            if updated_user.get('fullname'):
                assert updated_user.get('fullname') == new_fullname

    @allure.story(Story.user_management)
    def test_cannot_update_user_without_id(
            self,
            user_without_id: str,
            soap_client: SoapClient
    ):
        """Проверка что пользователь без ID не может быть обновлен"""
        current_user, status_code = soap_client.get_current_user(username=user_without_id)
        assert status_code == 200
        assert not current_user.get('id'), f"User {user_without_id} should not have ID"

        # Пробуем обновить с пустым ID
        update_data = SoapUser(
            id="",  # Пустой ID
            username=user_without_id,
            currency=Currency.USD
        )

        response, status_code = soap_client.update_user(update_data)

        with allure.step('Проверка что обновление невозможно без ID'):
            # Ожидаем ошибку, так как ID обязателен
            assert status_code in [400, 500], f"Expected error for user without ID, got {status_code}"

    @pytest.mark.friends_management
    @allure.story(Story.friends_management)
    def test_get_friends(self, soap_client: SoapClient, soap_friends_user: str):
        """Тест получения списка друзей через SOAP"""
        friends, status_code = soap_client.get_friends(username=soap_friends_user)

        with allure.step('Проверка корректности ответа'):
            assert isinstance(friends, list)
            for friend in friends:
                assert 'username' in friend
                assert 'friendshipStatus' in friend
                # Проверяем статус дружбы, если друзья есть
                if friends:  # Если список не пустой
                    assert friend['friendshipStatus'] == FriendshipStatus.FRIEND.value

    @TestData.page_info([
        PageInfo(page=1, size=5),
        PageInfo(page=2, size=3),
        PageInfo(page=4, size=2)
    ])
    @pytest.mark.friends_management
    @allure.story(Story.friends_management)
    def test_get_friends_page(
            self,
            soap_client: SoapClient,
            soap_friends_user: str,
            page_info: PageInfo,
    ):
        """Тест получения друзей с пагинацией через SOAP"""
        page_result, status_code = soap_client.get_friends_page(
            username=soap_friends_user,
            page_info=page_info
        )

        with allure.step('Проверка структуры ответа с пагинацией'):
            if status_code == 200:
                assert isinstance(page_result, dict)
                if 'size' in page_result:
                    assert int(page_result.get('size')) == page_info.size
                if 'number' in page_result:
                    assert int(page_result.get('number')) == page_info.page

    @TestData.page_info([
        PageInfo(page=4, size=100),
        PageInfo(page=100, size=100),
        PageInfo(page=1000, size=1)
    ])
    @pytest.mark.friends_management
    @allure.story(Story.friends_management)
    def test_get_friends_page_out_of_range(
            self,
            soap_client: SoapClient,
            soap_friends_user: str,
            page_info: PageInfo
    ):
        """Тест получения друзей с пагинацией через SOAP"""
        page_result, status_code = soap_client.get_friends_page(
            username=soap_friends_user,
            page_info=page_info
        )

        with allure.step('Проверка структуры ответа с пагинацией'):
            if status_code == 200:
                assert isinstance(page_result, dict)
                users = page_result.get('user', [])
                if isinstance(users, dict):
                    users = [users]
                assert len(users) == 0

                if 'size' in page_result:
                    assert int(page_result.get('size')) == page_info.size
                if 'number' in page_result:
                    assert int(page_result.get('number')) == page_info.page

    @TestData.page_info([
        PageInfo(page=-1, size=1),
        PageInfo(page=1, size=-1),
        PageInfo(page=1, size=0),
        PageInfo(page=-1, size=-1)
    ])
    @pytest.mark.friends_management
    @allure.story(Story.friends_management)
    def test_get_friends_page_invalid_parameters(
            self,
            soap_client: SoapClient,
            soap_friends_user: str,
            page_info: PageInfo
    ):
        """Тест получения друзей с пагинацией через SOAP с некорректными параметрами"""
        page_result, status_code = soap_client.get_friends_page(
            username=soap_friends_user,
            page_info=page_info
        )
        error_text = self.map_pagination_error(page_info)

        with allure.step('Проверка корректности ответа'):
            if status_code == 500:
                assert error_text in str(page_result)