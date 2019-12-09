import typing as t
from dataclasses import dataclass
from os import listdir
from json import loads
from itertools import chain, groupby
from datetime import datetime

Vertex = (float, float)
BoxVertices = (Vertex, Vertex, Vertex, Vertex)
PRECISION = 2
PRINT_SCALE = 0.05
EMPTY_VERTICES: BoxVertices = ((0, 0), (0, 0), (0, 0), (0, 0))


def to_vertices(vertex_raw: t.Dict[str, float]) -> Vertex:
    return vertex_raw['x'], vertex_raw['y']


def parse_date(raw: str) -> datetime:
    return datetime.strptime(raw, '%d.%m.%Y')


def avg(x: t.Union[float, int], y: t.Union[float, int]) -> float:
    return (x + y) / 2


@dataclass(frozen=True, eq=True)
class VerticesMixin:
    raw: t.Dict[str, t.Any]

    @property
    def vertices(self) -> BoxVertices:
        """
        :return: (left-top, right-top, right-bottom, left-bottom)
        """
        try:
            return list(map(to_vertices, self.raw['boundingBox']['normalizedVertices']))
        except KeyError:
            return EMPTY_VERTICES

    @property
    def _y_positions(self) -> t.Iterable[float]:
        return (y for x, y in self.vertices)

    @property
    def _x_positions(self) -> t.Iterable[float]:
        return (x for x, y in self.vertices)

    @property
    def pos_top(self) -> float:
        return min(self._y_positions)

    @property
    def pos_bottom(self) -> float:
        return max(self._y_positions)

    @property
    def pos_left(self) -> float:
        return min(self._x_positions)

    @property
    def pos_right(self) -> float:
        return max(self._x_positions)

    @property
    def pos_x(self) -> float:
        return round(avg(self.pos_left, self.pos_right), PRECISION)

    @property
    def pos_y(self) -> float:
        return round(avg(self.pos_bottom, self.pos_top), PRECISION)

    @property
    def vertex_topleft(self):
        return self.vertices[0]

    @property
    def vertex_bottomleft(self):
        return self.vertices[3]

    @property
    def vertex_topright(self):
        return self.vertices[1]

    @property
    def vertex_bottomright(self):
        return self.vertices[2]

    @property
    def width(self) -> float:
        return self.pos_right - self.pos_left

    @property
    def height(self):
        return self.pos_bottom - self.pos_top

    @property
    def center(self) -> Vertex:  # to a global precision
        return self.pos_x, self.pos_y


@dataclass(frozen=True, eq=True)
class Symbol(VerticesMixin):
    raw: t.Dict[str, t.Any]

    @property
    def confidence(self) -> float:
        return self.raw['confidence']

    @property
    def _text(self) -> str:
        return self.raw['text']

    def __repr__(self):
        return f'<Symbol "{self._text}">'

    def __str__(self):
        return self._text


@dataclass(frozen=True, eq=True)
class Word(VerticesMixin):
    raw: t.Dict[str, t.Any]

    @property
    def symbols(self) -> t.List[Symbol]:
        return list(map(Symbol, self.raw['symbols']))

    @property
    def _text(self) -> str:
        return ''.join(map(str, self.symbols))

    @property
    def _char_width(self):
        return self.width / len(self._text)

    @property
    def padding(self) -> int:
        return int(PRINT_SCALE * self.pos_left / self._char_width)

    def __repr__(self):
        return f'<Word: {self._text}>'

    def __str__(self):
        return self._text


@dataclass(frozen=True, eq=True)
class Paragraph(VerticesMixin):
    raw: t.Dict[str, t.Any]

    @property
    def words(self) -> t.List[Word]:
        return list(map(Word, self.raw['words']))

    @property
    def confidence(self) -> float:
        return self.raw['confidence']

    @property
    def _text(self):
        return ' '.join(map(str, self.words))

    def __repr__(self):
        return f'<Paragraph at {self.vertices}: "{self._text}">'

    def __str__(self):
        return self._text


