from dataclasses import dataclass, field
from typing import List, Optional

from models.enums import Direction, Currency, FriendshipStatus


@dataclass
class Sort:
    property: str
    direction: Direction

@dataclass
class PageInfo:
    page: int
    size: int
    sort: List[Sort] = field(default_factory=list)

@dataclass
class SoapUser:
    id: str
    username: str
    currency: Currency
    firstname: Optional[str] = None
    surname: Optional[str] = None
    fullname: Optional[str] = None
    photo: Optional[str] = None
    photoSmall: Optional[str] = None
    friendshipStatus: Optional[FriendshipStatus] = None

@dataclass
class CurrentUserRequest:
    username: str

@dataclass
class UpdateUserRequest:
    user: SoapUser

@dataclass
class AllUsersRequest:
    username: str
    searchQuery: Optional[str] = None

@dataclass
class AllUsersPageRequest:
    username: str
    pageInfo: PageInfo
    searchQuery: Optional[str] = None

@dataclass
class FriendsRequest:
    username: str
    searchQuery: Optional[str] = None

@dataclass
class FriendsPageRequest:
    username: str
    pageInfo: PageInfo
    searchQuery: Optional[str] = None

@dataclass
class RemoveFriendRequest:
    username: str
    friendToBeRemoved: str

@dataclass
class SendInvitationRequest:
    username: str
    friendToBeRequested: str

@dataclass
class AcceptInvitationRequest:
    username: str
    friendToBeAdded: str

@dataclass
class DeclineInvitationRequest:
    username: str
    invitationToBeDeclined: str

@dataclass
class UserResponse:
    user: SoapUser

@dataclass
class UsersResponse:
    users: List[SoapUser] = field(default_factory=list)
    size: Optional[int] = None
    number: Optional[int] = None
    totalElements: Optional[int] = None
    totalPages: Optional[int] = None