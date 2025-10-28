from typing import Optional, List

from sqlalchemy import create_engine, Engine, event
from sqlmodel import Session, select
from models.user import UserName, User
from utils.allure_helpers import attach_sql


class UsersDb:
    engine: Engine

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        event.listen(self.engine, "before_cursor_execute", attach_sql)

    def get_user(self, username: str) -> Optional[User]:
        """Возвращает пользователя или None если не найден"""
        with Session(self.engine) as session:
            statement = select(User).where(User.username == username)
            result = session.exec(statement).first()
            return result

    def get_all_users(self) -> List[User]:
        """Возвращает всех пользователей"""
        with Session(self.engine) as session:
            statement = select(User)
            result = session.exec(statement).all()
            return result

    def user_exists(self, username: str) -> bool:
        """Проверяет существует ли пользователь"""
        return self.get_user(username) is not None