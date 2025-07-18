from playwright.sync_api import Page, Locator


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

        # Локаторы для удаления трат
        self.delete_spending_button = page.locator("#delete")
        self.delete_spending_dialog = page.get_by_role("dialog")
        self.delete_spending_dialog_button = self.delete_spending_dialog.get_by_role("button", name="Delete")
        self.delete_spending_popup = page.get_by_text(f"Spendings succesfully deleted")
        self.delete_button = page.get_by_role("button", name="Delete")
        self.cancel_button = self.page.get_by_role("button", name="Cancel")
        self.select_all_checkbox = page.get_by_role("checkbox", name="select all rows")
        self.no_spendings_message = page.get_by_text("There are no spendings")


    def navigate_to_spending(self):
        self.page.get_by_role("link", name="New spending").click()

    def add_spending(self, amount: str, category: str = None):
        self.amount_field.fill(amount)
        if category:
            self.category_field.fill(category)
        self.add_button.click()
        self.page.wait_for_load_state("networkidle")

    def delete_spending(self, category: str, amount: str):
        """Удаляет трату по категории и сумме"""
        # Форматируем сумму для поиска (добавляем ₽)
        formatted_amount = f"{amount} ₽"

        # Находим строку с тратой
        spending_row = self.page.locator(
            f'tr:has(span:has-text("{category}")):has(span:has-text("{formatted_amount}"))'
        )

        # Выбираем и удаляем
        spending_row.locator("input[type='checkbox']").check()
        self.delete_button.click()
        self.delete_button.click()
        # Ждем подтверждения удаления
        self.delete_spending_popup.wait_for()

    def get_spending_row(self, spending_data: dict) -> Locator:
        formatted_amount = f"{spending_data['amount']} ₽"
        return self.page.locator(
            f'tr:has(span:has-text("{spending_data["category"]}")):has(span:has-text("{formatted_amount}"))'
        )

    def has_any_spendings(self) -> bool:
        return not self.page.get_by_text("There are no spendings").is_visible()

    def delete_all_spendings(self):
        self.page.get_by_role("checkbox", name="select all rows").check()
        self.delete_button.click()
        self.delete_button.click()