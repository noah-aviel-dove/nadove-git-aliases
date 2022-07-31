#!/usr/bin/python3

"""
Expand the bash snippets used to express more complex git aliases into separate
shell scripts for convenient invocation.
"""

import argparse
import pathlib
import sys
from typing import Iterable

import arg_types
from environment import bash_script_prefix

cmd_head = '#' * 3


def write_script(
    path: pathlib.Path,
    lines: Iterable[str],
) -> None:
    with open(path, 'w') as f:
        f.writelines([
            f'#!/bin/bash\n',
            f'. $(dirname "$0")/../common.sh\n',
            *lines
        ])


def make_scripts(
    source_file_path: pathlib.Path,
    output_dir: pathlib.Path,
) -> None:
    with open(source_file_path) as alias_file:
        script_lines = []
        cmd_name = None
        for line in alias_file:
            if line.startswith(cmd_head):
                if script_lines:
                    write_script(output_dir / script_name, script_lines)
                    script_lines.clear()
                _, _, cmd_name = line.partition(cmd_head)
                cmd_name = cmd_name.strip()
                script_name = bash_script_prefix + cmd_name
            elif cmd_name is not None:
                script_lines.append(line)
        assert not script_lines, script_lines


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__
    )
    parser.add_argument(
        'source_file_path',
        help='The file containing the bash snippets to export to scripts',
        type=arg_types.file_path,
    )
    parser.add_argument(
        'output_dir',
        help='Directory to populate with bash scripts',
        type=arg_types.directory_path,
    )

    args = parser.parse_args(argv)

    make_scripts(args.source_file_path, pathlib.Path(args.output_dir))


if __name__ == '__main__':
    main(sys.argv[1:])
