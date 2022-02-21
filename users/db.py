from sqlalchemy import (
    MetaData, Table, Column, ForeignKey, Integer, String, Boolean,
    UniqueConstraint
)
from sqlalchemy_utils import EmailType


meta = MetaData()

users_friends_association = Table(
    'users_friends_association', meta,

    Column('first_id', ForeignKey('users.id', ondelete='CASCADE')),
    Column('second_id', ForeignKey('users.id', ondelete='CASCADE')),
    UniqueConstraint('first_id', 'second_id'),
)

users = Table(
    'users', meta,

    Column('id', Integer, primary_key=True),
    Column('nickname', String(100), unique=True, nullable=False),
    Column('first_name', String(100), nullable=False),
    Column('last_name', String(100), nullable=False),
    Column('email', EmailType, unique=True, nullable=False),
    Column('password', String(100), nullable=False),
    Column('is_superuser', Boolean, nullable=False, default=False),
    Column('disabled', Boolean, nullable=False, default=False),
)
