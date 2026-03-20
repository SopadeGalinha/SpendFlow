import asyncio

# from uuid import UUID
from datetime import date
from sqlmodel import Session, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import engine
from src.models.user import User, TransactionType, Frequency, WeekendAdjustment
from src.models.finance import Account, RecurringRule


async def seed_data():
    # O segredo está em usar AsyncSession(engine)
    async with AsyncSession(engine) as session:
        # 1. Criar Usuário de Teste
        user_stmt = select(User).where(User.username == "marla_dev")
        result = await session.execute(user_stmt)
        user = result.scalars().first()

        if not user:
            user = User(
                username="marla_dev",
                email="marla@spendflow.ai",
                hashed_password="fake_hash_123",
                timezone="Europe/Lisbon",
                currency="EUR"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"✅ Usuário criado: {user.username}")

        # 2. Criar Conta Corrente
        acc_stmt = select(Account).where(Account.name == "Main Bank")
        result = await session.execute(acc_stmt)
        account = result.scalars().first()

        if not account:
            account = Account(name="Main Bank", balance=1500.0, user_id=user.id)
            session.add(account)
            await session.commit()
            await session.refresh(account)
            print(f"✅ Conta criada: {account.id}")

        # 3. Criar Regras Recorrentes (Cenários de Teste)
        rules = [
            RecurringRule(
                description="Salário (Sempre Segunda se cair no FDS)",
                amount=2500.0,
                type=TransactionType.INCOME,
                frequency=Frequency.MONTHLY,
                start_date=date(2026, 3, 1),  # 1 de Março é DOMINGO
                weekend_adjustment=WeekendAdjustment.FOLLOWING,
                account_id=account.id,
            ),
            RecurringRule(
                description="Aluguel (Sempre Sexta se cair no FDS)",
                amount=-800.0,
                type=TransactionType.EXPENSE,
                frequency=Frequency.MONTHLY,
                start_date=date(2026, 3, 28),  # 28 de Março é SÁBADO
                weekend_adjustment=WeekendAdjustment.PRECEDING,
                account_id=account.id,
            ),
            RecurringRule(
                description="Netflix (Mantém no FDS)",
                amount=-15.0,
                type=TransactionType.EXPENSE,
                frequency=Frequency.MONTHLY,
                start_date=date(2026, 3, 15),  # 15 de Março é DOMINGO
                weekend_adjustment=WeekendAdjustment.KEEP,
                account_id=account.id,
            ),
        ]

        for r in rules:
            # Verifica se a regra já existe pela descrição para não duplicar
            check = await session.execute(
                select(RecurringRule).where(
                    RecurringRule.description == r.description,
                )
            )
            if not check.scalars().first():
                session.add(r)

        await session.commit()
        print("🚀 Seed finalizado com sucesso!")


if __name__ == "__main__":
    asyncio.run(seed_data())
