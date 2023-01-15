import os

import pytest

from pysh import env


def test_new_env_has_not_been_altered():
    with env(one="bar") as environ:
        assert os.environ is environ
        assert os.environ["one"] == "bar"
    assert "one" not in os.environ


def test_new_env_has_been_deleted():
    with env(two="bar") as environ:
        assert os.environ is environ
        assert os.environ["two"] == "bar"
        del environ["two"]
    assert "two" not in os.environ


def test_new_env_has_been_altered():
    with env(three="bar") as environ:
        assert os.environ is environ
        assert os.environ["three"] == "bar"
        environ["three"] = "baz"
    assert os.environ["three"] == "baz"


def test_old_env_has_been_restored():
    os.environ["four"] = "bar"
    with env(four="baz") as environ:
        assert os.environ is environ
        assert os.environ["four"] == "baz"
    assert os.environ["four"] == "bar"


def test_old_env_has_been_restored_with_del_and_new():
    os.environ["five"] = "bar"
    with env(five="baz") as environ:
        assert os.environ is environ
        assert os.environ["five"] == "baz"
        environ["five"] = "qux"
    assert os.environ["five"] == "qux"


def test_without_with():
    env(six="bar")
    assert os.environ.get("six") == "bar"


def test_exception():
    with pytest.raises(NotImplementedError):
        with env(seven="bar"):
            raise NotImplementedError
    assert "seven" not in os.environ
