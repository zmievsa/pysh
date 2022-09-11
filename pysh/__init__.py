import os
from pathlib import Path
import subprocess
from typing import Generator, Union, overload


@overload
def sh(*argv, capture: None = None, cwd: Union[str, Path] = ".", **kwargs) -> bool:
    ...


@overload
def sh(*argv, capture: bool = True, cwd: Union[str, Path] = ".", **kwargs) -> "subprocess.CompletedProcess[str]":
    ...


def sh(*argv, capture: Union[bool, None] = None, cwd: Union[str, Path] = ".", **kwargs):
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
    return CompletedProcessWrapper(result)


def cd(path: Union[str, Path]) -> Generator[Path, None, None]:
    if isinstance(path, str):
        path = Path(path)
    cwd = Path.cwd().absolute()
    os.chdir(path)
    yield path
    os.chdir(cwd)


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
