from datetime import date, timedelta
from decimal import Decimal
from typing import List

from dateutil.rrule import (  # type: ignore
    DAILY,
    MONTHLY,
    WEEKLY,
    YEARLY,
    rrule,
)

from src.models import (
    Frequency,
    RecurringRule,
    TransactionType,
    WeekendAdjustment,
)
from src.schemas.finance import ProjectionResponse

FREQ_MAP = {
    Frequency.DAILY: DAILY,
    Frequency.WEEKLY: WEEKLY,
    Frequency.MONTHLY: MONTHLY,
    Frequency.YEARLY: YEARLY,
}


class CalendarService:
    @staticmethod
    def normalize_amount(amount: Decimal) -> Decimal:
        return abs(amount)

    @classmethod
    def signed_amount(
        cls,
        amount: Decimal,
        transaction_type: TransactionType,
    ) -> Decimal:
        normalized_amount = cls.normalize_amount(amount)
        if transaction_type == TransactionType.INCOME:
            return normalized_amount
        return -normalized_amount

    @staticmethod
    def adjust_date(target_date: date, adjustment: WeekendAdjustment) -> date:
        """Adjusts the date according to the weekend adjustment rule.
        weekday(): 0=Monday, ..., 5=Saturday, 6=Sunday
        """
        weekday = target_date.weekday()

        if weekday < 5 or adjustment == WeekendAdjustment.KEEP:
            return target_date

        if adjustment == WeekendAdjustment.FOLLOWING:
            days_to_add = 7 - weekday
            return target_date + timedelta(days=days_to_add)

        if adjustment == WeekendAdjustment.PRECEDING:
            days_to_subtract = weekday - 4
            return target_date - timedelta(days=days_to_subtract)

        return target_date

    @classmethod
    def get_projection(
        cls,
        rules: List[RecurringRule],
        start_period: date,
        end_period: date,
        current_balance: Decimal | None = None,
    ) -> List[ProjectionResponse]:
        """
        Generates a list of projected transactions for a specific period.
        """
        projection_entries = []

        for rule in rules:
            interval = max(getattr(rule, "interval", 1) or 1, 1)
            occurrences = rrule(
                FREQ_MAP[rule.frequency],
                interval=interval,
                dtstart=rule.start_date,
                until=rule.end_date or end_period,
            )

            for occ in occurrences:
                occ_date = occ.date()

                if start_period <= occ_date <= end_period:
                    adjusted_date = cls.adjust_date(
                        occ_date, rule.weekend_adjustment
                    )

                    normalized_amount = cls.normalize_amount(rule.amount)
                    projection_entries.append(
                        {
                            "id": (
                                f"virtual_{rule.id}_"
                                f"{adjusted_date.isoformat()}"
                            ),
                            "description": rule.description,
                            "amount": normalized_amount,
                            "type": rule.type,
                            "original_date": occ_date,
                            "date": adjusted_date,
                            "is_virtual": True,
                            "rule_id": rule.id,
                            "balance_delta": cls.signed_amount(
                                normalized_amount,
                                rule.type,
                            ),
                        }
                    )

        projection_entries.sort(
            key=lambda entry: (
                entry["date"],
                entry["original_date"],
                entry["description"],
                str(entry["rule_id"]),
            )
        )

        running_balance = current_balance
        projections = []
        for entry in projection_entries:
            projected_balance = None
            if running_balance is not None:
                running_balance += entry["balance_delta"]
                projected_balance = running_balance

            projections.append(
                ProjectionResponse(
                    **entry,
                    projected_balance=projected_balance,
                )
            )

        return projections