@dataclass(frozen=True, eq=True)
class Block(VerticesMixin):
    raw: t.Dict[str, t.Any]

    @property
    def paragraphs(self):
        return list(map(Paragraph, self.raw['paragraphs']))

    @property
    def block_type(self) -> str:
        return self.raw['blockType']

    @property
    def confidence(self) -> float:
        return self.raw['confidence']

    def __repr__(self):
        return f'<Block {self.vertices}, ({len(self.paragraphs)} paragraphs)>'


@dataclass(frozen=True, eq=True)
class Annotation:
    raw: t.Dict[str, t.Any]

    @property
    def width(self) -> int:
        return self.raw['width']

    @property
    def height(self) -> int:
        return self.raw['height']

    @property
    def confidence(self) -> float:
        return self.raw['confidence']

    @property
    def blocks(self) -> t.List[Block]:
        return list(map(Block, self.raw['blocks']))

    def __repr__(self):
        return f'<Annotation: width={self.width} height={self.height} confidence={self.confidence}>'


@dataclass(frozen=True, eq=True)
class Line(VerticesMixin):
    raw: t.List[Word]

    @property
    def words(self) -> t.List[Word]:
        return list(sorted(self.raw, key=lambda w: w.pos_x))

    @property
    def vertices(self) -> BoxVertices:  # override - this is an aggregation object
        """
        :return: (left-top, right-top, right-bottom, left-bottom)
        """
        top = self.words[0].pos_top
        bottom = self.words[0].pos_bottom
        left = self.words[0].pos_left
        right = self.words[-1].pos_right

        return (left, top), (right, top), (right, bottom), (left, bottom)

    @property
    def _char_width(self):
        return self.width / len(self._text)

    @property
    def _text(self) -> str:
        return ' '.join(map(str, self.words))

    def __repr__(self):
        return f'<Line>'

    def __str__(self):
        return self._text


@dataclass(frozen=True, eq=True)
class PaddedLine:
    line: Line
    char_width: float

    @property
    def _text(self) -> str:
        return str(self.line)

    def __str__(self) -> str:
        return ' ' * round(PRINT_SCALE * self.line.pos_left / self.char_width) + self._text


@dataclass(frozen=True, eq=True)
class Page:
    filename: str
    raw: t.Dict[str, t.Any]

    def __repr__(self) -> str:
        return f'<Page #{self.pagenum} of {self.filename}>'

    @property
    def _context(self) -> t.Dict[str, t.Any]:
        return self.raw['context']

    @property
    def _data(self) -> t.Dict[str, t.Any]:
        return self.raw['fullTextAnnotation']

    @property
    def pagenum(self) -> int:
        return self._context['pageNumber']

    @property
    def text(self) -> str:
        return self._data['text']

    @property
    def _annotations(self) -> t.List[Annotation]:
        return list(map(Annotation, self._data['pages']))

    @property
    def paragraphs(self) -> t.List[Paragraph]:
        annotations = self._annotations
        blocks: t.Iterable[Block] = chain(*(a.blocks for a in annotations))
        return list(chain(*(b.paragraphs for b in blocks)))

    @property
    def words(self) -> t.List[Word]:
        return list(chain(*((paragraph.words for paragraph in self.paragraphs))))

    @property
    def lines(self) -> t.Generator[Line, None, None]:
        by = lambda word: word.pos_y
        words = sorted(self.words, key=by)
        lines = groupby(words, key=by)

        for key, line in lines:
            yield Line(list(line))


@dataclass(frozen=True, eq=True)
class DocumentFile:
    json_path: str

    @property
    def _json_data(self) -> t.Dict[str, t.Any]:
        with open(self.json_path) as f:
            return loads(f.read())

    @property
    def _pages_data(self):
        return self._json_data['responses'][0]['responses']

    @property
    def pages(self) -> t.List[Page]:
        return [Page(self.json_path, raw) for raw in self._pages_data]

    def __repr__(self):
        return f'<DocumentFile: {self.json_path} ({len(self.pages)} pages)>'
