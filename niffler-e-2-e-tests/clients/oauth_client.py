
import pkce
from urllib.parse import urljoin

from conftest import Settings
from models.oauth import OAuthRequest
from utils.sessions import AuthSession


class OauthClient:
    def __init__(self, settings: Settings) -> None:
        """Генерация code_verifier, code_challenge."""

        self.session = AuthSession(auth_url=settings.AUTH_URL)
        self.redirect_uri = urljoin(str(settings.FRONTEND_URL), '/authorized')
        self.domain_url = settings.AUTH_URL
        self.token = None

        # Самостоятельная генерация кодов. Замена на целевую схему с использованием библиотеки
        # self.code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
        # self.code_verifier = re.sub('[^a-zA-Z0-9]+', '', self.code_verifier)
        #
        # self.code_challenge = hashlib.sha256(self.code_verifier.encode('utf-8')).digest()
        # self.code_challenge = base64.urlsafe_b64encode(self.code_challenge).decode('utf-8')
        # self.code_challenge = self.code_challenge.replace('=', '')
        self.code_verifier, self.code_challenge = pkce.generate_pkce_pair()

    def access_token(self, username: str, password: str) -> str:
        """Получение token oauth для авторизации пользователя с username, password.
        1. Получение jsessionid и xsrf-token в cookies сессии.
        2. Получение code из redirect_uri по xsrf-token'у.
        3. Получение access_token.
        """

        self.session.get(
            url='/oauth2/authorize',
            params=OAuthRequest(
                redirect_uri=self.redirect_uri,
                code_challenge=self.code_challenge
            ).model_dump(),
            allow_redirects=True
        )

        self.session.post(
            url='/login',
            data={
                'username': username,
                'password': password,
                '_csrf': self.session.cookies.get('XSRF-TOKEN'),
            },
            allow_redirects=True
        )

        token_response = self.session.post(
            url='/oauth2/token',
            data={
                'code': self.session.code,
                'redirect_uri': self.redirect_uri,
                'code_verifier': self.code_verifier,
                'grant_type': 'authorization_code',
                'client_id': 'client'
            }
        )

        self.token = token_response.json().get('access_token', None)
        return self.token

    def register(self, username, password):
        self.session.get(
            url=f"{self.domain_url}/register",
            params={
                "redirect_uri": "http://auth.niffler.dc:9000/register",
            },
            allow_redirects=True
        )

        result = self.session.post(
            url=f"{self.domain_url}/register",
            data={
                "username": username,
                "password": password,
                "passwordSubmit": password,
                "_csrf": self.session.cookies.get("XSRF-TOKEN")
            },
            allow_redirects=True
        )
        return result