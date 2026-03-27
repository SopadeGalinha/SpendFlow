"""Debug test matching test_list_accounts structure."""

from decimal import Decimal

from fastapi import status

from src.models import Account


def test_debug_create_and_list(
    client, test_user, test_user_object, session, event_loop
):
    """Debug test that mirrors test_list_accounts structure."""

    # Create accounts using setup like test_list_accounts does
    async def setup():
        account1 = Account(
            name="Account 1",
            balance=Decimal("100.00"),
            user_id=test_user_object.id,
        )
        account2 = Account(
            name="Account 2",
            balance=Decimal("200.00"),
            user_id=test_user_object.id,
        )
        session.add(account1)
        session.add(account2)
        await session.commit()
        print("Committed 2 accounts")

    event_loop.run_until_complete(setup())

    # Now try to list them
    response = client.get(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {test_user}"},
    )

    print(f"Response status: {response.status_code}")
    data = response.json()
    print(f"Response data: {data}")
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 2, f"Expected 2 accounts, got {len(data)}"
