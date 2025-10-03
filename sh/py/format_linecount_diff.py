"""
Input: stdin, each line in the format `$path $addition $deletion $old_linecount $new_linecount
Output: stdout, a pretty-printed table of the same info
"""
from abc import (
    ABC,
    abstractmethod,
)
from collections import defaultdict
from enum import Enum
import sys
from typing import (
    Mapping,
    Sequence,
)


class Color(Enum):
    RESET = (0,)
    GREEN = (0, 32)
    RED = (0, 31)
    YELLOW = (1, 33)

    def __str__(self):
        codes = ';'.join(map(str, self.value))
        return f'\033[{codes}m'

    def __len__(self):
        # Simplifies calculation of visual line lengths
        return 0


class ColumnEntry(ABC):

    def __init__(self, parent: 'Report'):
        self.parent = parent

    @abstractmethod
    def _parts(self) -> list[str | Color]:
        raise NotImplementedError

    @abstractmethod
    def col_class(self) -> type['ColumnEntry']:
        raise NotImplementedError

    def __str__(self) -> str:
        parts = self._parts()
        content = ''.join(map(str, parts))
        content_len = sum(map(len, parts))
        col_max_len = max(map(len, self.parent.column(self)))
        padding = ' ' * (col_max_len - content_len)
        # Can't use builtin formatter for padding due to color codes
        return f'{content}{padding}{Color.RESET}'

    def __len__(self):
        return sum(map(len, self._parts()))


class Value(ColumnEntry):

    def __init__(self, parent: 'Report', val):
        super().__init__(parent)
        self.val = val

    def _parts(self) -> list[str | Color]:
        return [str(self.val)]

    def col_class(self) -> type[ColumnEntry]:
        return type(self)

    def __bool__(self):
        return True


class Path(Value):

    class Summary(ColumnEntry):

        def col_class(self) -> type[ColumnEntry]:
            return Path

        def _parts(self) -> list[str | Color]:
            path_count = len(self.parent.column(self)) - 1
            return [f'({path_count})']


class CompValue(Value, ABC):

    def __init__(self, parent, val, comp_val):
        super().__init__(parent, val)
        self.comp_val = comp_val


class Sum(Value):

    @abstractmethod
    def _nz_parts(self) -> Sequence[str | Color]:
        raise NotImplementedError

    def __bool__(self) -> bool:
        return self.val != 0

    def _parts(self) -> list[str | Color]:
        return self._nz_parts() if self else []

    class Summary(ColumnEntry, ABC):

        def _parts(self) -> list[str | Color]:
            entries = [e for e in self.parent.column(self) if isinstance(e, Value)]
            total = sum(e.val for e in entries)
            return [f'({total:+d})'] if any(entries) else []


class CompSum(CompValue, Sum, ABC):

    def __bool__(self) -> bool:
        return super().__bool__() and self.comp_val != 0


class Addition(CompSum):

    def _nz_parts(self) -> list[str | Color]:
        return ['(', Color.GREEN, f'{self.val:+d}']

    class Summary(Sum.Summary):

        def col_class(self) -> type[ColumnEntry]:
            return Addition


class Deletion(CompSum):

    def __init__(self, parent: 'Report', val, comp_val):
        super().__init__(parent, -val, comp_val)

    def _nz_parts(self) -> list[str | Color]:
        return [Color.RED, f'{self.val:+d}', Color.RESET, ')']

    class Summary(Sum.Summary):

        def col_class(self) -> type['ColumnEntry']:
            return Deletion


class LineCountChange(Sum):

    def __init__(self, parent: 'Report', a, d):
        super().__init__(parent, a - d)
        self.a = a
        self.d = d

    def __bool__(self) -> bool:
        return self.a != 0 or self.d != 0

    def _nz_parts(self) -> Sequence[str | Color]:
        if not self.d:
            color = Color.GREEN
        elif not self.a:
            color = Color.RED
        else:
            color = Color.YELLOW
        return [color, f'{self.val:+d}']

    class Summary(Sum.Summary):

        def col_class(self) -> type['ColumnEntry']:
            return LineCountChange


class LineCount(CompValue):

    def _parts(self) -> list[str | Color]:
        parts = super()._parts()
        if self.val == 0:
            parts.insert(0, Color.RED)
        elif self.comp_val == 0:
            parts.insert(0, Color.GREEN)
        return parts

    class Summary(ColumnEntry):

        @abstractmethod
        def color(self) -> Color:
            raise NotImplementedError

        def _parts(self) -> list[str | Color]:
            gone = sum(
                1 for c in self.parent.column(self)
                if isinstance(c, CompValue) and c.comp_val == 0
            )
            return [self.color(), f'({gone})'] if gone else []


class OldLineCount(LineCount):

    class Summary(LineCount.Summary):

        def color(self) -> Color:
            return Color.RED

        def col_class(self) -> type[ColumnEntry]:
            return OldLineCount


class NewLineCount(LineCount):

    def _parts(self) -> list[str | Color]:
        parts = super()._parts()
        parts.insert(-1, '=')
        return parts

    class Summary(LineCount.Summary):

        def color(self) -> Color:
            return Color.GREEN

        def col_class(self) -> type[ColumnEntry]:
            return NewLineCount


class Report:

    def __init__(self):
        self._columns_by_cls: Mapping[
            type[ColumnEntry],
            list[ColumnEntry]
        ] = defaultdict(list)

    def column(self, entry: ColumnEntry) -> Sequence[ColumnEntry]:
        column = self._columns_by_cls[entry.col_class()]
        assert entry in column
        return column

    def add_row(self, line: str):
        print(line)
        added_lines, deleted_lines, path, old_linecount, new_linecount = line.rstrip().split()
        added_lines = int(added_lines)
        deleted_lines = int(deleted_lines)
        old_linecount = int(old_linecount)
        new_linecount = int(new_linecount)
        self._add_entry(Path, path)
        self._add_entry(OldLineCount, old_linecount, new_linecount)
        self._add_entry(LineCountChange, added_lines, deleted_lines)
        self._add_entry(Addition, added_lines, deleted_lines)
        self._add_entry(Deletion, deleted_lines, added_lines)
        self._add_entry(NewLineCount, new_linecount, old_linecount)

    def add_summary(self):
        for cls, column in self._columns_by_cls.items():
            if len(column) > 1:
                new_entry = self._add_entry(cls.Summary)
                assert column[-1] is new_entry

    def _add_entry(self, entry_cls: type[ColumnEntry], *args) -> ColumnEntry:
        entry = entry_cls(self, *args)
        self._columns_by_cls[entry.col_class()].append(entry)
        return entry

    def show(self) -> list[list[str]]:
        column_classes = [Path, OldLineCount, LineCountChange, Addition, Deletion, NewLineCount]
        columns = [self._columns_by_cls[cls] for cls in column_classes]
        i = 0
        rows = []
        while True:
            try:
                row = [str(column[i]) for column in columns]
            except IndexError:
                break
            rows.append(row)
            i += 1
        return rows


def main():
    report = Report()
    for line in sys.stdin:
        report.add_row(line)
    report.add_summary()
    for row in report.show():
        print(*row)


if __name__ == '__main__':
    main()
