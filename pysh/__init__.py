import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Iterable, Optional, Union

try:
    import importlib.metadata

    __version__ = importlib.metadata.version("pysh")
except ImportError:
    import pkg_resources

    __version__ = pkg_resources.get_distribution("pysh").version

__all__ = ["sh", "cd", "env", "which"]


class CompletedProcessWrapper:
    stdout: str
    stderr: str
    returncode: int
    args: Any

    def __init__(self, completed_process: "subprocess.CompletedProcess[str]"):
        self.wrapped = completed_process

    def __getattribute__(self, __name: str):
        wrapped = object.__getattribute__(self, "wrapped")
        if __name == "wrapped":
            return wrapped
        else:
            return getattr(wrapped, __name)

    def __bool__(self) -> bool:
        return self.returncode == 0


def sh(
    *argv: Union[str, Iterable[str]], capture: Union[bool, None] = None, cwd: Union[str, Path] = ".", **kwargs: Any
) -> "CompletedProcessWrapper":
    flattened_argv = []
    for arg in argv:
        if isinstance(arg, str):
            flattened_argv.append(arg)
        else:
            flattened_argv.extend(arg)

    kwargs["stdin"] = subprocess.PIPE
    kwargs["shell"] = True
    kwargs["text"] = True
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    if "env" in kwargs:
        kwargs["env"].update(os.environ)
    else:
        kwargs["env"] = os.environ

    result = subprocess.run(flattened_argv, cwd=cwd, **kwargs)
    return CompletedProcessWrapper(result)


@contextmanager
def cd(path: Union[str, Path]) -> Generator[Path, None, None]:
    if isinstance(path, str):
        path = Path(path)
    cwd = Path.cwd().absolute()
    os.chdir(path)
    yield path
    os.chdir(cwd)


@contextmanager
def env(**kwargs: str) -> Generator[None, None, None]:
    old_values = {key: os.environ.get(key) for key in kwargs}
    os.environ.update(kwargs)

    yield

    for key, value in old_values.items():
        if value is not None:
            os.environ[key] = value
        else:
            del os.environ[key]


def which(cmd: str) -> Optional[str]:
    """Tells you whether a program/function/alias is available

    Doesn't necessarily return a path because it uses 'type' in unix
    """
    if sys.platform.startswith("win32"):
        return shutil.which(cmd)
    else:
        response = sh(f"type {cmd}", capture=True)
        if response:
            return response.stdout
