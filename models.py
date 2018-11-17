from __future__ import annotations
import typing as t

from dataclasses import dataclass


class ParsingException(Exception):
    pass


@dataclass
class Sickness:
    index: int
    name: t.Union[str, None]
    subcategory: str
    values: t.Tuple[float]
    this_year: str
    last_year: str
