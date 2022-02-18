from typing import Optional, Union
import re

import jwt
from passlib.hash import pbkdf2_sha256
from aiohttp.web import Request

from ratingsite.settings import config
from .db import users, users_friends_association


class BaseAuthService:
    """
    Base service for authentication services with generic
    validation methods
    """

    required_fields = tuple()

    def _validate_email(self, data: dict) -> dict:
        """Validate is email correct"""
        regex = r"[^@]+@[^@]+\.[^@]+"
        if 'email' in data and not re.match(regex, data['email']):
            return {'email': 'incorrect email'}

        return {}

    def _validate_data_fields(self, data: dict) -> dict:
        """Validate fields in data"""
        errors = {}
        err_msg = '{field} is required'
        for field in self.required_fields:
            if not field in data:
                errors[field] = err_msg.format(field=field)

        return errors


class RegistrationService(BaseAuthService):
    """Service with registration logic"""

    required_fields = ('password1', 'password2', 'email', 'nickname')

    def _validate_passwords_equal(self, data: dict) -> dict:
        """Validate are passwords equal"""
        if ('password1' in data and 'password2' in data and
                data['password1'] != data['password2']):
            return {'password2': 'passwords are not equal'}

        return {}

    def _validate_reg_data(self, data: dict) -> dict:
        """Validate is registration data valid"""
        validation_errors = {}
        validation_errors.update(self._validate_data_fields(data))
        validation_errors.update(self._validate_data_fields(data))
        validation_errors.update(self._validate_passwords_equal(data))
        validation_errors.update(self._validate_email(data))
        return validation_errors

    async def _create_db_user(self, conn, auth_data: dict) -> int:
        """Create a new entry in DB and return new user id"""
        del auth_data['password2']
        password = pbkdf2_sha256.hash(auth_data.pop('password1'))
        query = users.insert().values(password=password, **auth_data)
        cursor = await conn.execute(query)
        created_user_id = await cursor.fetchone()[0]
        return created_user_id

    async def registrate_user(self, conn, auth_data: dict) -> dict:
        """
        Registrate user: create the user entry in DB and the JWT token,
        return the created jwt token, error data
        """
        errors = self._validate_reg_data(auth_data)
        if errors: return errors
        created_user_id = await self._create_db_user(conn, auth_data)
        auth_data.update({'id': created_user_id})
        jwt_token = jwt.encode(auth_data, config['jwt_secret'])
        return {'jwt_token': jwt_token}


class LoginService(BaseAuthService):
    """Service with log in logic"""

    required_fields = ('email', 'password')

    def _validate_login_data(self, data: dict) -> dict:
        """Validate fields in login data"""
        validation_errors = {}
        validation_errors.update(self._validate_data_fields(data))
        validation_errors.update(self._validate_email(data))
        return validation_errors

    async def _get_user(self, conn, email: str):
        """Get user by email"""
        query = users.select().where(users.c.email == email)
        cursor = await conn.execute(query)
        user = await cursor.fetchone()
        return user

    def _create_jwt_token(self, user) -> str:
        """Create a new JWT token for user"""
        jwt_user = {
            'id': user.id, 'email': user.email, 'nickname': user.nickname
        }
        jwt_token = jwt.encode(jwt_user, config['jwt_secret'])
        return jwt_token

    async def login_user(self, conn, auth_data: dict) -> dict:
        """
        Get user from db by `auth_data` and create a new JWT token
        for it
        """
        errors = self._validate_login_data(auth_data)
        if errors: return errors
        user = await self._get_user(conn, auth_data['email'])
        if not user: return {'error': "User with this email doesn't exist"}
        jwt_token = self._create_jwt_token(user)
        return {'jwt_token': jwt_token}


def users_to_json(users_list: list) -> list[dict]:
    """Format users entries from DB to list of dicts"""
    json_users = [dict(user) for user in users_list]
    for user in json_users:
        del user['password']
        del user['disabled']

    return json_users


async def get_all_users(conn, current_user=None) -> dict:
    """Get all users from DB exclude current user (if not empty)"""
    query = users.select().where(users.c.disabled == False)
    if current_user:
        query = query.where(users.c.email != current_user['email'])

    cursor = await conn.execute(query)
    all_users = await cursor.fetchall()
    return users_to_json(all_users)


async def add_user_friend(conn, request: Request) -> None:
    """Add the user to friends list of current user"""
    json_request = await request.json()
    friend_id = json_request.get('id')
    if not friend_id or request.user['id'] == friend_id: return
    query = users_friends_association.insert({
        'first_id': request.user['id'], 'second_id': friend_id
    })
    await conn.execute(query)


class GetUserFriendsService:

    def _get_user_friends_query(self, user_id: Union[str, int]):
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

    def _format_friends_to_json(self, friends: list) -> list[dict]:
        """Format friends list from DB to JSON"""
        construct_lambda = lambda user: {
            'id': user.id, 'email': user.email, 'nickname': user.nickname
        }
        return list(map(construct_lambda, friends))

    async def get_friends(self, conn, user_id: Union[str, int]) -> list[dict]:
        """Get user friends"""
        query = self._get_user_friends_query(user_id)
        cursor = await conn.execute(query)
        user_friends = await cursor.fetchall()
        json_user_friends = self._format_friends_to_json(user_friends)
        return json_user_friends
