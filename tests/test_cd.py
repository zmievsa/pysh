from pathlib import Path

import pytest

from pysh import cd


def test_cd_init():
    old_cwd = Path.cwd()
    with cd("/tmp") as path:
        assert path == Path("/tmp")
        assert Path.cwd() == Path("/tmp")
    assert Path.cwd() == old_cwd


def test_cd_context_manager():
    old_cwd = Path.cwd()
    with cd("/usr"):
        assert Path.cwd() == Path("/usr")
    assert Path.cwd() == old_cwd


def test_cd_exception():
    old_cwd = Path.cwd()
    with pytest.raises(FileNotFoundError):
        with cd("/nonexistent_folder"):
            pass
    assert Path.cwd() == old_cwd


def test_cd_str_input():
    with cd("/tmp"):
        assert Path.cwd() == Path("/tmp")


def test_cd_path_input():
    old_cwd = Path.cwd()
    path = Path("/usr")
    with cd(path):
        assert Path.cwd() == path
    assert Path.cwd() == old_cwd


def test_cd_relative_path():
    parent_path = Path.cwd().parent
    with cd(".."):
        assert Path.cwd() == parent_path


def test_cd_back_to_original_directory():
    original_cwd = Path.cwd()
    with cd("/tmp"):
        pass
    assert Path.cwd() == original_cwd


def test_cd_exception_raised_in_context():
    old_cwd = Path.cwd()
    with pytest.raises(NotImplementedError):
        with cd("/tmp"):
            raise NotImplementedError()
    assert Path.cwd() == old_cwd
