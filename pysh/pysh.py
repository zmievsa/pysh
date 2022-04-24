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

from .util import import_from_path

from .token_transformers import transform_source

__version__ = "0.2.0"
__all__ = ["P", "sh", "PIPE", "re", "typer", "sys", "os"]

PIPE = subprocess.PIPE
DEVNULL = subprocess.DEVNULL

RE_SHELLVAR = re.compile(r"\$[\w@#]+")


def sh(
    cmd: T.Union[str, T.List[str]],
    extra_env: T.Dict[str, str] = {},
    pipe_stdout=False,
    **kwargs,
) -> subprocess.CompletedProcess[str]:
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

    add_hook()
    module_name = argv[0][: -len(".pysh")]
    main_hack.main_name = module_name
    sys.path.insert(0, str(P(argv[0]).parent))
    importlib.import_module(module_name)


if __name__ == "__main__":
    main()
