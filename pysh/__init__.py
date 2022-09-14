import importlib.metadata
import os
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Union

__version__ = importlib.metadata.version("pysh")


class CompletedProcessWrapper:
    def __init__(self, completed_process: subprocess.CompletedProcess):
        self.wrapped = completed_process

    def __getattribute__(self, __name: str):
        wrapped = object.__getattribute__(self, "wrapped")
        if __name == "wrapped":
            return wrapped
        else:
            return getattr(wrapped, __name)

    def __bool__(self):
        return self.returncode == 0  # type: ignore


def sh(*argv, capture: Union[bool, None] = None, cwd: Union[str, Path] = ".", **kwargs) -> subprocess.CompletedProcess:
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

    result = subprocess.run(argv, cwd=cwd, **kwargs)
    return CompletedProcessWrapper(result)  # type: ignore


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
