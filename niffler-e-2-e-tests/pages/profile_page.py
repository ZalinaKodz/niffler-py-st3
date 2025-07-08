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

    def navigate_to_profile(self):
        self.menu_button.click()
        self.profile_link.click()

    def update_profile_name(self, new_name: str):
        self.name_field.fill(new_name)
        self.save_button.click()

    def add_category(self, category_name: str):
        self.category_field.fill(category_name)
        self.category_field.press("Enter")