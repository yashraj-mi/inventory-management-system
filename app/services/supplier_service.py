"""
Supplier service managing vendor information.

Coordinates supplier creation, updates, and deletion while enforcing organizational
scoping and unique constraints on contact details.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import status

from app.core.exceptions import AppException
from app.constants.common_enum import CrudMessages
from app.constants.organization_enum import OrganizationStatus
from app.repositories.supplier_repository import SupplierRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.supplier import SupplierCreateInternal, SupplierUpdate
from app.db.models.supplier import Supplier
from app.dependencies.pagination import PaginationParams
from collections.abc import Sequence

from app.core.profiling import log_timing


class SupplierService:
    """
    Service layer driving data validation and business rules for Suppliers.
    """

    def __init__(
        self, supplier_repo: SupplierRepository, org_repo: OrganizationRepository
    ) -> None:
        """
        Initialize the SupplierService with requisite repositories.

        Args:
            supplier_repo: Data access layer for supplier entities.
            org_repo: Data access layer for organization validation.
        """
        self.supplier_repo = supplier_repo
        self.org_repo = org_repo

    @log_timing
    async def create(
        self, db: AsyncSession, payload: SupplierCreateInternal
    ) -> Supplier:
        """
        Create a new supplier associated with a specific organization.

        Validates the parent organization and enforces uniqueness on the
        supplier's email and phone number.

        Args:
            db: Active DB session context.
            payload: Validated schema containing supplier details.

        Returns:
            The created Supplier entity.

        Raises:
            AppException: If unique constraints fail (409) or org is invalid (404/400).
        """
        # Validate Organization
        org = await self.org_repo.get_by_id(db, payload.organization_id)
        if not org:
            raise AppException(
                message=CrudMessages.ORG_NOT_FOUND.format(module="Supplier"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if org.status != OrganizationStatus.ACTIVE:
            raise AppException(
                message=CrudMessages.ORG_NOT_ACTIVE.format(module="Supplier"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Validate Uniqueness
        if await self.supplier_repo.get_by_email(
            db, payload.organization_id, payload.email
        ):
            raise AppException(
                message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                    module="Supplier", field="email", value=payload.email
                ),
                status_code=status.HTTP_409_CONFLICT,
            )
        if await self.supplier_repo.get_by_phone(
            db, payload.organization_id, payload.phone
        ):
            raise AppException(
                message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                    module="Supplier", field="phone", value=payload.phone
                ),
                status_code=status.HTTP_409_CONFLICT,
            )

        supplier = Supplier(
            organization_id=payload.organization_id,
            name=payload.name,
            contact_person=payload.contact_person,
            email=payload.email,
            phone=payload.phone,
        )

        try:
            await self.supplier_repo.create(db, supplier)
            await db.flush()
            await db.refresh(supplier)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_CONSTRAINT.format(module="Supplier"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Supplier", action="creation"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return supplier

    @log_timing
    async def get_all_by_org(
        self, db: AsyncSession, org_id: int, params: PaginationParams
    ) -> tuple[Sequence[Supplier], int]:
        """
        Retrieve all suppliers for a specific organization.

        Args:
            db: Active DB session context.
            org_id: Parent organization ID.
            params: Pagination parameters.

        Returns:
            Tuple containing supplier sequence and total count.
        """
        org = await self.org_repo.get_by_id(db, org_id)
        if not org:
            raise AppException(
                message=CrudMessages.ORG_NOT_FOUND.format(module="Suppliers"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return await self.supplier_repo.get_all(db, org_id, params)

    @log_timing
    async def get(self, db: AsyncSession, supplier_id: int) -> Supplier:
        """
        Retrieve a supplier entity by its ID.

        Args:
            db: Active DB session context.
            supplier_id: ID of the supplier to fetch.

        Returns:
            The Supplier entity.

        Raises:
            AppException: If the supplier does not exist (404).
        """
        supplier = await self.supplier_repo.get_by_id(db, supplier_id)
        if not supplier:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Supplier"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return supplier

    @log_timing
    async def update(
        self, db: AsyncSession, supplier_id: int, payload: SupplierUpdate
    ) -> Supplier:
        """
        Update an existing supplier's details.

        Ensures that modified contact details do not conflict with existing suppliers.

        Args:
            db: Active DB session context.
            supplier_id: ID of the supplier to update.
            payload: Partial data payload for the update.

        Returns:
            The updated Supplier entity.
        """
        supplier = await self.get(db, supplier_id)

        update_data = payload.model_dump(exclude_unset=True)

        # If email or phone is updated, check for conflicts
        if "email" in update_data and update_data["email"] != supplier.email:
            if await self.supplier_repo.get_by_email(
                db, supplier.organization_id, update_data["email"]
            ):
                raise AppException(
                    message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                        module="Supplier", field="email", value=update_data["email"]
                    ),
                    status_code=status.HTTP_409_CONFLICT,
                )
        if "phone" in update_data and update_data["phone"] != supplier.phone:
            if await self.supplier_repo.get_by_phone(
                db, supplier.organization_id, update_data["phone"]
            ):
                raise AppException(
                    message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                        module="Supplier", field="phone", value=update_data["phone"]
                    ),
                    status_code=status.HTTP_409_CONFLICT,
                )

        for field, value in update_data.items():
            setattr(supplier, field, value)

        try:
            await db.flush()
            await db.refresh(supplier)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_CONSTRAINT.format(module="Supplier"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Supplier", action="update"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return supplier

    @log_timing
    async def delete(self, db: AsyncSession, supplier_id: int) -> None:
        """
        Delete a supplier entity from the system.

        Will fail if the supplier is mapped to existing products or purchase orders.

        Args:
            db: Active DB session context.
            supplier_id: ID of the supplier to delete.

        Raises:
            AppException: On relational constraint failures (409) or unknown DB errors.
        """
        supplier = await self.get(db, supplier_id)
        try:
            await self.supplier_repo.delete(db, supplier)
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_RELATIONAL_CONSTRAINT.format(module="Supplier"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Supplier", action="deletion"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
