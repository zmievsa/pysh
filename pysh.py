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
    return subprocess.run(cmd, shell=True, check=True, text=True, **kwargs)


def import_from_path(
    module_name: str,
    path: P,
    preprocess: T.Optional[T.Callable[[bytes], bytes]] = None,
    trim_traceback: bool = True,
) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not (spec and spec.loader):
        raise TypeError(f"File loader for {path} was not found. Please, refer to importlib docs.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        # A cute little trick to preprocess code before running it
        if preprocess is not None:
            original_source_to_code = spec.loader.source_to_code
            def source_to_code(data: bytes, path, *, _optimize=-1):
                return original_source_to_code(preprocess(data), path, _optimize=_optimize)
            spec.loader.source_to_code = source_to_code
            original_dont_write_bytecode = sys.dont_write_bytecode
            sys.dont_write_bytecode = True
            spec.loader.exec_module(module)
            sys.dont_write_bytecode = original_dont_write_bytecode
            spec.loader.source_to_code = original_source_to_code
        else:
            spec.loader.exec_module(module)
    except SystemExit as e:
        raise
    except BaseException:
        if not trim_traceback:
            raise
        import traceback

        exc = traceback.format_exc()
        if "_call_with_frames_removed\n" in exc:
            exc = "Traceback (most recent call last):\n" + exc[exc.find("_call_with_frames_removed\n") + len("_call_with_frames_removed\n") :]
        sys.stderr.write(exc)
        raise

    return module



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
    except:
        exit(1)


if __name__ == "__main__":
    main()
