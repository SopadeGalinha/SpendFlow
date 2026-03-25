from datetime import timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.schemas import UserCreate
from src.repositories import UserRepository
from src.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
)
from src.core.config import settings


class AuthService:
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
        return await UserRepository.get_by_email(db, email)

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
        return await UserRepository.get_by_id(db, user_id)

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        if not user_data.password or len(user_data.password) > 70:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password cannot be empty or longer than 70 characters",
            )
        hashed_password = get_password_hash(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            city=user_data.city,
            timezone=user_data.timezone,
            currency=user_data.currency,
            default_weekend_adjustment=user_data.default_weekend_adjustment,
        )
        return await UserRepository.create(db, user)

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, email: str, password: str
    ) -> User | None:
        user = await UserRepository.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_access_token(user_id: UUID) -> str:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(
            subject=str(user_id),
            expires_delta=expires_delta,
        )
