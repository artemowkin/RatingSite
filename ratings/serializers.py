from pydantic import BaseModel


class RatingSerializer(BaseModel):
    """PyDantic model for rating serializing"""

    rating_value: int
    improve: str
