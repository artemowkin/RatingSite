from typing import Union

from sqlalchemy import and_

from .db import ratings


class GetUserRatingService:

    def __init__(self, conn, current_user_id: Union[str, int]) -> None:
        self._conn = conn
        self._current_user_id = current_user_id

    async def get_user_rating(self, another_user_id: Union[str, int]) -> dict:
        """Get rating for user"""
        query = ratings.select().where(and_(
            ratings.c.creator_id == self._current_user_id,
            ratings.c.receiver_id == another_user_id
        ))
        cursor = await self._conn.execute(query)
        rating = await cursor.fetchone()
        if not rating: return {}
        return {
            'rating_value': rating.rating_value, 'improve': rating.improve
        }
