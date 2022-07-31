#!/usr/bin/python3

"""
Create and manage the git aliases.

Alias configuration is managed by setting and unsetting `include.path` and
`include.<condition>.path` variables in the git configuration. Subsequent
invocations are not idempotent (although their practical impact should be) and
may pollute the configuration with multiple redundant entries. If the commands
provided here don't seem to be working or the state of the configuration is ever
confusing, you can use `git config [--global] [--file] --edit` to view or edit
the variables directly.
"""

import argparse
from enum import (
    Enum,
)
import sys
from typing import (
    Iterable,
    Optional,
    Union,
)

import attr

import arg_types
import environment as env
from shell import (
    GitCommand,
)

section_header = '[alias]'

indent = ' ' * 4

bash_hook = '#!bash'


def create_aliases(alias_templates: Iterable[str]) -> Iterable[str]:
    for alias in alias_templates:
        cmd, _, subst = alias.rstrip().partition(' = ')
        if subst == bash_hook:
            subst = f'!{env.bash_script_prefix + cmd}'
        yield f'{cmd} = {subst}'


def create_config_file():
    with open(env.alias_file, 'w') as out_file:
        out_file.write(section_header + '\n')
        with open(env.template_file, 'r') as in_file:
            for alias in create_aliases(in_file):
                out_file.write(indent + alias + '\n')


class ConfigAction(Enum):
    get = '--get-regexp'
    add = '--add'
    rm = '--unset-all'


@attr.s(auto_attribs=True, frozen=True, kw_only=True)
class ConfigEntryTask:
    file: Optional[str]
    condition: Union[None, str, bool]
    action: ConfigAction

    @property
    def context(self) -> list[str]:
        return ['--global'] if self.file is None else ['--file', self.file]

    @property
    def key(self) -> str:
        return 'include.path' if self.condition is None else f'includeIf.{self.condition}.path'

    @property
    def cmd(self, verbose: bool = False, dry: bool = False) -> GitCommand:
        return GitCommand(
            'config',
            *self.context,
            self.action.value,
            self.key,
            env.alias_file,
        )


def main(
    create: bool,
    include: list[Optional[str]],
    exclude: list[Optional[str]],
    file: Optional[str],
):
    if create:
        create_config_file()

    for conditions, action in [
        (exclude, ConfigAction.rm),
        (include, ConfigAction.add)
    ]:
        for condition in conditions:
            task = ConfigEntryTask(file=file, condition=condition, action=action)
            print(*task.cmd.args)
            task.cmd.exec()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, add_help=True)
    parser.add_argument(
        '-c',
        '--create',
        help='''
        Create the file containing the aliases.
        Use `--include` for the aliases to take effect.
        ''',
        action='store_true'
    )
    parser.add_argument(
        '-i',
        '--include',
        help='Configure `git` to use the created aliases.',
        default=[],
        action='append_const',
        const=None
    )
    parser.add_argument(
        '-if',
        '--include-if',
        dest='include',
        metavar='CONDITION',
        help='''
        Configure `git` to use the created aliases if a particular condition is met.

        Multiple conditions can be in effect at once. Each condition is stored 
        as a separate entry in the git configuration. The aliases will be used
        if any condition is satisfied. Using `--include` is equivalent to
        specifying a condition that is always satisfied, and therefore makes any
        explicit conditions pointless.

        For information on the syntax and semantics of conditions, see the
        `Conditional includes` section from `git config --help`.
        ''',
        action='append'
    )
    parser.add_argument(
        '-x',
        '--exclude',
        help='''
        Inverse operation for `--include`.
        Does not remove conditions specified using `--include-if`.
        ''',
        default=[],
        action='append_const',
        const=None
    )
    parser.add_argument(
        '-xf',
        '--exclude-if',
        dest='exclude',
        metavar='CONDITION',
        help='''
        Inverse operation for `--include-if`. 
        The condition must be an exact match for the operation you are trying to undo.
        ''',
        action='append'
    )
    parser.add_argument(
        '-f',
        '--file',
        type=arg_types.file_path,
        help='''
        Config file location. 
        If set, acts like the `--file` option for `git config`.
        If unset, acts like the `--global` option for `git config`.
        '''
    )
    args = parser.parse_args(sys.argv[1:])
    main(**vars(args))
