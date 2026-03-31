import logging
from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from src.models import User
from src.repositories import UserRepository
from src.schemas import UserCreate, UserPreferencesResponse, UserPreferencesUpdate

logger = logging.getLogger(__name__)


class AuthService:
    @staticmethod
    def normalize_identifier(value: str) -> str:
        return value.strip().lower()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
        return await UserRepository.get_by_email(
            db,
            AuthService.normalize_identifier(email),
        )

    @staticmethod
    async def get_user_by_username(
        db: AsyncSession, username: str
    ) -> User | None:
        return await UserRepository.get_by_username(
            db,
            AuthService.normalize_identifier(username),
        )

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
        return await UserRepository.get_by_id(db, user_id)

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        passwd = user_data.password
        if not passwd or len(passwd) > 72:
            logger.warning(
                "User registration failed: invalid password",
                extra={"email": user_data.email},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be between 8 and 72 characters",
            )
        hashed_password = get_password_hash(passwd)
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            city=user_data.city,
            timezone=user_data.timezone,
            currency=user_data.currency,
            default_weekend_adjustment=user_data.default_weekend_adjustment,
        )
        try:
            created_user = await UserRepository.create(db, user)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists.",
            )
        await db.refresh(created_user)
        logger.info(
            "User registered successfully",
            extra={
                "user_id": str(created_user.id),
                "email": created_user.email,
            },
        )
        return created_user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, email: str, password: str
    ) -> User | None:
        normalized_email = AuthService.normalize_identifier(email)
        user = await UserRepository.get_by_email(db, normalized_email)
        if not user:
            logger.warning(
                "Login failed: user not found",
                extra={"email": normalized_email},
            )
            return None
        if not verify_password(password, user.hashed_password):
            logger.warning(
                "Login failed: incorrect password",
                extra={"email": normalized_email},
            )
            return None
        logger.info(
            "User authenticated successfully",
            extra={"user_id": str(user.id), "email": normalized_email},
        )
        return user

    @staticmethod
    def create_access_token(user_id: UUID) -> str:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(
            subject=str(user_id),
            expires_delta=expires_delta,
        )

    @staticmethod
    def get_user_preferences(user: User) -> UserPreferencesResponse:
        raw_preferences = (
            user.ui_preferences
            if isinstance(user.ui_preferences, dict)
            else {}
        )

        try:
            return UserPreferencesResponse.model_validate(raw_preferences)
        except Exception:
            # If persisted preferences become invalid for any reason,
            # fall back to safe defaults instead of blocking the user.
            return UserPreferencesResponse()

    @staticmethod
    async def update_user_preferences(
        db: AsyncSession,
        user: User,
        preferences_update: UserPreferencesUpdate,
    ) -> UserPreferencesResponse:
        preferences = AuthService.get_user_preferences(user)

        dashboard_update = preferences_update.dashboard
        if dashboard_update is not None:
            if dashboard_update.order is not None:
                preferences.dashboard.order = dashboard_update.order
            if dashboard_update.hidden is not None:
                preferences.dashboard.hidden = dashboard_update.hidden

        budget_update = preferences_update.budget
        if budget_update is not None and budget_update.view_mode is not None:
            preferences.budget.view_mode = budget_update.view_mode

        user.ui_preferences = preferences.model_dump(mode="json")
        await UserRepository.save(db, user)
        await db.commit()
        await db.refresh(user)

        return preferences
