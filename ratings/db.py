from sqlalchemy import (
    MetaData, Table, Column, ForeignKey, Integer, String, CheckConstraint
)


meta = MetaData()

ratings = Table(
    'ratings', meta,

    Column('id', Integer, primary_key=True),
    Column('creator_id', ForeignKey('users.id', ondelete='CASCADE')),
    Column('receiver_id', ForeignKey('users.id', ondelete='CASCADE')),
    Column('rating_value', Integer),
    Column('improve', String(100)),

    CheckConstraint('rating_value >= -1000 AND rating_value <= 1000'),
)
