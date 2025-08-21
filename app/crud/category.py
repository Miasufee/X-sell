from .base import CrudBase
from ..models.category import Category


class CategoryCrud(CrudBase[Category]):
    def __init__(self):
        super().__init__(Category)


# Create instance
category_crud = CategoryCrud()
