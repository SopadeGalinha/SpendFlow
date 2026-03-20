import asyncio

# from uuid import UUID
from datetime import date
from sqlmodel import select  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore
from src.database import engine
from src.models.user import User, TransactionType, Frequency, WeekendAdjustment
from src.models.finance import Account, RecurringRule


async def seed_data():
    async with AsyncSession(engine) as session:
        # 1. Create User
        user_stmt = select(User).where(User.username == "marla_dev")
        result = await session.execute(user_stmt)
        user = result.scalars().first()

        if not user:
            user = User(
                username="marla_dev",
                email="marla@spendflow.ai",
                hashed_password="fake_hash_123",
                timezone="Europe/Lisbon",
                currency="EUR",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"✅ User created: {user.username}")

        # 2. Create Account
        acc_stmt = select(Account).where(Account.name == "Main Bank")
        result = await session.execute(acc_stmt)
        account = result.scalars().first()

        if not account:
            account = Account(
                name="Main Bank",
                balance=1500.0,
                user_id=user.id,
            )
            session.add(account)
            await session.commit()
            await session.refresh(account)
            print(f"✅ Account created: {account.id}")

        # 3. Create Recurring Rules (Test Scenarios)
        rules = [
            RecurringRule(
                description="Salary (Always Monday if on Weekend)",
                amount=2500.0,
                type=TransactionType.INCOME,
                frequency=Frequency.MONTHLY,
                start_date=date(2026, 3, 1),  # Sunday
                weekend_adjustment=WeekendAdjustment.FOLLOWING,
                account_id=account.id,
            ),
            RecurringRule(
                description="Rent (Always Friday if on Weekend)",
                amount=-800.0,
                type=TransactionType.EXPENSE,
                frequency=Frequency.MONTHLY,
                start_date=date(2026, 3, 28),  # Saturday
                weekend_adjustment=WeekendAdjustment.PRECEDING,
                account_id=account.id,
            ),
            RecurringRule(
                description="Netflix (Keep Original Date Even if on Weekend)",
                amount=-15.0,
                type=TransactionType.EXPENSE,
                frequency=Frequency.MONTHLY,
                start_date=date(2026, 3, 15),  # Sunday
                weekend_adjustment=WeekendAdjustment.KEEP,
                account_id=account.id,
            ),
        ]

        for r in rules:
            # Verify if rule already exists to avoid duplicates
            check = await session.execute(
                select(RecurringRule).where(
                    RecurringRule.description == r.description,
                )
            )
            if not check.scalars().first():
                session.add(r)

        await session.commit()
        print("🚀 Seed ended successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())
