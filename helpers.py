import typing as t


def stripped(rows: t.Iterable[t.Iterable[str]]) -> t.List[t.List[str]]:
    return [[col for col in row if col.strip()] for row in rows]
