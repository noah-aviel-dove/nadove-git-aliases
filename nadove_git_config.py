#!/usr/bin/python3

"""
Create the alias file and include it in the git configuration.
"""

import argparse
import sys
from typing import Iterable

import arg_types
from environment import bash_script_prefix
from shell import Command

section_header = '[alias]'

indent = ' ' * 4

bash_hook = '#!bash'


def create_aliases(alias_templates: Iterable[str]) -> Iterable[str]:
    for alias in alias_templates:
        cmd, _, subst = alias.rstrip().partition('=')
        subst = subst.strip()
        yield f'{cmd} = !{bash_script_prefix + cmd}' if subst == bash_hook else alias


def create_config_file():
    with open('alias.template.gitconfig', 'r') as template_file:
        with open('alias.gitconfig', 'w') as alias_file:
            alias_file.write(section_header + '\n')
            for alias in create_aliases(template_file):
                alias_file.write(indent + alias + '\n')


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-c',
        '--create',
        help='Create the config file containing the aliases. '
             'Use `--include` for the aliases to take effect.',
        action='store_true'
    )
    parser.add_argument(
        '-i',
        '--include',
        help='Configure `git` to use the created aliases.',
        action='store_true'
    )
    parser.add_argument(
        '-x',
        '--exclude',
        help='Configure `git` to ignore the created aliases.',
        action='store_true'
    )
    parser.add_argument(
        f'--context',
        help='Config file location. '
             'If set, acts like the `--file` option for `git config`. '
             'If unset, acts like the `--global` option for `git config`.',
        type=arg_types.file_path,
        action='store'
    )
    args = parser.parse_args(argv)

    if args.include and args.exclude:
        raise argparse.ArgumentError(argument=None,
                                     message='Cannot specify both --include and --exclude')
    if args.create:
        create_config_file()
    if args.include:
        Command()



if __name__ == '__main__':
    main(sys.argv[1:])
