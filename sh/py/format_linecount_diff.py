"""
Input: stdin, each line in the format `$path $addition $deletion $old_linecount $new_linecount
Ouput: stdout, a pretty-printed table of the same info
"""
from abc import (
    ABC,
    abstractmethod,
)
from collections import defaultdict
from enum import Enum
import sys
from typing import (
    List,
    Mapping,
    Sequence,
    Type,
    Union,
)


class Color(Enum):
    RESET = (0,)
    GREEN = (0, 32)
    RED = (0, 31)
    YELLOW = (1, 33)

    def __str__(self):
        return f"\033[{';'.join(map(str, self.value))}m"


class ColumnEntry(ABC):
    values: Mapping[Type['ColumnEntry'], List['ColumnEntry']] = defaultdict(list)

    def __init__(self):
        self.values[self._col_class()].append(self)

    @abstractmethod
    def _parts(self) -> Sequence[Union[str, Color]]:
        raise NotImplementedError

    @abstractmethod
    def _col_class(self) -> Type['ColumnEntry']:
        raise NotImplementedError

    def _fmt_len(self) -> int:
        return sum(len(s) for s in self._parts() if isinstance(s, str))

    def _maxlen(self):
        return max(v._fmt_len() for v in self.values[self._col_class()])

    def __str__(self) -> str:
        content = ''.join(map(str, self._parts()))
        padding = ' ' * (self._maxlen() - self._fmt_len())
        return content + padding + str(Color.RESET)

    def __bool__(self) -> bool:
        return bool(self._parts)


class Value(ColumnEntry):

    def __init__(self, val):
        super().__init__()
        self.val = val

    def _parts(self) -> Sequence[Union[str, Color]]:
        return [str(self.val)]

    def _col_class(self) -> Type['ColumnEntry']:
        return type(self)


class Path(Value):
    class Summary(ColumnEntry):

        def _col_class(self) -> Type['ColumnEntry']:
            return Path

        def _parts(self) -> Sequence[Union[str, Color]]:
            return [f'({len(Value.values[Path]) - 1})']


class FriendValue(Value):

    def __init__(self, val, other_val):
        super().__init__(val)
        self.other = other_val


class Sum(Value):

    @abstractmethod
    def _nz_parts(self) -> Sequence[Union[str, Color]]:
        raise NotImplementedError

    def _show(self) -> bool:
        return self.val != 0

    def _parts(self) -> Sequence[Union[str, Color]]:
        if self._show():
            return self._nz_parts()
        else:
            return []

    class Summary(ColumnEntry, ABC):

        def _parts(self) -> Sequence[Union[str, Color]]:
            return [f'({sum(a.val for a in Value.values[self._col_class()] if a is not self):+d})']


class FriendSum(FriendValue, Sum, ABC):

    def _show(self) -> bool:
        return super()._show() and self.other != 0


class Addition(FriendSum):

    def _nz_parts(self) -> Sequence[Union[str, Color]]:
        return ['(', Color.GREEN, f'{self.val:+d}']

    class Summary(Sum.Summary):

        def _col_class(self) -> Type['ColumnEntry']:
            return Addition


class Deletion(FriendSum):

    def __init__(self, val, other_val):
        super().__init__(-val, other_val)

    def _nz_parts(self) -> Sequence[Union[str, Color]]:
        return [Color.RED, f'{self.val:+d}', Color.RESET, ')']

    class Summary(Sum.Summary):

        def _col_class(self) -> Type['ColumnEntry']:
            return Deletion


class LineCountChange(Sum):

    def __init__(self, a, d):
        super().__init__(a - d)
        self.a = a
        self.d = d

    def _show(self) -> bool:
        return self.a != 0 or self.d != 0

    def _nz_parts(self) -> Sequence[Union[str, Color]]:
        return [Color.GREEN if not self.d else Color.RED if not self.a else Color.YELLOW, f'{self.val:+d}']

    class Summary(Sum.Summary):

        def _col_class(self) -> Type['ColumnEntry']:
            return LineCountChange


class LineCount(FriendValue):

    def _parts(self) -> Sequence[Union[str, Color]]:
        return [
            *((Color.RED,) if self.val == 0 else (Color.GREEN,) if self.other == 0 else ()),
            str(self.val)
        ]

    class Summary(ColumnEntry):

        @abstractmethod
        def color(self) -> Color:
            raise NotImplementedError

        def _parts(self) -> Sequence[Union[str, Color]]:
            gone = sum(1 for c in Value.values[self._col_class()] if c is not self and c.other == 0)
            return [self.color(), f'({gone})'] if gone else ''


class OldLineCount(LineCount):
    class Summary(LineCount.Summary):

        def color(self) -> Color:
            return Color.RED

        def _col_class(self) -> Type['ColumnEntry']:
            return OldLineCount


class NewLineCount(LineCount):
    class Summary(LineCount.Summary):

        def color(self) -> Color:
            return Color.GREEN

        def _col_class(self) -> Type['ColumnEntry']:
            return NewLineCount

    def _parts(self) -> Sequence[Union[str, Color]]:
        p = list(super()._parts())
        p.insert(-1, '=')
        return p


parse_cols = [Addition, Deletion, Path, OldLineCount, NewLineCount]
print_cols = [Path, OldLineCount, LineCountChange, Addition, Deletion, NewLineCount]

table = []
for line in sys.stdin:
    row = {
        c: (v if c is Path else int(v))
        for v, c in zip(line.rstrip().split(), parse_cols)
    }
    row = [
        Path(row[Path]),
        OldLineCount(row[OldLineCount], row[NewLineCount]),
        LineCountChange(row[Addition], row[Deletion]),
        Addition(row[Addition], row[Deletion]),
        Deletion(row[Deletion], row[Addition]),
        NewLineCount(row[NewLineCount], row[OldLineCount])
    ]
    assert list(map(type, row)) == print_cols, row
    table.append(row)

if len(table) > 1:
    table.append([c.Summary() for c in print_cols])

for row in table:
    print(*row)
