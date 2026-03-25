from datetime import date, timedelta
from typing import List

from dateutil.rrule import (  # type: ignore
    DAILY,
    MONTHLY,
    WEEKLY,
    YEARLY,
    rrule,
)

from src.models import Frequency, RecurringRule, WeekendAdjustment
from src.schemas.finance import ProjectionResponse

FREQ_MAP = {
    Frequency.DAILY: DAILY,
    Frequency.WEEKLY: WEEKLY,
    Frequency.MONTHLY: MONTHLY,
    Frequency.YEARLY: YEARLY,
}


class CalendarService:
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
        cls, rules: List[RecurringRule], start_period: date, end_period: date
    ) -> List[ProjectionResponse]:
        """
        Generates a list of projected transactions for a specific period.
        """
        projections = []

        for rule in rules:
            occurrences = rrule(
                FREQ_MAP[rule.frequency],
                dtstart=rule.start_date,
                until=rule.end_date or end_period,
            )

            for occ in occurrences:
                occ_date = occ.date()

                if start_period <= occ_date <= end_period:
                    adjusted_date = cls.adjust_date(
                        occ_date, rule.weekend_adjustment
                    )

                    projections.append(
                        ProjectionResponse(
                            id=(
                                f"virtual_{rule.id}_"
                                f"{adjusted_date.isoformat()}"
                            ),
                            description=rule.description,
                            amount=rule.amount,
                            type=rule.type,
                            original_date=occ_date,
                            date=adjusted_date,
                            is_virtual=True,
                            rule_id=rule.id,
                        )
                    )

        # Sort by date for frontend display
        return sorted(projections, key=lambda x: x.date)
