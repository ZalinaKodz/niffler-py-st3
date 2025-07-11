from faker import Faker
from playwright.sync_api import expect, Page

from pages.spending_page import SpendingPage
from pages.profile_page import ProfilePage


class TestSpendingFunctionality:
    def test_add_spending(
        self,
        spending_page: SpendingPage,
        random_category: str,
        random_amount: int
    ):
        spending_page.add_spending(
            amount=str(random_amount),
            category=random_category
        )
        expect(spending_page.success_message).to_be_visible()


    def test_add_spending_without_category(self,
            authenticated_page: Page,
            random_category: str,
            random_amount: int
    , spending_page
    ):
        """
        Test adding spending without category (should fail)
        """
        # Инициализируем SpendingPage
        spending_page = SpendingPage(authenticated_page)

        # Пытаемся добавить трату без категории
        spending_page.add_spending(
                amount=str(random_amount),
                category=""  # Пустая категория
            )

        # Проверяем, что появилось сообщение об ошибке
        expect(spending_page.error_message).to_be_visible()

        # Проверяем текст ошибки
        assert "Please choose category" in spending_page.error_message.text_content()


class TestProfileFunctionality:
    def test_profile_update(
        self,
        profile_page: ProfilePage,
        faker: Faker
    ):
        new_name = faker.first_name()
        profile_page.update_profile_name(new_name)
        expect(profile_page.name_field).to_have_value(new_name)