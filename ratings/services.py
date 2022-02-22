from typing import Union, Optional

from sqlalchemy import and_

from .db import ratings
from .serializers import RatingSerializer


class GetUserRatingService:

    def __init__(self, conn, current_user_id: Union[str, int, None]) -> None:
        self._conn = conn
        self._current_user_id = current_user_id

    async def _get_rating(self, another_user_id: int):
        """Get rating from DB"""
        query = ratings.select().where(and_(
            ratings.c.creator_id == self._current_user_id,
            ratings.c.receiver_id == another_user_id
        ))
        cursor = await self._conn.execute(query)
        rating = await cursor.fetchone()
        return rating

    async def get_user_rating(self,
            another_user_id: int) -> Optional[dict]:
        """Get rating for user"""
        if not self._current_user_id: return None
        rating = await self._get_rating(another_user_id)
        if not rating: return None
        return RatingSerializer.parse_obj(dict(rating)).dict()
