import importlib.util
import os
import re
import subprocess
import sys
import types
import typing as T
from pathlib import Path as P

import typer

__version__ = "0.2.0"
__all__ = ["P", "sh", "PIPE", "re", "typer", "sys", "os"]


PIPE = subprocess.PIPE


def sh(cmd: T.Union[str, T.List[str]], extra_env: T.Dict[str, str] = {}, **kwargs):
    kwargs["env"] = dict(**(kwargs.get("env") or os.environ), **extra_env)
    if kwargs.get("input") is None:
        kwargs["stdin"] = subprocess.PIPE
    return subprocess.run(cmd, shell=True, check=True, text=True, **kwargs)


def import_from_path(module_name: str, path: P) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not (spec and spec.loader):
        raise TypeError(f"File loader for {path} was not found. Please, refer to importlib docs.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    # exec_module is not always available which is why a linter won't be able to find it.
    # Docs do not state specific conditions for when it is available so if it's not, we
    # are okay with raising an ImportError.
    spec.loader.exec_module(module)  # CAN raise ImportError
    return module


def version_callback(show_version: bool):
    if show_version:
        typer.echo(__version__)
        raise typer.Exit()


def main(argv: T.Optional[T.List[str]] = None) -> None:
    if argv is None:
        argv = sys.argv
    if len(argv) < 2:
        import code

        code.interact(local={k: v for k, v in globals().items() if k in __all__})
        exit(0)
    elif not P(argv[1]).is_file():
        print("Expecting a path to the script", file=sys.stderr)
        exit(1)
    import builtins


    argv[0] = argv.pop(1)

    globals_ = globals()
    for attr in __all__:
        setattr(builtins, attr, globals_[attr])
    for index, arg in enumerate(argv):
        setattr(builtins, f"a{index}", arg)
    try:
        import_from_path(argv[0], P(argv[0]))
    except SystemExit:
        pass
    except BaseException:
        import traceback

        exc = traceback.format_exc()
        exc = exc[exc.find("_call_with_frames_removed\n") + len("_call_with_frames_removed\n") :]
        sys.stderr.write("Traceback (most recent call last):\n" + exc)
        exit(1)


if __name__ == "__main__":
    main()
