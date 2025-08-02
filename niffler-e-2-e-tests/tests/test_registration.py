import allure
from playwright.sync_api import expect


@allure.epic("User Authentication")
@allure.feature("Registration")
@allure.story("Successful user registration")
def test_user_registration(registration_page, unregistered_user):
    """
    Test successful user registration flow:
    1. Navigate to registration page
    2. Fill registration form with valid credentials
    3. Submit the form
    4. Verify success message appears
    """
    with allure.step("Navigate to registration page"):
        registration_page.navigate()

    with allure.step("Fill registration form with test data"):
        registration_page.fill_registration_form(
            username=unregistered_user.username,
            password=unregistered_user.password
        )

    with allure.step("Submit registration form"):
        registration_page.submit_form()

    with allure.step("Verify success message appears"):
        expect(registration_page.success_message).to_be_visible(timeout=15000)
        assert registration_page.is_success_message_visible(), \
            "Success registration message is not visible"

    # Attach test data for debugging
    allure.attach(
        str(unregistered_user),
        name="Test User Data",
        attachment_type=allure.attachment_type.JSON
    )