from os.path import basename
import typing as t
from dataclasses import dataclass
from os import listdir

from visionary import DocumentFile, Page, parse_date

PDF_DIR = './downloads'


@dataclass(frozen=True, eq=True)
class ReportFile:
    pdf_path: str

    @property
    def _document(self) -> DocumentFile:
        return DocumentFile(self._json_path)

    @property
    def pages(self) -> t.List[Page]:
        return self._document.pages

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
    f = report_files[0]
    print(f)
    for page in f.pages:
        for line in page.lines:
            print(line)


if __name__ == '__main__':
    main()
