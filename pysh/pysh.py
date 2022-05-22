import argparse
import importlib
import importlib.abc
import importlib.util
import os
import re
import subprocess
import sys
import typing as T
from pathlib import Path as P

import typer
from ideas import import_hook, main_hack

from .token_transformers import transform_source
from .util import MutableBool, __raise_exception__

__version__ = "1.1.3"
__all__ = ["P", "sh", "re", "typer", "sys", "os", "__pysh_check_returncodes__"]

PIPE = subprocess.PIPE
DEVNULL = subprocess.DEVNULL
__last_bash_cmd_returncode__ = 0
__pysh_check_returncodes__ = MutableBool(True)


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
    result = subprocess.run(cmd, shell=True, text=True, check=__pysh_check_returncodes__.value, **kwargs)
    __last_bash_cmd_returncode__ = result.returncode
    return result


def add_hook():
    """Creates and automatically adds the import hook in sys.meta_path"""
    hook = import_hook.create_hook(
        hook_name=__name__,
        transform_source=transform_source,
        extensions=[".pysh"],
    )
    return hook


def parse_argv(argv: T.List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="pysh")
    parser.add_argument("script", help="The script to run", nargs="?", default=None)
    parser.add_argument("-c", "--compile", help="Compile the script without running", action="store_true")
    parser.add_argument("-o", "--output", help="The compilation output file/directory", default=None)
    return parser.parse_args(argv)


def main(argv: T.Optional[T.List[str]] = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    args = parse_argv(argv)
    import builtins

    globals_ = globals()
    for attr in __all__:
        setattr(builtins, attr, globals_[attr])
    builtins.__raise_exception__ = __raise_exception__  # type: ignore
    builtins.__pysh_check_returncodes__ = __pysh_check_returncodes__  # type: ignore

    if args.script is None:
        from ideas import console

        console.configure(transform_source=transform_source)
        console.start(prompt=">>> ", banner=f"Pysh Console [Python version: {sys.version}]")
        exit(0)
    elif not P(args.script).is_file():
        print("Expecting a path to the script", file=sys.stderr)
        exit(1)
    elif args.compile:
        new_source = transform_source(P(args.script).read_text())
        new_source = "from pysh import *\n" + new_source
        if args.output is None:
            file = P(args.script).with_suffix(".py")
        else:
            output = P(args.output)
            if output.is_dir():
                file = output / P(args.script).with_suffix(".py")
            else:
                file = output
        file.write_text(new_source)
    else:
        add_hook()
        if argv is sys.argv:
            argv[0] = argv.pop(1)

        module_name = args.script[: -len(".pysh")]
        main_hack.main_name = module_name
        module_path = P(args.script).resolve()
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
