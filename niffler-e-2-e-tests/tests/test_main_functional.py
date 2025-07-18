import re

import pytest
from _pytest.logging import caplog

from playwright.sync_api import expect, Page
import logging

from pages.spending_page import SpendingPage
from pages.profile_page import ProfilePage


class TestSpendingFunctionality:
    @pytest.fixture(autouse=True)
    def setup(self, spending_page: SpendingPage):
        """Общая настройка для всех тестов трат"""
        spending_page.navigate_to_spending()
        yield

    def test_add_spending(self, spending_page: SpendingPage, new_spending_data: dict):
        spending_page.add_spending(**new_spending_data)
        expect(spending_page.success_message).to_be_visible()

    def test_add_spending_without_category(self, spending_page: SpendingPage, new_spending_data: dict):
        spending_page.add_spending(amount=new_spending_data["amount"], category="")
        expect(spending_page.error_message).to_have_text(SpendingPage.REQUIRED_CATEGORY_MESSAGE)

    def test_create_and_delete_spending(self, spending_page: SpendingPage, new_spending_data: dict, caplog):
        caplog.set_level(logging.INFO)

        # Создание
        spending_page.add_spending(**new_spending_data)
        expect(spending_page.get_spending_row(new_spending_data)).to_be_visible()

        # Удаление
        spending_page.delete_spending(**new_spending_data)
        expect(spending_page.get_spending_row(new_spending_data)).not_to_be_visible()

    def test_create_invalid_spend(self, spending_page: SpendingPage):
        """Тест создания траты с невалидной суммой"""
        spending_page.add_spending(amount="0", category="Test")
        expect(spending_page.page.get_by_text(SpendingPage.INVALID_AMOUNT_MESSAGE)).to_be_visible()

    def test_cancel_button(self, spending_page: SpendingPage):
        """Тест работы кнопки отмены"""
        # Заполняем форму
        spending_page.amount_field.fill("500")
        spending_page.category_field.fill("Test")

        # Нажимаем Cancel
        spending_page.cancel_button.click()

        # Проверяем редирект
        expect(spending_page.page).to_have_url(re.compile(r".*/main"))

    def test_delete_all_spendings(self, spending_page: SpendingPage, new_spending_data: dict, caplog):
        caplog.set_level(logging.INFO)

        # Создаем тестовую трату
        spending_page.add_spending(**new_spending_data)

        # Удаляем все, если есть
        if spending_page.has_any_spendings():
            spending_page.delete_all_spendings()
            expect(spending_page.no_spendings_message).to_be_visible()
        else:
            pytest.skip("Нет трат для удаления")


class TestProfileFunctionality:
    def test_profile_update(self, profile_page: ProfilePage, fake_name: str):
        profile_page.update_profile_name(fake_name)
        expect(profile_page.name_field).to_have_value(fake_name)