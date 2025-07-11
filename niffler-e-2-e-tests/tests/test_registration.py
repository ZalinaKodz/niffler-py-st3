from playwright.sync_api import expect


def test_user_registration(registration_page, unregistered_user):
    """
    Тест успешной регистрации пользователя
    1. Переход на страницу регистрации
    2. Заполнение формы регистрации
    3. Отправка формы
    4. Проверка сообщения об успешной регистрации
    """
    # Заполняем форму регистрации
    registration_page.fill_registration_form(
        username=unregistered_user.username,
        password=unregistered_user.password
    )

    # Отправляем форму
    registration_page.submit_form()

    # Проверяем успешную регистрацию
    expect(registration_page.success_message).to_be_visible(timeout=15000)
    assert registration_page.is_success_message_visible(), \
        "Сообщение об успешной регистрации не отображается"