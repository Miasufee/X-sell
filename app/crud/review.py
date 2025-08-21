from .base import CrudBase
from ..models.review import Review, Favorite


class ReviewCrud(CrudBase[Review]):
    def __init__(self):
        super().__init__(Review)



class FavoriteCrud(CrudBase[Favorite]):
    def __init__(self):
        super().__init__(Favorite)



# Create instances
review_crud = ReviewCrud()
favorite_crud = FavoriteCrud()
