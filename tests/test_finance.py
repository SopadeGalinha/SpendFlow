from src.models import Account
from decimal import Decimal, ROUND_HALF_UP


def test_account_soft_delete_flow(client, session, test_user):
    account = Account(
        name="Business Savings",
        balance=Decimal("5000.50").quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        ),
        user_id=test_user.id,
    )
    session.add(account)
    session.commit()
    session.refresh(account)

    assert account.deleted_at is None

    response = client.delete(f"/api/v1/finance/accounts/{account.id}")
    assert response.status_code == 200

    session.refresh(account)
    assert account.deleted_at is not None

    list_response = client.get(
        f"/api/v1/finance/accounts?user_id={test_user.id}",
    )
    data = list_response.json()

    assert len(data) == 0
