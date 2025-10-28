import allure
import pytest


from pytest import Item
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv


from clients.kafka_client import KafkaClient

pytest_plugins = [
    "fixtures.auth_fixtures",
    "fixtures.client_fixtures",
    "fixtures.grpc_fixtures",
    "fixtures.pages_fixtures",
    "fixtures.browser_fixtures",
    "fixtures.test_data_fixtures",
    "fixtures.allure_hooks",
    "fixtures.kafka_fixtures",
    "fixtures.soap_fixtures",
]


class Settings(BaseSettings):
    AUTH_URL: str = Field(default="http://auth.niffler.dc:9000")
    FRONTEND_URL: str = Field(default="http://frontend.niffler.dc")
    GATEWAY_URL: str = Field(default="http://gateway.niffler.dc:8090")
    API_BASE_URL: str = Field(default="http://gateway.niffler.dc:8090/swagger-ui")
    TEST_USERNAME: str = Field(default="test_user")
    TEST_PASSWORD: str = Field(default="test_password")
    SPEND_DB_URL: str = Field(default="postgresql+psycopg2://postgres:secret@localhost:5432/niffler-spend")
    AUTH_SECRET: str = Field(default="secret")
    USER_DB_URL: str = Field(default="postgresql+psycopg2://postgres:secret@localhost:5432/niffler-userdata")
    KAFKA_ADDRESS: str = Field(default="kafka_address")
    GRPC_URL: str = Field(default="localhost:8092")


    class ConfigDict:
        env_file = ".env"
        env_file_encoding = "utf-8"


@pytest.fixture(scope="session")
def settings():
    load_dotenv()
    return Settings()



@pytest.fixture(scope="session")
def auth_url(settings):
    return settings.AUTH_URL.rstrip('/')


@pytest.fixture(scope="session")
def frontend_url(settings):
    return settings.FRONTEND_URL.rstrip('/')


@pytest.fixture(scope="session")
def gateway_url(settings):
    return settings.GATEWAY_URL.rstrip('/')

@pytest.fixture(scope="session")
def kafka(settings):
    """Взаимодействие с Kafka"""
    with KafkaClient(settings) as k:
        yield k

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_call(item: Item):
    """Динамическое формирование заголовка теста из имени"""
    yield
    try:
        # Преобразуем test_some_feature -> "Some Feature"
        test_name = " ".join(item.name.split("_")[1:]).title()
        allure.dynamic.title(test_name)
    except Exception as e:
        print(f"Error setting dynamic title: {e}")