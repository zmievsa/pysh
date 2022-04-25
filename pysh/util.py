import importlib.util
import sys
import types
import typing as T
from dataclasses import dataclass
from pathlib import Path

from typing_extensions import Never


@dataclass
class MutableBool:
    value: bool

    def set(self, value: bool) -> None:
        self.value = value


def import_from_path(
    module_name: str,
    path: Path,
    preprocess: T.Optional[T.Callable[[bytes], bytes]] = None,
    trim_traceback: bool = False,
) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not (spec and spec.loader):
        raise TypeError(
            f"File loader for {path} was not found. That most likely means that the file extension is not valid."
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        # A cute little trick to preprocess code before running it
        if preprocess is not None:
            original_source_to_code = spec.loader.source_to_code  # type: ignore

            def source_to_code(data: bytes, path, *, _optimize=-1):
                return original_source_to_code(preprocess(data), path, _optimize=_optimize)

            spec.loader.source_to_code = source_to_code  # type: ignore
            original_dont_write_bytecode = sys.dont_write_bytecode
            sys.dont_write_bytecode = True
            spec.loader.exec_module(module)
            sys.dont_write_bytecode = original_dont_write_bytecode
            spec.loader.source_to_code = original_source_to_code  # type: ignore
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
            exc = (
                "Traceback (most recent call last):\n"
                + exc[exc.find("_call_with_frames_removed\n") + len("_call_with_frames_removed\n") :]
            )
        sys.stderr.write(exc)
        raise

    return module


def __raise_exception__(exc: BaseException) -> Never:
    raise exc
