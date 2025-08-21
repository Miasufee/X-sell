from .base import CrudBase
from ..models.cart import Cart, CartItem


class CartCrud(CrudBase[Cart]):
    def __init__(self):
        super().__init__(Cart)




class CartItemCrud(CrudBase[CartItem]):
    def __init__(self):
        super().__init__(CartItem)



# Create instances
cart_crud = CartCrud()
cart_item_crud = CartItemCrud()
