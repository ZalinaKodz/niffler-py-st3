from typing import Optional

import allure
import pytest
from sqlalchemy import Engine, event
from pytest import Item, FixtureDef, FixtureRequest
from allure_commons.reporter import AllureReporter


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_fixture_setup(fixturedef: FixtureDef, request: FixtureRequest):
    yield
    logger = allure_logger(request.config)
    if logger and hasattr(logger, 'get_last_item'):
        scope_map = {'function': 'F', 'class': 'C', 'module': 'M', 'package': 'P', 'session': 'S'}
        scope_letter = scope_map.get(fixturedef.scope, fixturedef.scope[0].upper())
        fixture_name = " ".join(fixturedef.argname.split("_")).title()
        logger.get_last_item().name = f"[{scope_letter}] {fixture_name}"


def allure_logger(config) -> Optional[AllureReporter]:
    """Безопасное получение Allure логгера"""
    try:
        listener = config.pluginmanager.get_plugin("allure_listener")
        if hasattr(listener, 'allure_logger'):
            return listener.allure_logger
        return None
    except Exception as e:
        pytest.exit(f"Failed to get Allure logger: {e}")



@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_fixture_setup(fixturedef: FixtureDef, request: FixtureRequest):
    """Форматирование имен фикстур для Allure"""
    yield
    try:
        logger = allure_logger(request.config)
        if logger and hasattr(logger, 'get_last_item'):
            item = logger.get_last_item()

            # Маппинг scope к буквам
            scope_map = {
                'function': 'F',
                'class': 'C',
                'module': 'M',
                'package': 'P',
                'session': 'S'
            }
            scope_letter = scope_map.get(fixturedef.scope, fixturedef.scope[0].upper())

            # Форматирование имени: some_fixture -> "Some Fixture"
            fixture_name = " ".join(fixturedef.argname.split("_")).title()
            item.name = f"[{scope_letter}] {fixture_name}"
    except Exception as e:
        print(f"Error in fixture setup hook: {e}")


sql_queries = []

@event.listens_for(Engine, "before_cursor_execute")
def log_sql(conn, cursor, statement, parameters, context, executemany):
    sql_queries.append(f"SQL: {statement}\nParams: {parameters}")

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item):
    yield
    if hasattr(item, "rep_call") and item.rep_call.failed:
        # Прикрепляем SQL-логи только если они есть
        if sql_queries:
            allure.attach(
                "\n".join(sql_queries),
                name="SQL Queries",
                attachment_type=allure.attachment_type.TEXT
            )
        sql_queries.clear()