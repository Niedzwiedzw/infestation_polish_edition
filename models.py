from __future__ import annotations
import typing as t
from dataclasses import dataclass
from datetime import datetime, timedelta
from string import whitespace, digits

from visionary import Line, PaddedLine

SicknessValues = (float, float, float, float)


WEIRD_CHARACTERS_MAPPING = {
    '-': '0',
    '–': '0',
    ',': '.',
}

VALID_NUMBER_CHARACTERS = digits + '.'


def normalize_number(number: str) -> str:
    for k, v in WEIRD_CHARACTERS_MAPPING.items():
        number = number.replace(k, v)
    return number


def remove_nonnumber(number: str) -> str:
    n = number
    for ch in number:
        if ch not in VALID_NUMBER_CHARACTERS:
            n.replace(ch, '')

    return n


class SicknessEntry:
    def __init__(self, raw: PaddedLine, start_date: datetime, end_date: datetime, pdf_path: str):
        self._line = raw
        self.words: t.List[str] = list(map(str, raw.line.words))
        self.start_date: datetime = start_date
        self.end_date: datetime = end_date
        self.pdf_path = pdf_path

    @property
    def name(self):
        return ' '.join(self.words[:-4])

    @property
    def _values(self) -> [str, str, str, str]:
        return self.words[-4:]

    @property
    def values(self) -> SicknessValues:
        values = map(normalize_number, self._values)
        values = map(remove_nonnumber, values)
        return tuple(map(float, values))

    @property
    def value_for_time_period(self) -> float:
        return self.values[0]

    @property
    def time_span(self) -> timedelta:
        return self.end_date - self.start_date

    @property
    def days_span(self) -> int:
        return self.time_span.days

    @property
    def value_per_30_days(self):
        return self.value_for_time_period * (30 / self.days_span)

    def __repr__(self):
        return f'<Sickness "{self.name}": {self.value_for_time_period} (pdf: {self.pdf_path})'

    @property
    def json(self) -> t.Dict[str, t.Any]:
        return {
            'name': self.name,
            'per_30_days': self.value_per_30_days,
            'measured': self.end_date.isoformat()
        }
