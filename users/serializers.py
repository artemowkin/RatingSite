import re

from pydantic import BaseModel, validator


class RegistrationData(BaseModel):
    """PyDantic model for registration data"""

    nickname: str
    email: str
    password1: str
    password2: str
    first_name: str
    last_name: str

    @validator('email')
    def email_matching(cls, value: str) -> str:
        """Validate is email matching the regexp"""
        regex = r"^[^@]+@[^@]+\.[^@]+$"
        if not re.match(regex, value):
            raise ValueError('Incorrect email')

        return value

    @validator('nickname')
    def is_nickname_slug(cls, value: str) -> str:
        """Validate does nickname contain only slug chars"""
        regex = r"^[-\w\d]+$"
        if not re.match(regex, value):
            raise ValueError(
                'Nickname can only contain letters, numbers and -, _'
            )

        return value

    @validator('password1')
    def validate_password(cls, value: str) -> str:
        """
        Validate password: >= 1 number, >= 1 uppercase, >= 1 lowercase,
        >= 1 special symbol, 6 <= length <= 20
        """
        regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
        if not re.match(regex, value):
            raise ValueError(
                'Password should have at least: one number, one uppercase '
                'and one lowercase character, one special symbol; and '
                'should be between 6 to 20 characters long'
            )

        return value

    @validator('password2')
    def validate_passwords_are_equal(cls, value: str, values: dict,
            **kwargs) -> str:
        """Validate are password1 and password2 equal"""
        if 'password1' in values and value != values['password1']:
            raise ValueError('passwords do not match')

        return value


class LoginData(BaseModel):
    """PyDantic model for login data"""

    email: str
    password: str


class UserSerializer(BaseModel):
    """PyDantic model for user in output json"""

    id: int
    nickname: str
    first_name: str
    last_name: str
    is_superuser: bool
