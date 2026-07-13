"""
Category service for product classification.

Handles creation, retrieval, updates, and deletion of product categories,
ensuring that organizational constraints and name uniqueness rules are respected.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import status
from app.repositories.category_repository import CategoryRepository
from app.db.models.category import Category
from app.schemas.category import CategoryCreateInternal, CategoryUpdate
from app.core.exceptions import AppException
from app.repositories.organization_repository import OrganizationRepository
from app.constants.organization_enum import OrganizationStatus
from app.constants.common_enum import CrudMessages
from app.dependencies.pagination import PaginationParams
from collections.abc import Sequence


from app.core.profiling import log_timing


class CategoryService:
    """
    Service layer driving data validation, business rule execution, and
    transactions for Category entities.
    """

    def __init__(
        self, category_repo: CategoryRepository, org_repo: OrganizationRepository
    ):
        """
        Initialize the CategoryService with required repositories.

        Args:
            category_repo: Repository for category persistence and queries.
            org_repo: Repository for organization validation to maintain data consistency.
        """
        self.category_repo = category_repo
        self.org_repo = org_repo

    @log_timing
    async def create_category(
        self, db: AsyncSession, category_data: CategoryCreateInternal
    ) -> Category:
        """
        Creates a new category after validating organization status and unique constraints.

        Args:
            db (AsyncSession): The active database session context.
            category_data (CategoryCreateInternal): The category payload.

        Returns:
            Category: The newly created category.

        Raises:
            AppException: If the organization doesn't exist, isn't active, or name is duplicate.
        """
        # Validate that the organization exists and is active
        org = await self.org_repo.get_by_id(db, category_data.organization_id)
        if not org:
            raise AppException(
                message=CrudMessages.ORG_NOT_FOUND.format(module="Category"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if org.status != OrganizationStatus.ACTIVE:
            raise AppException(
                message=CrudMessages.ORG_NOT_ACTIVE.format(module="Category"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Check unique constraint: organization_id + name
        existing = await self.category_repo.get_by_name(
            db, category_data.organization_id, category_data.name
        )
        if existing:
            raise AppException(
                message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                    module="Category", field="name", value=category_data.name
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        category_model = Category(**category_data.model_dump())
        try:
            category = await self.category_repo.create(db, category_model)
            await db.flush()
            await db.refresh(category)
            return category
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.ALREADY_EXISTS_FIELD.format(
                    module="Category", field="name", value=category_data.name
                ),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Category", action="creation"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @log_timing
    async def get_category(self, db: AsyncSession, category_id: int) -> Category:
        """
        Retrieves a category by ID, raising an error if not found.

        Args:
            db (AsyncSession): The active database session context.
            category_id (int): The ID of the category.

        Returns:
            Category: The found category.

        Raises:
            AppException: If not found (404).
        """
        category = await self.category_repo.get(db, category_id)
        if not category:
            raise AppException(
                message=CrudMessages.NOT_FOUND.format(module="Category"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return category

    @log_timing
    async def get_all_categories(
        self, db: AsyncSession, params: PaginationParams
    ) -> tuple[Sequence[Category], int]:
        """
        Retrieves all categories.

        Args:
            db (AsyncSession): The active database session context.
            params (PaginationParams): Pagination parameters.

        Returns:
            tuple[Sequence[Category], int]: List of all categories and total count.
        """
        return await self.category_repo.get_all(db, params)

    @log_timing
    async def update_category(
        self, db: AsyncSession, category_id: int, update_data: CategoryUpdate
    ) -> Category:
        """
        Updates an existing category with partial data.

        Args:
            db (AsyncSession): The active database session context.
            category_id (int): The ID of the category to update.
            update_data (CategoryUpdate): The fields to update.

        Returns:
            Category: The updated category instance.

        Raises:
            AppException: If a duplicate category name is provided.
        """
        category = await self.get_category(db, category_id)

        # Extract only fields that were explicitly set in the request
        data_to_update = update_data.model_dump(exclude_unset=True)

        if "name" in data_to_update and data_to_update["name"] != category.name:
            existing = await self.category_repo.get_by_name(
                db, category.organization_id, data_to_update["name"]
            )
            if existing:
                raise AppException(
                    message=CrudMessages.ALREADY_IN_USE.format(
                        module="Category", field="name"
                    ),
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        for key, value in data_to_update.items():
            setattr(category, key, value)

        try:
            category = await self.category_repo.update(db, category)
            await db.flush()
            await db.refresh(category)
            return category
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_CONSTRAINT.format(module="Category"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Category", action="update"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @log_timing
    async def delete_category(self, db: AsyncSession, category_id: int) -> None:
        """
        Deletes a category by ID.

        Args:
            db (AsyncSession): The active database session context.
            category_id (int): The ID of the category to delete.
        """
        category = await self.get_category(db, category_id)
        try:
            await self.category_repo.delete(db, category)
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_RELATIONAL_CONSTRAINT.format(module="Category"),
                status_code=status.HTTP_409_CONFLICT,
            )
        except SQLAlchemyError:
            await db.rollback()
            raise AppException(
                message=CrudMessages.DB_UNEXPECTED.format(
                    module="Category", action="deletion"
                ),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @log_timing
    async def get_by_organization(
        self, db: AsyncSession, organization_id: int, params: PaginationParams
    ) -> tuple[Sequence[Category], int]:
        """
        Retrieves all categories belonging to a specific organization.

        Args:
            db (AsyncSession): The active database session context.
            organization_id (int): The parent organization ID.
            params (PaginationParams): Pagination parameters.

        Returns:
            tuple[Sequence[Category], int]: The categories for the organization and total count.

        Raises:
            AppException: If the organization doesn't exist (404).
        """
        organization = await self.org_repo.get_by_id(
            organization_id=organization_id, db=db
        )

        if not organization:
            raise AppException(
                message=CrudMessages.ORG_NOT_FOUND.format(module="Category"),
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return await self.category_repo.get_by_organization(
            organization_id=organization_id, db=db, params=params
        )
