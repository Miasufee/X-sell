from sqlalchemy.ext.asyncio import AsyncSession

from .base import CrudBase
from app.models.merchant import MerchantApplication, MerchantApplicationStatus


class MerchantApplicationCrud(CrudBase[MerchantApplication]):
    def __init__(self):
        super().__init__(MerchantApplication)

    async def applied_to_be_merchant(self, db: AsyncSession, user_id: int):
        pass



# Create instance for easy import
merchant_application_crud = MerchantApplicationCrud()
