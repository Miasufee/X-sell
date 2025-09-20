
from .crud_base import CrudBase
from ..models.delivery import Delivery, DeliveryStatus


class DeliveryCrud(CrudBase[Delivery]):
    def __init__(self):
        super().__init__(Delivery)


# Create instance
delivery_crud = DeliveryCrud()
