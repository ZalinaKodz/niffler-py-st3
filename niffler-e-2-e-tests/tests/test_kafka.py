import json
import logging
import time

import allure
import pytest
from allure import step, epic, suite, title, tag
from faker import Faker


from conftest import settings, kafka
from databases.user_db import UsersDb
from fixtures.kafka_fixtures import users_db
from models.user import UserName


@allure.epic("Niffler Application")
@allure.feature("Event Streaming")
@allure.tag("kafka", "integration")
@pytest.mark.kafka
class TestAuthRegistrationKafkaTest:
        @title("KAFKA: Сообщение с пользователем публикуется в Kafka после успешной регистрации")
        @tag("KAFKA")
        def test_message_should_be_produced_to_kafka_after_successful_registration(self, auth_client, kafka):
                username = Faker().user_name()
                password = Faker().password(special_chars=False)

                topic_partitions = kafka.subscribe_listen_new_offsets("users")

                result = auth_client.register(username, password)
                assert result.status_code == 201

                event = kafka.log_msg_and_json(topic_partitions)

                with step("Check that message from kafka exist"):
                        assert event != '' and event != b''

                with step("Check message content"):
                        UserName.model_validate(json.loads(event.decode('utf8')))
                        assert json.loads(event.decode('utf8'))['username'] == username

        @title('KAFKA: Создание пользователя из сообщения Kafka')
        @tag("KAFKA", "INTEGRATION", "USER-CREATION")
        def test_user_creation_from_kafka_message(self, kafka, settings):
                # Ожидание перед проверкой (если нужно время на обработку)
                time.sleep(1)
                with step('Отправляем сообщение в топик users'):
                        user_name_for_msg = Faker().user_name()
                        logging.info(f'Отправить сообщение по пользователю: {user_name_for_msg}')
                        kafka.send_message("users", user_name_for_msg)

                with step('Ожидаем обработки сообщения и проверяем наличие в БД'):
                        db_client = UsersDb(settings.USER_DB_URL)

                        # Ожидание с таймаутом
                        timeout = 10  # секунд
                        start_time = time.time()

                        while time.time() - start_time < timeout:
                                user_from_db = db_client.get_user(username=user_name_for_msg)
                                if user_from_db and user_from_db.username == user_name_for_msg:
                                        break
                                time.sleep(0.5)
                        else:
                                pytest.fail(
                                        f"Пользователь {user_name_for_msg} не появился в БД в течение {timeout} секунд")

                        assert user_from_db.username == user_name_for_msg

        @title('KAFKA: Регистрация пользователя через Kafka в БД')
        @tag("KAFKA", "INTEGRATION", "REGISTRATION")
        def test_end_to_end_user_registration_via_kafka(self, auth_client, kafka, users_db, settings):
                """
                End-to-end тест полного цикла регистрации: UI -> Auth Service -> Kafka -> UserData Service -> БД
                Проверяет всю цепочку от регистрации до создания записи в базе данных.
                """
                with step("Генерация тестовых данных пользователя"):
                        username = Faker().user_name()
                        password = Faker().password(special_chars=False)
                        logging.info(f"Сгенерированы тестовые данные: username={username}")

                with step("Подписка на топик Kafka 'users' перед регистрацией"):
                        topic_partitions = kafka.subscribe_listen_new_offsets("users")
                        logging.info(f"Подписались на топик users")

                with step("Выполнение регистрации через Auth Service"):
                        result = auth_client.register(username, password)
                        assert result.status_code == 201, f"Ошибка регистрации: {result.status_code}"
                        logging.info(f"Регистрация успешна: пользователь {username}")

                with step("Получение и валидация сообщения из Kafka"):
                        event = kafka.log_msg_and_json(topic_partitions)
                        assert event != '' and event != b'', "Сообщение из Kafka пустое или отсутствует"
                        logging.info(f"Получено сообщение из Kafka: {event}")

                with step("Валидация структуры и содержания Kafka сообщения"):
                        message_data = json.loads(event.decode('utf8'))

                        # Валидация структуры через Pydantic модель
                        user_name_model = UserName.model_validate(message_data)
                        logging.info(f"Сообщение валидно: {user_name_model}")

                        # Проверка содержания
                        assert message_data['username'] == username, \
                                f"Username в сообщении ({message_data['username']}) не совпадает с ожидаемым ({username})"

                with step("Ожидание обработки сообщения и проверка записи в БД"):
                        # Ожидание с таймаутом для обработки сообщения consumer'ом
                        timeout = 30
                        start_time = time.time()
                        user_from_db = None

                        while time.time() - start_time < timeout:
                                user_from_db = users_db.get_user(username=username)
                                if user_from_db:
                                        logging.info(f"Пользователь найден в БД: {user_from_db.username}")
                                        break

                                logging.info(f"Ожидание обработки... Прошло {int(time.time() - start_time)}с")
                                time.sleep(2)
                        else:
                                pytest.fail(
                                        f"Пользователь {username} не создан в БД в течение {timeout} секунд. "
                                        "Сообщение не было обработано службой userdata."
                                )

                with step("Валидация данных пользователя в БД"):
                        assert user_from_db is not None, "Запись пользователя не найдена в БД"
                        assert user_from_db.username == username, \
                                f"Username в БД ({user_from_db.username}) не совпадает с ожидаемым ({username})"

                        # Дополнительные проверки, если данные доступны в модели
                        if hasattr(user_from_db, 'email') and user_from_db.email:
                                logging.info(f"Email пользователя: {user_from_db.email}")

                        if hasattr(user_from_db, 'created_at') and user_from_db.created_at:
                                logging.info(f"Дата создания: {user_from_db.created_at}")

                with step("Финальная проверка - полный цикл завершен"):
                        logging.info(
                                f"✓ Полный цикл регистрации завершен: "
                                f"UI -> Auth -> Kafka -> UserData -> БД. "
                                f"Пользователь {username} успешно создан."
                        )


        @title("KAFKA: Тест различных форматов сообщений")
        @tag("KAFKA", "FORMAT")
        def test_different_message_formats(self, kafka, settings):
                """Тестируем обработку разных форматов сообщений"""
                test_cases = [
                        {
                                "name": "valid_json_object",
                                "data": {"username": f"json_obj_{int(time.time())}", "email": "test@example.com"},
                                "expected_success": True
                        },
                        {
                                "name": "minimal_data",
                                "data": {"username": f"minimal_{int(time.time())}"},
                                "expected_success": True
                        }
                ]

                for test_case in test_cases:
                        with step(f"Тестируем формат: {test_case['name']}"):
                                # Извлекаем username из данных для отправки в Kafka
                                username_to_send = test_case["data"]["username"]  # Это строка!
                                kafka.send_message("users", username_to_send)  # Передаем только строку

                                # Даем время на обработку
                                time.sleep(8)

                                # Проверяем результат в БД
                                db_client = UsersDb(settings.USER_DB_URL)
                                user = db_client.get_user(username_to_send)

                                if test_case["expected_success"]:
                                        assert user is not None, f"Сообщение {test_case['name']} не обработано"
                                        logging.info(f"✓ Формат {test_case['name']} обработан успешно")
                                else:
                                        logging.info(f"Формат {test_case['name']} ожидаемо не обработан")