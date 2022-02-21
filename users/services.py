from typing import Optional, Union
import re

import jwt
from passlib.hash import pbkdf2_sha256
from aiohttp.web import Request
from sqlalchemy import and_

from ratingsite.settings import config
from ratings.services import GetUserRatingService
from .db import users, users_friends_association
from .serializers import RegistrationData, LoginData, UserSerializer


async def get_user_by_nickname(conn, nickname: str):
    """Get user from DB using nickname"""
    query = users.select().where(users.c.nickname == nickname)
    cursor = await conn.execute(query)
    user = await cursor.fetchone()
    if not user: raise IndexError
    return user


async def get_all_users(conn, current_user=None) -> dict:
    """Get all users from DB exclude current user (if not empty)"""
    query = users.select().where(users.c.disabled == False)
    if current_user:
        query = query.where(users.c.email != current_user['email'])

    cursor = await conn.execute(query)
    all_users = await cursor.fetchall()
    json_users = [
        UserSerializer.parse_obj(dict(user)).dict() for user in all_users
    ]
    return json_users


async def add_user_friend(conn, request: Request) -> None:
    """Add the user to friends list of current user"""
    json_request = await request.json()
    friend_id = json_request.get('id')
    if not friend_id or request.user['id'] == friend_id: return
    query = users_friends_association.insert({
        'first_id': request.user['id'], 'second_id': friend_id
    })
    await conn.execute(query)


async def get_user_info(conn, user_nickname: str) -> dict:
    """Get information (id, nickname, is_superuser, friends) about user"""
    user = await get_user_by_nickname(conn, user_nickname)
    json_user = UserSerializer.parse_obj(dict(user)).dict()
    get_friends_service = GetUserFriendsService(conn)
    user_friends = await get_friends_service.get_friends_by_id(user.id)
    json_user['friends'] = user_friends
    return json_user


class RegistrationService:
    """Service with registration logic"""

    def __init__(self, conn):
        self._conn = conn

    def _get_query_data(self, auth_data: RegistrationData) -> dict:
        """
        Get data for query with password field with hashed password
        instead of password1 and password2 fields
        """
        password = pbkdf2_sha256.hash(auth_data.password1)
        query_data = auth_data.dict(exclude={'password1', 'password2'})
        query_data['password'] = password
        return query_data

    async def _create_db_user(self, auth_data: RegistrationData) -> int:
        """Create a new entry in DB and return new user id"""
        auth_data_dict = self._get_query_data(auth_data)
        query = users.insert().values(**auth_data_dict)
        cursor = await self._conn.execute(query)
        created_user_id = await cursor.fetchone()
        return created_user_id[0]

    async def _get_jwt_token(self, auth_data: RegistrationData,
            user_id: int) -> str:
        """Generate jwt token for user"""
        jwt_payload = auth_data.dict(include={'nickname', 'email'})
        jwt_payload.update({'id': created_user_id})
        jwt_token = jwt.encode(jwt_payload, config['jwt_secret'])
        return jwt_token

    async def registrate_user(self, auth_data: RegistrationData) -> dict:
        """
        Registrate user: create the user entry in DB and the JWT token,
        return the created jwt token, error data
        """
        created_user_id = await self._create_db_user(auth_data)
        jwt_token = self._get_jwt_token(auth_data, created_user_id)
        return {'jwt_token': jwt_token}


class LoginService:
    """Service with log in logic"""

    def __init__(self, conn):
        self._conn = conn

    async def _get_user(self, email: str):
        """Get user by email"""
        query = users.select().where(
            and_(users.c.email == email, users.c.disabled == False)
        )
        cursor = await self._conn.execute(query)
        user = await cursor.fetchone()
        return user

    def _create_jwt_token(self, user) -> str:
        """Create a new JWT token for user"""
        jwt_payload = {
            'id': user.id, 'email': user.email, 'nickname': user.nickname
        }
        jwt_token = jwt.encode(jwt_payload, config['jwt_secret'])
        return jwt_token

    async def login_user(self, auth_data: LoginData) -> dict:
        """
        Get user from db by `auth_data` and create a new JWT token
        for it
        """
        user = await self._get_user(auth_data.email)
        if not user: return {
            'error': "User with these credentials doesn't exist"
        }
        jwt_token = self._create_jwt_token(user)
        return {'jwt_token': jwt_token}


class GetUserFriendsService:

    def __init__(self, conn):
        self._conn = conn

    def _get_user_friends_query(self, user_id: int):
        """Construct get user friends query"""
        return users.select().join(
            users_friends_association,
            users_friends_association.c.second_id == users.c.id
        ).where(
            users_friends_association.c.first_id == user_id
        ).intersect(users.select().join(
            users_friends_association,
            users_friends_association.c.first_id == users.c.id
        ).where(
            users_friends_association.c.second_id == user_id
        ))

    async def get_friends_by_id(self, user_id: int) -> list[dict]:
        """Get user friends using user id"""
        query = self._get_user_friends_query(user_id)
        cursor = await self._conn.execute(query)
        user_friends = await cursor.fetchall()
        json_friends = [
            UserSerializer.parse_obj(dict(user)).dict() for user in user_friends
        ]
        return json_friends

    async def get_friends_by_nick(self, user_nickname: str) -> list[dict]:
        """Get user friends using user nickname"""
        user = await get_user_by_nickname(self._conn, user_nickname)
        friends = await self.get_friends_by_id(user.id)
        return friends


class GetAnotherUserInfoService:

    def __init__(self, conn, current_user_id: Union[str, int, None]) -> None:
        self._conn = conn
        self._current_user_id = current_user_id

    async def get_info(self, another_user_nickname: str) -> dict:
        """Get full info (including friends and rating) about another user"""
        user_info = await get_user_info(self._conn, another_user_nickname)
        rating_service = GetUserRatingService(
            self._conn, self._current_user_id
        )
        user_rating = await rating_service.get_user_rating(user_info['id'])
        user_info['rating'] = user_rating
        return user_info
