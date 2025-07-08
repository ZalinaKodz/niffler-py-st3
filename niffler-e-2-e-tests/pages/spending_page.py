from playwright.sync_api import Page

class SpendingPage:
    def __init__(self, page: Page):
        self.page = page
        self.amount_field = page.get_by_role("spinbutton", name="Amount")
        self.category_field = page.get_by_role("textbox", name="Add new category")
        self.add_button = page.get_by_role("button", name="Add")
        self.success_message = page.get_by_text("New spending is successfully")
        self.error_message = page.get_by_text("Please choose category")

        # Локаторы для удаления трат
        self.delete_button = page.get_by_role("button", name="Delete")
        self.delete_confirm_button = page.get_by_role("button", name="Delete", exact=True)
        self.delete_success_message = page.get_by_text("Spendings successfully deleted")
        self.spending_rows = page.locator(".spending-row")

    def navigate_to_spending(self):
        self.page.get_by_role("link", name="New spending").click()

    def add_spending(self, amount: str, category: str = None):
        self.amount_field.fill(amount)
        if category:
            self.category_field.fill(category)
        self.add_button.click()
        self.page.wait_for_load_state("networkidle")