"""Debug test to check database connectivity and data persistence."""

from decimal import Decimal

from sqlalchemy import select

from src.models import Account, User


def test_debug_database_access(session, test_user_object, event_loop):
    """Debug test to verify database is working correctly."""

    async def debug_test():
        # First, verify the user is in the database
        stmt = select(User).where(User.id == test_user_object.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        assert user is not None, "User not found in database"
        print(f"User found: {user.username}")

        # Add an account
        account = Account(
            name="Debug Account",
            balance=Decimal("500.00"),
            user_id=test_user_object.id,
        )
        session.add(account)
        await session.commit()
        print(f"Account committed: {account.id}")

        # Query the account back
        stmt = select(Account).where(Account.id == account.id)
        result = await session.execute(stmt)
        found_account = result.scalar_one_or_none()
        assert found_account is not None, "Account not found after commit"
        print(f"Account found: {found_account.name}")

        # Query accounts for the user
        stmt = select(Account).where(Account.user_id == test_user_object.id)
        result = await session.execute(stmt)
        accounts = result.scalars().all()
        print(f"Found {len(accounts)} accounts for user")
        assert len(accounts) == 1, f"Expected 1 account, found {len(accounts)}"

        return True

    result = event_loop.run_until_complete(debug_test())
    assert result is True
