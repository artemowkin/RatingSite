from typing import Optional
import re

import jwt
from passlib.hash import pbkdf2_sha256

from ratingsite.settings import config
from .db import users


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

    async def registrate_user(self, conn, auth_data: dict) -> dict:
        """
        Registrate user: create the user entry in DB and the JWT token,
        return the created jwt token, error data
        """
        errors = self._validate_reg_data(auth_data)
        if errors: return errors
        del auth_data['password2']
        password = pbkdf2_sha256.hash(auth_data.pop('password1'))
        query = users.insert().values(password=password, **auth_data)
        cursor = await conn.execute(query)
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
        jwt_user = dict(
            zip(('email', 'nickname'), (user.email, user.nickname))
        )
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
