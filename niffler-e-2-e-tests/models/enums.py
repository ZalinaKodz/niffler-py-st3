from enum import Enum


class Currency(str, Enum):
    RUB = "RUB"
    EUR = "EUR"
    USD = "USD"
    KZT = "KZT"

    @classmethod
    def all_values(cls):
        return [cls.RUB, cls.EUR, cls.USD, cls.KZT]


class FriendshipStatus(str, Enum):
    INVITE_SENT = "INVITE_SENT"
    INVITE_RECEIVED = "INVITE_RECEIVED"
    FRIEND = "FRIEND"
    VOID = "VOID"


class Direction(str, Enum):
    ASC = "ASC"
    DESC = "DESC"