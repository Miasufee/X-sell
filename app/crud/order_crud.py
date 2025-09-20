from .crud_base import CrudBase
from ..models.order import Order, OrderItem, OrderStatus


class OrderCrud(CrudBase[Order]):
    def __init__(self):
        super().__init__(Order)



class OrderItemCrud(CrudBase[OrderItem]):
    def __init__(self):
        super().__init__(OrderItem)


# Create instances
order_crud = OrderCrud()
order_item_crud = OrderItemCrud()
