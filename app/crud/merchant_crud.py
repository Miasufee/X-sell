from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select
from typing import Optional, List, Dict, Any, Sequence
from datetime import datetime
from .crud_base import CrudBase
from app.models.merchant import MerchantApplication, MerchantApplicationStatus


class MerchantCrud(CrudBase[MerchantApplication]):
    """Service for handling merchant applications and operations."""

    def __init__(self):
        super().__init__(MerchantApplication)

    async def create_application(
            self,
            db: AsyncSession,
            user_id: int,
            business_name: str,
            business_description: str,
            business_address: str,
            business_phone: str,
            business_email: str,
            tax_id: Optional[str] = None,
            website_url: Optional[str] = None
    ) -> MerchantApplication:
        """Create a new merchant application."""
        application_data = {
            "user_id": user_id,
            "business_name": business_name,
            "business_description": business_description,
            "business_address": business_address,
            "business_phone": business_phone,
            "business_email": business_email,
            "tax_id": tax_id,
            "website_url": website_url,
            "status": MerchantApplicationStatus.PENDING
        }

        return await self.create(db, **application_data)

    async def get_user_application(
            self,
            db: AsyncSession,
            user_id: int
    ) -> Optional[MerchantApplication]:
        """Get merchant application for a specific user."""
        return await self.get(
            db,
            filters={"user_id": user_id}
        )

    async def get_pending_applications(
            self,
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100
    ) -> Sequence[MerchantApplication]:
        """Get all pending merchant applications."""
        return await self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters={"status": MerchantApplicationStatus.PENDING},
            order_by="created_at"
        )

    async def get_applications_by_status(
            self,
            db: AsyncSession,
            status: MerchantApplicationStatus,
            skip: int = 0,
            limit: int = 100
    ) -> Sequence[MerchantApplication]:
        """Get applications by specific status."""
        return await self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters={"status": status},
            order_by="created_at"
        )

    async def approve_application(
            self,
            db: AsyncSession,
            application_id: int,
            admin_user_id: int,
            notes: Optional[str] = None
    ) -> MerchantApplication:
        """Approve a merchant application."""
        application = await self.get(db, obj_id=application_id)
        if not application:
            raise ValueError("Application not found")

        if application.status != MerchantApplicationStatus.PENDING:
            raise ValueError("Application is not in pending status")

        update_data = {
            "status": MerchantApplicationStatus.APPROVED,
            "approved_by": admin_user_id,
            "approved_at": datetime.now(),
            "admin_notes": notes
        }

        return await self.update(db, obj_id=application_id, **update_data)

    async def reject_application(
            self,
            db: AsyncSession,
            application_id: int,
            admin_user_id: int,
            rejection_reason: str,
            notes: Optional[str] = None
    ) -> MerchantApplication:
        """Reject a merchant application."""
        application = await self.get(db, obj_id=application_id)
        if not application:
            raise ValueError("Application not found")

        if application.status != MerchantApplicationStatus.PENDING:
            raise ValueError("Application is not in pending status")

        update_data = {
            "status": MerchantApplicationStatus.REJECTED,
            "approved_by": admin_user_id,
            "rejection_reason": rejection_reason,
            "admin_notes": notes
        }

        return await self.update(db, obj_id=application_id, **update_data)

    async def suspend_application(
            self,
            db: AsyncSession,
            application_id: int,
            admin_user_id: int,
            suspension_reason: str,
            notes: Optional[str] = None
    ) -> MerchantApplication:
        """Suspend an approved merchant application."""
        application = await self.get(db, obj_id=application_id)
        if not application:
            raise ValueError("Application not found")

        if application.status != MerchantApplicationStatus.APPROVED:
            raise ValueError("Only approved applications can be suspended")

        update_data = {
            "status": MerchantApplicationStatus.SUSPENDED,
            "approved_by": admin_user_id,
            "rejection_reason": suspension_reason,
            "admin_notes": notes
        }

        return await self.update(db, obj_id=application_id, **update_data)

    async def reactivate_application(
            self,
            db: AsyncSession,
            application_id: int,
            admin_user_id: int,
            notes: Optional[str] = None
    ) -> MerchantApplication:
        """Reactivate a suspended merchant application."""
        application = await self.get(db, obj_id=application_id)
        if not application:
            raise ValueError("Application not found")

        if application.status != MerchantApplicationStatus.SUSPENDED:
            raise ValueError("Only suspended applications can be reactivated")

        update_data = {
            "status": MerchantApplicationStatus.APPROVED,
            "approved_by": admin_user_id,
            "rejection_reason": None,
            "admin_notes": notes
        }

        return await self.update(db, obj_id=application_id, **update_data)

    async def search_applications(
            self,
            db: AsyncSession,
            search_term: Optional[str] = None,
            status: Optional[MerchantApplicationStatus] = None,
            min_date: Optional[datetime] = None,
            max_date: Optional[datetime] = None,
            skip: int = 0,
            limit: int = 100
    ) -> Sequence[MerchantApplication]:
        """Search merchant applications with various filters."""
        conditions = []

        # Status filter
        if status:
            conditions.append(MerchantApplication.status == status)

        # Date range filter
        if min_date:
            conditions.append(MerchantApplication.created_at >= min_date)
        if max_date:
            conditions.append(MerchantApplication.created_at <= max_date)

        # Search term filter (search in multiple fields)
        if search_term:
            search_condition = or_(
                MerchantApplication.business_name.ilike(f"%{search_term}%"),
                MerchantApplication.business_email.ilike(f"%{search_term}%"),
                MerchantApplication.business_phone.ilike(f"%{search_term}%"),
                MerchantApplication.tax_id.ilike(f"%{search_term}%")
            )
            conditions.append(search_condition)

        where_clause = and_(*conditions) if conditions else None

        return await self.get_multi(
            db,
            skip=skip,
            limit=limit,
            where_clause=where_clause,
            order_by=["-created_at", "business_name"]
        )

    async def get_application_stats(
            self,
            db: AsyncSession
    ) -> Dict[str, int]:
        """Get statistics about merchant applications."""
        stats = {}

        # Count by status
        for status in MerchantApplicationStatus:
            count = await self.count(db, filters={"status": status})
            stats[f"{status.value}_count"] = count

        # Total count
        stats["total_count"] = await self.count(db)

        # Recent applications (last 7 days)
        one_week_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        stats["recent_count"] = await self.count(
            db,
            where_clause=MerchantApplication.created_at >= one_week_ago
        )

        return stats

    async def get_applications_with_users(
            self,
            db: AsyncSession,
            status: Optional[MerchantApplicationStatus] = None,
            skip: int = 0,
            limit: int = 100
    ) -> Sequence[MerchantApplication]:
        """Get applications with user information (using joined load)."""
        from sqlalchemy.orm import joinedload

        stmt = select(self.model).options(
            joinedload(self.model.user),
            joinedload(self.model.approver)
        )

        if status:
            stmt = stmt.where(MerchantApplication.status.is_(status))

        stmt = stmt.order_by(MerchantApplication.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()

    async def bulk_update_status(
            self,
            db: AsyncSession,
            application_ids: List[int],
            new_status: MerchantApplicationStatus,
            admin_user_id: int,
            notes: Optional[str] = None
    ) -> int:
        """Bulk update application status."""
        update_data = {
            "status": new_status,
            "approved_by": admin_user_id,
            "admin_notes": notes
        }

        if new_status == MerchantApplicationStatus.APPROVED:
            update_data["approved_at"] = datetime.now()
            update_data["rejection_reason"] = None
        elif new_status == MerchantApplicationStatus.REJECTED:
            update_data["rejection_reason"] = "Bulk rejection"

        return await self.bulk_update(
            db,
            filters={"id": application_ids},
            update_values=update_data
        )

    async def check_duplicate_applications(
            self,
            db: AsyncSession,
            business_email: str,
            tax_id: Optional[str] = None,
            exclude_application_id: Optional[int] = None
    ) -> bool:
        """Check for duplicate merchant applications."""
        conditions = [
            MerchantApplication.business_email == business_email,
            MerchantApplication.status.in_([
                MerchantApplicationStatus.PENDING,
                MerchantApplicationStatus.APPROVED
            ])
        ]

        if tax_id:
            conditions.append(MerchantApplication.tax_id == tax_id)

        if exclude_application_id:
            conditions.append(MerchantApplication.id != exclude_application_id)

        return await self.exists(
            db,
            where_clause=and_(*conditions)
        )

    async def get_application_timeline(
            self,
            db: AsyncSession,
            application_id: int
    ) -> Dict[str, Any]:
        """Get timeline information for an application."""
        application = await self.get(db, obj_id=application_id)
        if not application:
            raise ValueError("Application not found")

        timeline = {
            "created": application.created_at,
            "status_changes": []
        }

        # Add status change events
        if application.approved_at:
            timeline["status_changes"].append({
                "event": "approved",
                "timestamp": application.approved_at,
                "by_user_id": application.approved_by
            })

        # You could add more timeline events here based on your business logic

        return timeline

    async def export_applications(
            self,
            db: AsyncSession,
            status: Optional[MerchantApplicationStatus] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Export applications data for reporting."""
        conditions = []

        if status:
            conditions.append(MerchantApplication.status == status)
        if start_date:
            conditions.append(MerchantApplication.created_at >= start_date)
        if end_date:
            conditions.append(MerchantApplication.created_at <= end_date)

        where_clause = and_(*conditions) if conditions else None

        applications = await self.get_multi(
            db,
            where_clause=where_clause,
            order_by="created_at",
            limit=10000  # Reasonable limit for exports
        )

        # Convert to export format
        export_data = []
        for app in applications:
            export_data.append({
                "id": app.id,
                "business_name": app.business_name,
                "business_email": app.business_email,
                "business_phone": app.business_phone,
                "status": app.status.value,
                "created_at": app.created_at.isoformat(),
                "approved_at": app.approved_at.isoformat() if app.approved_at else None,
                "user_id": app.user_id,
                "tax_id": app.tax_id,
                "website_url": app.website_url
            })

        return export_data

merchant_crud = MerchantCrud()