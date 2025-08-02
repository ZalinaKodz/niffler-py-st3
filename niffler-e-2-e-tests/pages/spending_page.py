from typing import Optional

import allure
from playwright.sync_api import Page, Locator


@allure.epic("Finance Application")
class SpendingPage:
    REQUIRED_CATEGORY_MESSAGE = "Please choose category"
    INVALID_AMOUNT_MESSAGE = "Amount has to be not less then 0.01"

    def __init__(self, page: Page):
        self.page = page
        self.amount_field = page.get_by_role("spinbutton", name="Amount")
        self.category_field = page.get_by_role("textbox", name="Add new category")
        self.add_button = page.get_by_role("button", name="Add")
        self.success_message = page.get_by_text("New spending is successfully")
        self.error_message = page.get_by_text("Please choose category")
        self.delete_spending_button = page.locator("#delete")
        self.delete_spending_dialog = page.get_by_role("dialog")
        self.delete_spending_dialog_button = self.delete_spending_dialog.get_by_role("button", name="Delete")
        self.delete_spending_popup = page.get_by_text("Spendings succesfully deleted")
        self.delete_button = page.get_by_role("button", name="Delete")
        self.cancel_button = self.page.get_by_role("button", name="Cancel")
        self.select_all_checkbox = page.get_by_role("checkbox", name="select all rows")
        self.no_spendings_message = page.get_by_text("There are no spendings")

    @allure.step("Navigate to spending page")
    def navigate_to_spending(self) -> None:
        """Navigate to new spending section"""
        self.page.get_by_role("link", name="New spending").click()
        self._attach_screenshot("Spending page loaded")

    @allure.step("Add spending: {amount} for {category}")
    def add_spending(self, amount: str, category: Optional[str] = None) -> None:
        """Add new spending record"""
        with allure.step("Fill amount field"):
            self.amount_field.fill(amount)
            self._attach_field_value("Amount", amount)

        if category:
            with allure.step("Select category"):
                self.category_field.fill(category)
                self._attach_field_value("Category", category)

        with allure.step("Submit spending"):
            self.add_button.click()
            self._attach_screenshot("After adding spending")

        self.page.wait_for_load_state("networkidle")

    @allure.step("Delete spending: {amount} for {category}")
    def delete_spending(self, category: str, amount: str) -> None:
        """Delete spending by category and amount"""
        formatted_amount = f"{amount} ₽"

        with allure.step(f"Locate spending row: {category} - {formatted_amount}"):
            spending_row = self.page.locator(
                f'tr:has(span:has-text("{category}")):has(span:has-text("{formatted_amount}"))'
            )
            spending_row.locator("input[type='checkbox']").check()
            self._attach_screenshot("Spending row selected")

        with allure.step("Confirm deletion"):
            self.delete_button.click()
            self.delete_button.click()  # Double click for confirmation
            self.delete_spending_popup.wait_for()
            self._attach_screenshot("Deletion confirmed")

    def get_spending_row(self, spending_data: dict) -> Locator:
        formatted_amount = f"{spending_data['amount']} ₽"
        return self.page.locator(
            f'tr:has(span:has-text("{spending_data["category"]}")):has(span:has-text("{formatted_amount}"))'
        )

    def has_any_spendings(self) -> bool:
        return not self.page.get_by_text("There are no spendings").is_visible()

    @allure.step("Delete all spendings")
    def delete_all_spendings(self) -> None:
        """Delete all spending records"""
        with allure.step("Select all spendings"):
            self.select_all_checkbox.check()
            self._attach_screenshot("All spendings selected")

        with allure.step("Confirm mass deletion"):
            self.delete_button.click()
            self.delete_button.click()
            self._attach_screenshot("Mass deletion confirmed")

        self.no_spendings_message.wait_for(state="visible")

    def _attach_screenshot(self, description: str) -> None:
        allure.attach(
            self.page.screenshot(),
            name=description,
            attachment_type=allure.attachment_type.PNG
        )

    def _attach_field_value(self, field_name: str, value: str) -> None:
        allure.attach(
            f"{field_name}: {value}",
            name=field_name,
            attachment_type=allure.attachment_type.TEXT
        )
