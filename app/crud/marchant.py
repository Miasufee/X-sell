from sqlalchemy.ext.asyncio import AsyncSession

from .base import CrudBase
from app.models.merchant import MerchantApplication, MerchantApplicationStatus


class MerchantApplicationCrud(CrudBase[MerchantApplication]):
    def __init__(self):
        super().__init__(MerchantApplication)


merchant_application_crud = MerchantApplicationCrud()
