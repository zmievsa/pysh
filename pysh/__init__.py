import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Optional, Union

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
) -> CompletedProcessWrapper:
    """Run a shell command and display the output:

    >>> sh("git status")

    Capture the output of a shell command:

    >>> res = sh("git status", capture=True)
    >>> print(res.stdout)
    """
    flattened_argv = []
    for arg in argv:
        if isinstance(arg, str):
            flattened_argv.append(arg)
        else:
            flattened_argv.extend(arg)

    kwargs["stdin"] = subprocess.PIPE
    kwargs.pop("shell", None)
    kwargs.pop("text", None)
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    if "env" in kwargs:
        kwargs["env"].update(os.environ)
    else:
        kwargs["env"] = os.environ

    result = subprocess.run(flattened_argv, cwd=cwd, shell=True, text=True, **kwargs)
    return CompletedProcessWrapper(result)


class cd:
    """Changes the current working directory

    >>> cd("/tmp")
    >>> Path.cwd()
    PosixPath('/tmp')

    >>> with cd("/usr"):
    ...     Path.cwd()
    ...
    PosixPath('/usr')
    >>> Path.cwd()
    PosixPath('/tmp')

    """

    def __init__(self, path: Union[str, Path]) -> None:
        if isinstance(path, str):
            path = Path(path)
        self.path = path
        self.old_cwd = Path.cwd().resolve()
        os.chdir(path)

    def __enter__(self) -> Path:
        return self.path

    def __exit__(self, *args) -> None:
        os.chdir(self.old_cwd)


class env:
    """Sets environment variables for the duration of the context manager

    >>> env(var="value")
    >>> os.environ["var"]
    'value'

    >>> with env(var2="value2", var3="value3"):
    ...     os.environ["var2"], os.environ["var3"]
    ...
    ('value2', 'value3')

    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.old_environ = os.environ.copy()
        os.environ.update(self.kwargs)

    def __enter__(self) -> "os._Environ[str]":
        return os.environ

    def __exit__(self, exc_type, exc_val, exc_tb):
        for key in self.kwargs:
            in_old = key in self.old_environ
            in_new = key in os.environ
            new_eq_kwargs = os.environ.get(key) == self.kwargs.get(key)

            if not in_old and in_new and new_eq_kwargs:
                del os.environ[key]
            elif in_old and in_new and new_eq_kwargs:
                os.environ[key] = self.old_environ[key]


def which(cmd: str) -> Optional[str]:
    """Checks whether an executable/script/builtin is available

    Doesn't necessarily return a path because it uses 'type' in unix

    >>> which("git")
    '/usr/bin/git'

    >>> which("source")
    'source is a special shell builtin'

    >>> which("doesntexist")
    >>>
    """
    result = shutil.which(cmd)

    if result is not None or sys.platform.startswith("win32"):
        return result
    else:
        response = sh(f"type {cmd}", capture=True)
        if response:
            return response.stdout.strip()
