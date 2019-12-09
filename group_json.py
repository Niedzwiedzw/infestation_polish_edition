import typing as t
from json import loads, dumps
from itertools import groupby


def _get_response() -> str:
    with open('./response.json') as f:

        return f.read()


def _save_response(data: dict):
    with open('grouped-response.json', 'w') as f:
        f.write(dumps(data))


def by_sickness(values: t.Iterable) -> dict:
    return {k: v for k, v in ((v['name'], v['per_30_days']) for v in values)}


def sicknesses_by_date(entries: t.Iterable[dict]) -> t.Dict[str, t.Any]:
    all_sicknesses = {e['name']: 0 for e in entries}
    return {k: {**all_sicknesses, **by_sickness(v)} for k, v in groupby(entries, key=lambda x: x['measured'])}


def main():
    data = loads(_get_response())
    formatted = sicknesses_by_date(data)
    _save_response(formatted)


if __name__ == '__main__':
    main()
