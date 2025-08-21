
from .base import CrudBase
from app.models.shop import Shop


class ShopCrud(CrudBase[Shop]):
    def __init__(self):
        super().__init__(Shop)




# Create instance for easy import
shop_crud = ShopCrud()
