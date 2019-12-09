from __future__ import annotations
import typing as t
import os
import csv
import argparse
from itertools import chain
import warnings
warnings.filterwarnings("ignore")
from pprint import pprint

import tabula

from helpers import stripped
from models import Sickness, ParsingException
from downloader import all_pdfs

NORMALIZED_LINE_LENGTH = 3
OUTPUT_DIRECTORY = 'result/'
DEFAULT_OUTPUT = 'csv'
WEIRD_HYPHEN = '–'
NULL_VALUES = [
    WEIRD_HYPHEN,
    '.'
]

parser = argparse.ArgumentParser(
    description=(
        'Infestation™ PL-edition™.\n'
        'CLI utility to provide computer-friendly format for SANEPID™ data.'
    )
)

parser.add_argument(
    '--source',
    type=str,
    required=False,
    help='HTTP link or local path to a file converted. By default all files are downloaded.'
)

parser.add_argument('--format', type=str, default=DEFAULT_OUTPUT, help=f'output format, defaults to {DEFAULT_OUTPUT}')

parser.add_argument(
    '--out',
    type=str,
    required=False,
    help='name of output file, defaults to source name with .csv extension'
)

args = parser.parse_args()


def starts_with_index(word: str) -> bool:
    return word.split()[0].isdigit()


def get_valid_lines(lines: t.List[t.List[str]]) -> t.Generator[t.List[str], None, None]:
    def _valid_lines():
        for line in lines:
            if starts_with_index(line[0]):
                if line[0].strip()[0].isdigit():
                    fullname, *rest = line
                    for i, element in enumerate(rest):
                        if element[0].isalpha():
                            fullname += ' ' + element
                        else:
                            newline = [fullname, *rest[i:]]
                            yield newline
                            break
                else:
                    yield line

    for line in _valid_lines():
        if len(line) == 2:
            name, values = line
            fixed_values = reformat_weird_spacing(values).split()
            vals_1, vals_2 = fixed_values[:2], fixed_values[2:]
            yield [name, ' '.join(vals_1), ' '.join(vals_1)]

        if not len(line) == NORMALIZED_LINE_LENGTH:
            raise ParsingException(f'{line} has ircorrect length (expected {NORMALIZED_LINE_LENGTH}')
        yield line


def reformat_weird_spacing(values: str) -> str:
    parsed = ''
    values = values.split()
    for i, element in enumerate(values):
        parsed += element
        nextval = values[i + 1] if values[i + 1:] else None
        if nextval:
            if len(nextval) == 3 or ('.' in nextval and len(nextval) == 6):
                pass
            else:
                parsed += ' '

    return parsed


def fix_werid_spacing(values: str) -> t.Tuple[str, str]:
    parsed = reformat_weird_spacing(values)

    if len(parsed.split()) != 2:
        return parsed[:-6], parsed[-6:]

    return tuple(parsed.split())


def parse_values(values: t.List[str]) -> t.List[float]:
    parsed = values[:]
    for null_value in NULL_VALUES:
        parsed: t.List[str] = [piece.replace(null_value, '0.0') for piece in parsed]
    parsed = [piece.replace(',', '.') for piece in parsed]
    parsed = [fix_werid_spacing(piece) if len(piece.split()) != 2 else piece.split() for piece in parsed]
    parsed: t.List[float] = [float(value) for piece in parsed for value in piece]

    return parsed


def parse_line(line: t.List[str]) -> t.Tuple[int, str, t.Tuple[float]]:
    tablename, values = line[0], line[1:]
    values = tuple(parse_values(values))
    index, fieldname = tablename.split(maxsplit=1)
    return index, fieldname, values


def skip(iterable: t.Iterator, times: int) -> t.Iterator:
    for _ in range(times):
        next(iterable)

    return iterable


def load_sicknesses(filename: str) -> t.Generator[Sickness, None, None]:
    tmpfile = filename.rsplit('/')[-1] + '.tmp'
    tabula.convert_into(filename, tmpfile, output_format=format_, pages='all', silent=True)

    with open(tmpfile) as file:
        lines = stripped(csv.reader(file, delimiter=','))
    os.remove(tmpfile)

    this_year, last_year = lines[0]
    valid_lines = get_valid_lines(lines[3:])

    for line in valid_lines:
        index, name, values = parse_line(line)
        main_name = name if name[0].isupper() else None
        subcategory = name if not main_name else 'razem'
        args = int(index), main_name, subcategory, values, this_year, last_year

        yield Sickness(*args)


def write_to_csv(filename: str, sicknesses: t.Generator[Sickness, None, None]):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        first = next(sicknesses)
        writer.writerow(
            ['id', 'Sickness', 'Subcategory', first.this_year, first.this_year, first.last_year, first.last_year]
        )
        for sickness in chain([first], sicknesses):
            writer.writerow(
                [
                    sickness.index,
                    sickness.name,
                    sickness.subcategory,
                    *sickness.values
                ]
            )


def main():
    current_files = os.listdir(OUTPUT_DIRECTORY)

    for date, link in all_pdfs():
        filename = f'{date}.csv'
        print(f'{date}... ', end='')
        if filename not in current_files:
            write_to_csv(f'{OUTPUT_DIRECTORY}{filename}', load_sicknesses(link))
            print('DONE')
        else:
            print('ALREADY EXISTS')


if __name__ == '__main__':
    format_ = args.format
    sources = [args.source] if args.source else ['test_data/INF_18_10B.pdf']
    outs = [args.out] if args.out else [o[:-3] + format_ for o in sources]

    main()
