import importlib.util
import importlib
import importlib.abc
import os
import re
import subprocess
import sys
import typing as T
from pathlib import Path as P
from ideas import import_hook, main_hack

import typer

from .token_transformers import transform_source
from .util import __raise_exception__

__version__ = "0.2.0"
__all__ = ["P", "sh", "re", "typer", "sys", "os"]

PIPE = subprocess.PIPE
DEVNULL = subprocess.DEVNULL


def sh(
    cmd: T.Union[str, T.List[str]],
    extra_env: T.Dict[str, str] = {},
    pipe_stdout=False,
    **kwargs,
) -> subprocess.CompletedProcess:
    global __last_bash_cmd_returncode__
    kwargs["env"] = dict(**(kwargs.get("env") or os.environ), **extra_env)
    if pipe_stdout:
        kwargs["stdout"] = PIPE
        kwargs["stderr"] = subprocess.STDOUT
    result = subprocess.run(cmd, shell=True, text=True, **kwargs)
    __last_bash_cmd_returncode__ = result.returncode
    return result


def add_hook(verbose_finder=False):
    """Creates and automatically adds the import hook in sys.meta_path"""
    hook = import_hook.create_hook(
        hook_name=__name__,
        transform_source=transform_source,
        verbose_finder=verbose_finder,
        extensions=[".pysh"],
    )
    return hook


def main(argv: T.Optional[T.List[str]] = None) -> None:
    if argv is None:
        argv = sys.argv
    import builtins

    globals_ = globals()
    for attr in __all__:
        setattr(builtins, attr, globals_[attr])
    builtins.__raise_exception__ = __raise_exception__  # type: ignore

    if len(argv) < 2:
        from ideas import console

        console.configure(transform_source=transform_source)
        console.start(prompt=">>> ", banner=f"Pysh Console [Python version: {sys.version}]")
        exit(0)
    elif not P(argv[1]).is_file():
        print("Expecting a path to the script", file=sys.stderr)
        exit(1)

    add_hook()
    argv[0] = argv.pop(1)

    module_name = argv[0][: -len(".pysh")]
    main_hack.main_name = module_name
    module_path = P(argv[0]).resolve()
    sys.path.insert(0, str(module_path.parent))
    try:
        importlib.import_module(module_name)
    except Exception:
        import traceback

        exc = traceback.format_exc()
        seeked_str = f'  File "{module_path}"'
        if seeked_str in exc:

            exc = "Traceback (most recent call last):\n" + exc[exc.index(f'  File "{module_path}"') :]
            sys.stderr.write(exc)
            sys.exit(1)
        else:
            raise


if __name__ == "__main__":
    main()
