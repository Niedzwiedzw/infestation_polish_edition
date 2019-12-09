from os.path import basename
import typing as t
from dataclasses import dataclass
from os import listdir
from itertools import chain
import statistics
from json import dumps

from models import SicknessEntry
from visionary import DocumentFile, Page, parse_date, Line, Word, PaddedLine

WEIRD_HYPHENS = ['–']
IGNORE_CHARACTERS = [',', ' ']

PDF_DIR = './downloads'


@dataclass(frozen=True, eq=True)
class ReportPage:
    raw: Page

    @staticmethod
    def _is_stat_line(line: Line) -> bool:
        return len(line.words) > 5 \
            and all((ReportPage._is_data_entry(word) for word in line.words[-4:])) \
            and not ReportPage._is_data_entry(line.words[-5])

    @staticmethod
    def _is_data_entry(word: Word) -> bool:
        word = str(word).strip()
        for ch in IGNORE_CHARACTERS:
            word = word.replace(ch, '')

        for ch in WEIRD_HYPHENS:
            word = word.replace(ch, '-')

        return word.isnumeric() or word == '-'

    @property
    def lines(self) -> t.Generator[Line, None, None]:
        yield from filter(ReportPage._is_stat_line, self.raw.lines)

    @property
    def padded_lines(self) -> t.Generator[PaddedLine, None, None]:
        char_width = self._char_width()
        return (PaddedLine(line, char_width) for line in self.lines)

    def _char_width(self) -> float:
        lines = list(self.lines)
        try:
            longest: Line = list(sorted(lines, key=lambda l: l.width))[-1]
        except IndexError:
            return 0.
        words = chain(*(line.words for line in lines))
        symbols = chain(*(word.symbols for word in words))
        char_width = statistics.median((symbol.width for symbol in symbols))
        return char_width / len(longest._text)


@dataclass(frozen=True, eq=True)
class ReportFile:
    pdf_path: str

    @property
    def _document(self) -> DocumentFile:
        return DocumentFile(self._json_path)

    @property
    def _pages(self) -> t.List[Page]:
        return self._document.pages

    @property
    def pages(self) -> t.List[ReportPage]:
        return list(map(ReportPage, self._pages))

    @property
    def pdf_name(self) -> str:
        return basename(self.pdf_path)

    @property
    def _base_name(self) -> str:
        return self.pdf_name.rsplit('.', 1)[0]

    @property
    def _dates_raw(self):
        return self._base_name.split('-')

    @property
    def _date_raw_start(self):
        return self._dates_raw[0]

    @property
    def _date_raw_end(self):
        return self._dates_raw[1]

    @property
    def start_date(self):
        return parse_date(self._date_raw_start)

    @property
    def end_date(self):
        return parse_date(self._date_raw_end)

    @property
    def _json_path(self) -> str:
        return f'./result/{self._base_name}.json'

    def __repr__(self):
        return f'<ReportFile: {self.pdf_path} ({len(self.pages)} pages)>'


def main():
    report_files = sorted(list(map(ReportFile, listdir(PDF_DIR))), key=lambda r: r.end_date)
    # f = report_files[0]
    # print(f)

    response: t.List[t.Dict[str, t.Union[str, int, float]]] = []

    for f in report_files:
        print(f, end=' ')
        lines: t.List[PaddedLine] = list(chain(*(page.padded_lines for page in f.pages)))
        sicknesses = (SicknessEntry(line, f.start_date, f.end_date, f.pdf_path) for line in lines)

        for sickness in sicknesses:
            print('.', end='', flush=True)
            response.append(sickness.json)

        print('[OK]')

    with open('response.json', 'w') as f:
        f.write(dumps(response, indent=2))
        # break


if __name__ == '__main__':
    main()
