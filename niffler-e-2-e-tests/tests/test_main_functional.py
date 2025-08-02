import re

import allure
import pytest

from playwright.sync_api import expect, Page


from pages.spending_page import SpendingPage
from pages.profile_page import ProfilePage


@allure.epic("Finance Application")
@allure.feature("Spending Management")
class TestSpendingFunctionality:
    @pytest.fixture(autouse=True)
    def setup(self, spending_page: SpendingPage):
        spending_page.navigate_to_spending()
        yield

    @allure.story("Adding spendings")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_add_spending(self, spending_page: SpendingPage, new_spending_data: dict):
        """Test successful spending creation"""
        spending_page.add_spending(**new_spending_data)
        expect(spending_page.success_message).to_be_visible()
        expect(spending_page.get_spending_row(new_spending_data)).to_be_visible()

    @allure.story("Validation")
    def test_add_spending_without_category(self, spending_page: SpendingPage, new_spending_data: dict):
        """Test validation when category is missing"""
        spending_page.add_spending(amount=new_spending_data["amount"], category="")
        expect(spending_page.error_message).to_have_text(SpendingPage.REQUIRED_CATEGORY_MESSAGE)

    @allure.story("Spending lifecycle")
    def test_create_and_delete_spending(self, spending_page: SpendingPage, new_spending_data: dict):
        """Test full spending lifecycle"""
        spending_page.add_spending(**new_spending_data)
        expect(spending_page.get_spending_row(new_spending_data)).to_be_visible()

        spending_page.delete_spending(**new_spending_data)
        expect(spending_page.get_spending_row(new_spending_data)).not_to_be_visible()

    @allure.story("Validation")
    def test_create_invalid_spend(self, spending_page: SpendingPage):
        """Test validation for invalid amount"""
        spending_page.add_spending(amount="0", category="Test")
        expect(spending_page.page.get_by_text(SpendingPage.INVALID_AMOUNT_MESSAGE)).to_be_visible()

    @allure.story("UI Behavior")
    def test_cancel_button(self, spending_page: SpendingPage):
        """Test cancel button functionality"""
        spending_page.amount_field.fill("500")
        spending_page.category_field.fill("Test")
        spending_page.cancel_button.click()
        expect(spending_page.page).to_have_url(re.compile(r".*/main"))

    @allure.story("Mass operations")
    def test_delete_all_spendings(self, spending_page: SpendingPage, new_spending_data: dict):
        """Test mass deletion of spendings"""
        spending_page.add_spending(**new_spending_data)

        if spending_page.has_any_spendings():
            spending_page.delete_all_spendings()
            expect(spending_page.no_spendings_message).to_be_visible()
        else:
            pytest.skip("No spendings available for deletion")


@allure.epic("Finance Application")
@allure.feature("Profile Management")
class TestProfileFunctionality:
    @allure.story("Profile updates")
    def test_profile_update(self, profile_page: ProfilePage, fake_name: str):
        """Test successful profile name update"""
        profile_page.navigate_to_profile()
        profile_page.update_profile_name(fake_name)
        expect(profile_page.name_field).to_have_value(fake_name)
        expect(profile_page.success_message).to_be_visible()