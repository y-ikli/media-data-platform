"""Dates et fenêtres de dates manipulées par l'ingestion."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, timedelta


def parse_date(value: str) -> date:
    """Convertit une date ``AAAA-MM-JJ`` ; lève ``ValueError`` si le format est invalide."""
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"date invalide (AAAA-MM-JJ attendu) : {value!r}") from exc


@dataclass(frozen=True, slots=True)
class DateWindow:
    """Période de dates, bornes incluses."""

    start: date
    end: date

    def __post_init__(self) -> None:
        """Refuse une fenêtre dont le début est après la fin."""
        if self.end < self.start:
            raise ValueError(f"fenêtre inversée : {self.start} > {self.end}")

    def __contains__(self, day: object) -> bool:
        """Indique si ``day`` est une date comprise dans la fenêtre."""
        return isinstance(day, date) and self.start <= day <= self.end

    def __str__(self) -> str:
        """Affiche la fenêtre sous la forme ``début..fin``."""
        return f"{self.start}..{self.end}"

    @property
    def days_count(self) -> int:
        """Nombre de jours de la fenêtre, bornes comprises."""
        return (self.end - self.start).days + 1

    def days(self) -> Iterator[date]:
        """Parcourt les jours de la fenêtre, dans l'ordre."""
        for offset in range(self.days_count):
            yield self.start + timedelta(days=offset)

    def split(self, max_days: int) -> list[DateWindow]:
        """Découpe la fenêtre en fenêtres contiguës d'au plus ``max_days`` jours."""
        if max_days < 1:
            raise ValueError("max_days doit être ≥ 1")
        windows: list[DateWindow] = []
        cursor = self.start
        while cursor <= self.end:
            last = min(cursor + timedelta(days=max_days - 1), self.end)
            windows.append(DateWindow(cursor, last))
            cursor = last + timedelta(days=1)
        return windows

    @classmethod
    def last_days(cls, count: int, today: date) -> DateWindow:
        """Les ``count`` derniers jours complets : de J-``count`` à hier inclus."""
        if count < 1:
            raise ValueError("count doit être ≥ 1")
        yesterday = today - timedelta(days=1)
        return cls(yesterday - timedelta(days=count - 1), yesterday)
