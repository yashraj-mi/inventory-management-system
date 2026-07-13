"""
Customer service module managing client relationships.

Handles business logic and data persistence for customers. Enforces validation
rules such as organization association, and uniqueness of email and phone fields.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import status
from collections.abc import Sequence

from app.core.exceptions import AppException
from app.constants.common_enum import CrudMessages
from app.constants.organization_enum import OrganizationStatus
from app.repositories.customer_repository import CustomerRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.customer import CustomerCreateInternal, CustomerUpdate
from app.db.models.customer import Customer
from app.dependencies.pagination import PaginationParams
from app.core.profiling import log_timing


class CustomerService:
    """
    Service layer driving data validation and business rules for Customers.
    """

    def __init__(
        self, repo: CustomerRepository, org_repo: OrganizationRepository
    ) -> None:
        """
        Initialize the CustomerService with data repositories.

        Args:
            repo: Repository for customer data operations.
            org_repo: Repository to validate parent organization states.
        """
        self.repo = repo
        self.org_repo = org_repo

    @log_timing
    async def create(
        self, db: AsyncSession, payload: CustomerCreateInternal
    ) -> Customer:
        """
        Create a new customer linked to a specific organization.

        Verifies the organization is active and ensures the customer's
        email and phone are unique within the organization.

        Args:
            db: The active database session context.
            payload: The internal payload containing validated customer details.

        Returns:
            The created Customer entity.

        Raises:
            AppException: For inactive organizations, duplicate fields (409), or DB errors.
        """
        # Validate Organization
        org = await self.org_repo.get_by_id(db, payload.organization_id)
        if not org:
            raise AppException(
                message=CrudMessages.ORG_NOT_FOUND.format(module="Customer"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if org.status != OrganizationStatus.ACTIVE:
            raise AppException(
                message=CrudMessages.ORG_NOT_ACTIVE.format(module="Customer"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Validate Uniqueness for email and phone within the organization
        if payload.email and await self.repo.get_by_email(
            db, payload.organization_id, payload.email
        ):
            raise AppException(
                message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                    module="Customer", field="email", value=payload.email
                ),
                status_code=status.HTTP_409_CONFLICT,
            )
        if payload.phone and await self.repo.get_by_phone(
            db, payload.organization_id, payload.phone
        ):
            raise AppException(
                message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                    module="Customer", field="phone", value=payload.phone
                ),
                status_code=status.HTTP_409_CONFLICT,
            )

        customer = Customer(
            organization_id=payload.organization_id,
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            address=payload.address,
        )

        try:
            await self.repo.create(db, customer)
            await db.flush()
            await db.refresh(customer)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_CONSTRAINT.format(module="Customer"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Customer", action="creation"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return customer

    @log_timing
    async def get_all_by_org(
        self, db: AsyncSession, org_id: int, params: PaginationParams
    ) -> tuple[Sequence[Customer], int]:
        """
        Retrieve all customers belonging to a specific organization.

        Args:
            db: The active database session context.
            org_id: The ID of the organization.
            params: Parameters for paginating the result set.

        Returns:
            A tuple of customer sequences and the total count.
        """
        org = await self.org_repo.get_by_id(db, org_id)
        if not org:
            raise AppException(
                message=CrudMessages.ORG_NOT_FOUND.format(module="Customer"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return await self.repo.get_all(db, org_id, params)

    @log_timing
    async def get(self, db: AsyncSession, customer_id: int, org_id: int) -> Customer:
        """
        Retrieve a specific customer, ensuring organizational ownership.

        Args:
            db: The active database session context.
            customer_id: The ID of the customer to fetch.
            org_id: The organization ID requesting access.

        Returns:
            The matching Customer entity.

        Raises:
            AppException: If the customer does not exist or doesn't belong to the organization.
        """
        customer = await self.repo.get_by_id(db, customer_id)
        if not customer or customer.organization_id != org_id:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Customer"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return customer

    @log_timing
    async def update(
        self, db: AsyncSession, customer_id: int, payload: CustomerUpdate, org_id: int
    ) -> Customer:
        """
        Update an existing customer's contact details.

        Checks organizational ownership before updating and verifies uniqueness
        if the email or phone number is changed.

        Args:
            db: The active database session context.
            customer_id: The ID of the customer to update.
            payload: Partial customer data for update.
            org_id: The organization ID of the actor.

        Returns:
            The updated Customer entity.

        Raises:
            AppException: On duplicate email/phone or database errors.
        """
        customer = await self.get(db, customer_id, org_id)

        update_data = payload.model_dump(exclude_unset=True)

        # Validate Uniqueness if email or phone are updated
        if "email" in update_data and update_data["email"] != customer.email:
            if update_data["email"] and await self.repo.get_by_email(
                db, org_id, update_data["email"]
            ):
                raise AppException(
                    message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                        module="Customer", field="email", value=update_data["email"]
                    ),
                    status_code=status.HTTP_409_CONFLICT,
                )
        if "phone" in update_data and update_data["phone"] != customer.phone:
            if update_data["phone"] and await self.repo.get_by_phone(
                db, org_id, update_data["phone"]
            ):
                raise AppException(
                    message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                        module="Customer", field="phone", value=update_data["phone"]
                    ),
                    status_code=status.HTTP_409_CONFLICT,
                )

        for field, value in update_data.items():
            setattr(customer, field, value)

        try:
            await db.flush()
            await db.refresh(customer)
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_CONSTRAINT.format(module="Customer"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Customer", action="update"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return customer

    @log_timing
    async def delete(self, db: AsyncSession, customer_id: int, org_id: int) -> None:
        """
        Delete a customer entity from the database.

        Verifies ownership through the get method prior to deletion.
        A relational constraint failure typically implies linked sales orders.

        Args:
            db: The active database session context.
            customer_id: The ID of the customer to delete.
            org_id: The requesting organization ID.

        Raises:
            AppException: If related records prevent deletion (409) or on unknown DB errors.
        """
        customer = await self.get(db, customer_id, org_id)
        try:
            await self.repo.delete(db, customer)
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_RELATIONAL_CONSTRAINT.format(module="Customer"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Customer", action="deletion"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
