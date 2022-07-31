import subprocess
from typing import Optional


class Command:

    def __init__(self, *args: Optional[str]):
        self.args = [arg for arg in args if arg is not None]

    def exec(self) -> subprocess.CompletedProcess:
        return subprocess.run(self.args)

    def exec_out(self) -> bytes:
        return subprocess.check_output(self.args)


class GitCommand(Command):

    def __init__(self, *args: Optional[str]):
        super().__init__('git', *args)
