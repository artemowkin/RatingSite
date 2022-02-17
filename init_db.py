from sqlalchemy import create_engine, MetaData

from ratingsite.settings import config
from users.db import users, users_friends_association, jwt_tokens
from ratings.db import ratings


DSN = "postgresql://{user}:{password}@{host}:{port}/{database}"


def create_tables(engine):
    meta = MetaData()
    meta.create_all(bind=engine, tables=[
        users_friends_association, users, ratings, jwt_tokens
    ])


if __name__ == '__main__':
    db_url = DSN.format(**config['postgres'])
    engine = create_engine(db_url)
    create_tables(engine)
