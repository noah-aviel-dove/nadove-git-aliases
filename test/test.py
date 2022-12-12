from collections import defaultdict
import itertools
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
from typing import (
    AbstractSet,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Union,
)
import unittest
from unittest import (
    TestCase,
    TestLoader,
)

from shell import (
    Command,
    GitCommand,
)

test_dir = Path(__file__).parent.absolute()
project_root = test_dir.parent


def alias_test(alias):
    def wrapper(method):
        try:
            aliases = method.aliases
        except AttributeError:
            aliases = method.aliases = set()
        aliases.add(alias)
        return method

    return wrapper


class TestCommand(GitCommand):

    def assertOutput(self, expected: Union[str, bytes]) -> None:
        raise NotImplementedError


class GitAliasTestCase(TestCase):
    temp_dir = None

    init_branch = 'test_main'
    child_branches = ['foo', 'bar', 'baz', 'quux']

    @property
    def setup_branches(self) -> List[str]:
        return [self.init_branch, *self.child_branches]

    def setUp(self) -> None:
        super().setUp()

        class _TestCommand(TestCommand):

            def assertOutput(self_, expected: Union[str, bytes]):
                if isinstance(expected, str):
                    expected = expected.encode('UTF8')
                self.assertEqual(expected, self_.exec_out())

        self.git_command = _TestCommand

    @classmethod
    def _setup(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        Command('bash', str(test_dir / 'setup.sh'), cls.temp_dir.name).exec()
        os.chdir(cls.temp_dir.name)

    @classmethod
    def _teardown(cls):
        del cls.temp_dir
        os.chdir(test_dir)

    def assertOutputsEqual(self, cmd1: Command, cmd2: Command):
        self.assertEqual(cmd1.exec_out(), cmd2.exec_out(), msg=(cmd1.args, cmd2.args))

    def assertGitOutputsEqual(self,
                              args1: Sequence[Optional[str]],
                              args2: Sequence[Optional[str]]):
        self.assertOutputsEqual(self.git_command(*args1), self.git_command(*args2))

    def _current_git_branch_command(self) -> TestCommand:
        return self.git_command('rev-parse', '--abbrev-ref', '@')

    def current_git_branch(self) -> bytes:
        return self._current_git_branch_command().exec_out()

    def previous_git_branch(self) -> bytes:
        return self.git_command('rev-parse', '--abbrev-ref', '@{-1}').exec_out()

    def assertBranch(self, branch: str) -> None:
        self._current_git_branch_command().assertOutput(f'{branch}\n')


class ReadOnlyGitAliasTestCase(GitAliasTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls._setup()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._teardown()
        super().tearDownClass()


class ReadWriteGitAliasTestCase(GitAliasTestCase):

    def setUp(self) -> None:
        super().setUp()
        self._setup()

    def tearDown(self) -> None:
        self._teardown()
        super().tearDown()


class TestLocalInfo(ReadOnlyGitAliasTestCase):

    @alias_test('rev')
    @alias_test('rev8')
    def test_parsing(self):
        refs = [
                   (ref, ref)
                   for ref in ['@', '@^', '@{-1}', *self.setup_branches]
               ] + [
                   ('@{-1}', '-'),
                   ('@', None)
               ]

        def _test(stock_refs, alias_refs):
            expected_output = self.git_command('rev-parse', *stock_refs).exec_out()
            with self.subTest(ref=alias_refs, cmd='rev'):
                self.git_command('rev', *alias_refs).assertOutput(expected_output)
            expected_output = b'\n'.join([ref[:8] for ref in expected_output.split()] + [b''])
            with self.subTest(ref=alias_refs, cmd='rev8'):
                self.git_command('rev8', *alias_refs).assertOutput(expected_output)

        for stock_ref, alias_ref in refs:
            _test([stock_ref], [alias_ref])

        _test(*zip(*refs[:-1]))

    @alias_test('s')
    def test_status(self):
        self.assertOutputsEqual(self.git_command('status', '-sb'),
                                self.git_command('s'))

    @alias_test('h')
    @alias_test('h1')
    @alias_test('l')
    @alias_test('l1')
    @alias_test('lg')
    def test_log(self):
        for alias_cmd, stock_cmd in [
            ('h', 'log --pretty=%h'),
            ('h -n1', 'log -n1 --pretty=%h'),
            ('h1', 'log -n1 --pretty=%h'),
            ('l', 'log --oneline'),
            ('l -n1', 'log -n1 --oneline'),
            ('l1', 'log -n1 --oneline'),
            ('lg', 'log --oneline --graph')
        ]:
            with self.subTest(alias=alias_cmd):
                self.assertGitOutputsEqual(shlex.split(stock_cmd),
                                           shlex.split(stock_cmd))

    @alias_test('lb')
    @alias_test('hb')
    def test_log_from_parent(self):
        pass

    @alias_test('b')
    def test_branch(self):
        self.assertBranch(self.init_branch)
        for ref, branch in [('', self.init_branch),
                            ('@', self.init_branch),
                            *[(branch, branch) for branch in self.setup_branches]]:
            with self.subTest(ref):
                self.git_command('b', ref).assertOutput(f'{branch}\n')
        prev_branch = self.previous_git_branch()
        for ref in ['-', '@{-1}']:
            with self.subTest(ref):
                self.git_command('b', ref).assertOutput(prev_branch)

    @alias_test('bll')
    def test_local_branch_list(self):
        self.git_command('bll').assertOutput('\n'.join([
            *[f'  {branch}' for branch in sorted(self.child_branches)],
            f'* {self.init_branch}\n'
        ]))

    @alias_test('bllg')
    def test_grep_local_branch(self):

        def expected_output(branches, current_branch):
            return '\n'.join(
                f'{"*" if branch == current_branch else " "} {branch}'
                for branch in branches
            ) + '\n'

        for pattern, expected_matches in [
            (None, sorted(self.setup_branches)),
            ('foo', ['foo']),
            ('ba[rz]', ['bar', 'baz']),
            ('*', ['test_main'])
        ]:
            with self.subTest(f'{expected_matches} =~ {pattern}'):
                self.git_command('bllg', pattern).assertOutput(expected_output(expected_matches, self.init_branch))

    @alias_test('dr')
    def test_show(self):
        refs = {r: r for r in [None, '@', '@^', *self.setup_branches]}
        refs['@{-1}'] = '-'
        for stock_ref, alias_ref in refs.items():
            with self.subTest(ref=alias_ref):
                self.assertGitOutputsEqual(['show', '--oneline', stock_ref],
                                           ['dr', alias_ref])

    @alias_test('d')
    @alias_test('dl')
    def test_diff_between_two_commits(self):
        refs = {
            ref: [ref]
            for ref in ['@', '@^', self.init_branch, self.child_branches[0], '@{-1}']
        }
        refs['@{-1}'].append('-')
        pairs = set()
        for stock_ref_1, stock_ref_2 in itertools.product(refs, refs):
            for alias_ref in refs[stock_ref_1]:
                pairs.add(((stock_ref_1, stock_ref_2), (alias_ref, stock_ref_2)))
            for alias_ref in refs[stock_ref_2]:
                pairs.add(((stock_ref_1, stock_ref_2), (stock_ref_1, alias_ref)))

        for (stock_pair, alias_pair) in pairs:
            for stock_cmd, alias_cmd in [
                (['diff'], ['d']),
                (['diff', '--name-only'], ['dl'])
            ]:
                with self.subTest(' '.join([*alias_cmd, *alias_pair])):
                    self.assertGitOutputsEqual([*stock_cmd, *stock_pair], [*alias_cmd, *alias_pair])


class TestLocalReadWrite(ReadWriteGitAliasTestCase):

    @alias_test('co')
    def test_checkout(self):
        self.assertBranch(self.init_branch)
        branches = self.setup_branches
        for branch in self.setup_branches:
            self.git_command('co', branch).exec()
            self.assertBranch(branch)
            if branch == self.init_branch:
                self.assertRaises(FileNotFoundError, lambda: open('c.txt'))
            else:
                with open('c.txt') as f:
                    self.assertEqual([f'Editing on branch {branch}\n'], f.readlines())

        swap = self.git_command('co', '-')
        for i in [-2, -1]:
            swap.exec()
            self.assertBranch(branches[i])

        self.git_command('co', '@^').exec()
        self.assertBranch('HEAD')
        swap.exec()
        self.assertBranch(branches[i])

    @alias_test('d0')
    @alias_test('d')
    @alias_test('dl')
    @alias_test('dd')
    @alias_test('ddl')
    @alias_test('ds')
    @alias_test('dsl')
    @alias_test('a')
    @alias_test('r')
    @alias_test('rh')
    def test_dirty_working_tree(self):
        with self.subTest('clean'):
            self._check_is_dirty(False)
            self._check_dirty_files({})
            self._check_diff()

        for f in ['a', 'new']:
            Command('bash', '-c', f'echo overwrite {f}.txt >{f}.txt').exec()

        with self.subTest('dirty'):
            self._check_is_dirty(True)
            self._check_dirty_files({'M': {'a.txt'},
                                     '??': {'new.txt'}})
            self._check_diff()

        self._add(explicit={'a.txt'})

        with self.subTest('partial_staged'):
            self._check_is_dirty(True)
            self._check_dirty_files({'M': {'a.txt'},
                                     '??': {'new.txt'}})
            self._check_diff()

        self._add(explicit={'new.txt'})

        with self.subTest('fully_staged'):
            self._check_is_dirty(True)
            self._check_dirty_files({'M': {'a.txt'},
                                     'A': {'new.txt'}})
            self._check_diff()

        self._soft_reset_head(explicit={'new.txt'},
                              expected={'new.txt'})

        with self.subTest('after_partial_soft_reset'):
            self._check_is_dirty(True)
            self._check_dirty_files({'M': {'a.txt'},
                                     '??': {'new.txt'}})
            self._check_diff()

        self._soft_reset_head(explicit={'new.txt', 'a.txt'},
                              expected={'a.txt'})

        with self.subTest('after_full_soft_reset'):
            self._check_is_dirty(True)
            self._check_dirty_files({'M': {'a.txt'},
                                     '??': {'new.txt'}})
            self._check_diff()

        self._hard_reset_head(explicit={'a.txt'})

        with self.subTest('after_partial_hard_reset'):
            self._check_is_dirty(False)
            self._check_dirty_files({'??': {'new.txt'}})
            self._check_diff()

        self._hard_reset_head()

        # FIXME This is now pointless
        with self.subTest('after_full_hard_reset'):
            self._check_is_dirty(False)
            self._check_dirty_files({'??': {'new.txt'}})
            self._check_diff()

    def _check_diff(self):
        for alias_cmd, stock_cmd in [
            (['d'], ['diff', '@']),
            (['d', '@~2'], ['diff', '@~2']),
            (['dd'], ['diff']),
            (['ds'], ['diff', '--staged'])
        ]:
            for path in [
                [],
                ['--', 'a.txt'],
                ['--', 'a.txt', 'b.txt']
            ]:
                self.assertGitOutputsEqual(alias_cmd + path, stock_cmd + path)

    def _check_is_dirty(self, is_dirty: bool):
        try:
            output = self.git_command('d0').exec_out()
        except subprocess.CalledProcessError as e:
            self.assertTrue(is_dirty)
            self.assertEqual(1, e.returncode)
            output = e.output
        else:
            self.assertFalse(is_dirty)
        self.assertEqual(b'', output)

    def _add(self, *,
             explicit: AbstractSet[str],
             expected: Optional[AbstractSet[str]] = None):

        def msg(p):
            return f"add '{p}'\n"

        if expected is None:
            expected = explicit

        expected = ''.join(map(msg, sorted(expected)))
        self.git_command('a', *explicit).assertOutput(expected)

    def _soft_reset_head(self, *,
                         expected: AbstractSet[str],
                         explicit: Optional[AbstractSet[str]] = None):
        if explicit is None or (expected and expected != explicit):
            expected = 'Unstaged changes after reset:\n' + ''.join(f'M\t{p}\n' for p in sorted(expected))
        else:
            expected = ''

        if explicit:
            explicit = ['--', *explicit]

        self.git_command('r', *explicit).assertOutput(expected)

    def _check_dirty_files(self, expected_file_states: Mapping[str, AbstractSet[str]]):
        output = self.git_command('s').exec_out().decode('UTF8')
        output = [l.strip().split() for l in output.split('\n')[1:] if l]
        assert len({path for status, path in output}) == len(output), output
        file_states = defaultdict(set)
        for status, path in output:
            file_states[status].add(path)
        self.assertEqual(expected_file_states, file_states)

    def _hard_reset_head(self, *, explicit: AbstractSet[str] = frozenset()):
        if explicit:
            explicit = ['--', *explicit]
            expected = ''
        else:
            head = self.git_command('log', '-n1', '--pretty=%h %s').exec_out()
            expected = b'HEAD is now at ' + head
        self.git_command('rh', *explicit).assertOutput(expected)


# FIXME https://github.com/noah-aviel-dove/nadove-git-aliases/issues/20
@unittest.skip('Tests involving a remote repository are not implemented')
class TestRemote(GitAliasTestCase):

    @alias_test('bu')
    @alias_test('du')
    @alias_test('dul')
    @alias_test('ru')
    @alias_test('rhu')
    @alias_test('dru')
    @alias_test('p')
    @alias_test('pf')
    @alias_test('pu')
    @alias_test('pd')
    @alias_test('p')
    @alias_test('rhp')
    @alias_test('rhpf')
    @alias_test('rhpfc')
    @alias_test('rhpfci')
    @alias_test('mf')
    @alias_test('f')
    @alias_test('ff')
    @alias_test('fs')
    @alias_test('frhu')
    @alias_test('bl')
    def test(self):
        raise NotImplementedError


@unittest.skip('Cannot assert coverage until all existing aliases are covered')
class TestCoverage(TestCase):
    base_test_cls = GitAliasTestCase

    def _load_aliases(self) -> Iterable[str]:
        with open(project_root / 'alias.gitconfig') as f:
            for line in f:
                alias, _, definition = line.strip().partition(" = ")
                yield alias

    def _load_test_names(self) -> AbstractSet[str]:
        loader = TestLoader()
        return set.union(*(
            self._get_test_method_aliases(test)
            for suite in loader.loadTestsFromName(__name__)
            for test in suite
            if isinstance(test, self.base_test_cls)
        ))

    def _get_test_method_aliases(self, test: TestCase) -> AbstractSet[str]:
        test_id = test.id()
        _, _, method_name = test_id.rpartition('.')
        method = getattr(test, method_name)
        try:
            return method.aliases
        except AttributeError:
            raise RuntimeError(f'{test_id} is not mapped to any aliases')

    def test(self):
        defined = set(self._load_aliases())
        covered = self._load_test_names()
        self.assertEqual(defined, covered)

