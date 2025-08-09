from urllib.parse import parse_qs, urlparse, urljoin

import requests

from requests import Session, Response

from utils.allure_helpers import allure_attach_request


def raise_for_status(function):
    def wrapper(*args, **kwargs):
        response: Response = function(*args, **kwargs)
        check = kwargs.pop('check_status', True)
        if check:
            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                if response.status_code == 400:
                    e.add_note(response.text)
                    raise
        return response
    return wrapper

class BaseSession(Session):
    """Сессия с прокидыванием gateway_url, логированием запроса, ответа."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.gateway_url = kwargs.pop("gateway_url", None)
        self.token = kwargs.get("token", None)
        self.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    @raise_for_status
    @allure_attach_request
    def request(self, method: str, path: str, check_status: bool = True, **kwargs) -> Response:
        return super().request(method, urljoin(str(self.gateway_url), path), **kwargs)


class AuthSession(Session):
    """Сессия с прокидыванием auth_url, логированием запроса, ответа.
    Автосохранение code, также cookies внутри сессии из каждого response, redirect response."""

    def __init__(self, *args, **kwargs):
        """Прокидывание auth_url (url авторизации из Settings), code - код авторизации из redirect_uri."""

        super().__init__()
        self.auth_url = kwargs.pop('auth_url', None)
        self.code = None

    @raise_for_status
    @allure_attach_request
    def request(self, method: str, url: str, **kwargs):
        """Сохранение всех cookies из redirects, code из redirect_uri и использование в дальнейших запросах этой сессии."""

        response = super().request(method, urljoin(str(self.auth_url), url), **kwargs)
        for r in response.history:
            cookies = r.cookies.get_dict()
            self.cookies.update(cookies)

            code = parse_qs(urlparse(r.headers.get('Location')).query).get('code', None)
            if code:
                self.code = code

        return response