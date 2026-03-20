from datetime import date, timedelta
from typing import List
from dateutil.rrule import (  # type: ignore
    rrule,
    DAILY,
    WEEKLY,
    MONTHLY,
    YEARLY,
)
from src.models.user import Frequency, WeekendAdjustment
from src.models.finance import RecurringRule

# Mapeamento de Frequência para constantes do dateutil
FREQ_MAP = {
    Frequency.DAILY: DAILY,
    Frequency.WEEKLY: WEEKLY,
    Frequency.MONTHLY: MONTHLY,
    Frequency.YEARLY: YEARLY,
}


class CalendarService:
    @staticmethod
    def adjust_date(target_date: date, adjustment: WeekendAdjustment) -> date:
        """
        Aplica a regra de ajuste de fim de semana.
        weekday(): 0=Seg, 1=Ter, ..., 5=Sáb, 6=Dom
        """
        weekday = target_date.weekday()

        # Se for dia de semana ou a regra for MANTER, não faz nada
        if weekday < 5 or adjustment == WeekendAdjustment.KEEP:
            return target_date

        if adjustment == WeekendAdjustment.FOLLOWING:
            # Sábado (5) -> +2 dias (Segunda)
            # Domingo (6) -> +1 dia (Segunda)
            days_to_add = 7 - weekday
            return target_date + timedelta(days=days_to_add)

        if adjustment == WeekendAdjustment.PRECEDING:
            # Sábado (5) -> -1 dia (Sexta)
            # Domingo (6) -> -2 dias (Sexta)
            days_to_subtract = weekday - 4
            return target_date - timedelta(days=days_to_subtract)

        return target_date

    @classmethod
    def get_projection(
        cls, rules: List[RecurringRule], start_period: date, end_period: date
    ) -> List[dict]:
        """
        Gera a lista de transações projetadas para um período específico.
        """
        projections = []

        for rule in rules:
            # Gera as datas baseadas na frequência da regra
            # rrule cuida de meses com 28, 30 ou 31 dias automaticamente
            occurrences = rrule(
                FREQ_MAP[rule.frequency],
                dtstart=rule.start_date,
                until=rule.end_date or end_period,
            )

            for occ in occurrences:
                occ_date = occ.date()

                if start_period <= occ_date <= end_period:
                    adjusted_date = cls.adjust_date(
                        occ_date, rule.weekend_adjustment)

                    projections.append(
                        {
                            "id": f"virtual_{rule.id}_{adjusted_date.isoformat()}",
                            "description": rule.description,
                            "amount": rule.amount,
                            "type": rule.type,
                            "original_date": occ_date,
                            "date": adjusted_date,
                            "is_virtual": True,
                            "rule_id": rule.id,
                        }
                    )

        # Ordena por data para o frontend não se perder
        return sorted(projections, key=lambda x: x["date"])
