import allure
from playwright.sync_api import Page


@allure.epic("Finance Application")
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

    @allure.step("Navigate to profile page")
    def navigate_to_profile(self) -> None:
        """Navigate to profile section through menu"""
        with allure.step("Open menu"):
            self.menu_button.click()
            self._attach_screenshot("Menu opened")

        with allure.step("Select profile link"):
            self.profile_link.click()
            self._attach_screenshot("Profile page loaded")

    @allure.step("Update profile name to '{new_name}'")
    def update_profile_name(self, new_name: str) -> None:
        """Update user profile name"""
        with allure.step("Fill name field"):
            self.name_field.fill(new_name)
            self._attach_field_value("New name", new_name)

        with allure.step("Save changes"):
            self.save_button.click()
            self._attach_screenshot("After saving profile")

        self._wait_for_success_message()

    @allure.step("Edit category from '{old_name}' to '{new_name}'")
    def edit_category(self, old_name: str, new_name: str) -> None:
        """Edit existing category name"""
        with allure.step(f"Find and edit category '{old_name}'"):
            category_item = self.page.locator(f'div:has-text("{old_name}")')
            edit_button = category_item.locator('button:has-text("edit")')
            edit_button.click()
            self._attach_screenshot("Edit button clicked")

        with allure.step("Update category name"):
            edit_field = self.page.get_by_role("textbox", name="Edit category")
            edit_field.fill(new_name)
            edit_field.press("Enter")
            self._attach_field_value("New category name", new_name)

        self._wait_for_category_update()

    def _wait_for_success_message(self) -> None:
        self.success_message.wait_for(state="visible")
        self._attach_screenshot("Success message visible")

    def _wait_for_category_update(self) -> None:
        self.page.wait_for_load_state("networkidle")
        self.success_message_for_category.wait_for(state="visible")
        self._attach_screenshot("Category updated")

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
