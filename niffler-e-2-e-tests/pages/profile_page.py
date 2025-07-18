from playwright.sync_api import Page

class ProfilePage:
    def __init__(self, page: Page):
        self.page = page
        self.menu_button = page.get_by_role("button", name="Menu")
        self.profile_link = page.get_by_role("link", name="Profile")
        self.name_field = page.get_by_role("textbox", name="Name", exact=True)
        self.save_button = page.get_by_role("button", name="Save changes")
        self.success_message = page.get_by_text("Profile successfully updated")
        self.category_field = page.get_by_role("textbox", name="Add new category")
        self.category_added_message = page.get_by_text("You've added new category")
        self.success_message_for_category = page.get_by_text("Category name is changed")

    def navigate_to_profile(self):
        self.menu_button.click()
        self.profile_link.click()

    def update_profile_name(self, new_name: str):
        self.name_field.fill(new_name)
        self.save_button.click()

    def edit_category(self, old_name: str, new_name: str):
        """
        Редактирует существующую категорию
        """
        # Находим кнопку редактирования для конкретной категории
        category_item = self.page.locator(f'div:has-text("{old_name}")')
        edit_button = category_item.locator('button:has-text("edit")')
        edit_button.click()

        # Заполняем новое имя категории
        edit_field = self.page.get_by_role("textbox", name="Edit category")
        edit_field.fill(new_name)
        edit_field.press("Enter")

        # Ждем обновления
        self.page.wait_for_load_state("networkidle")