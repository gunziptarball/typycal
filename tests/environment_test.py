import os
import typing

import pytest

import typycal


def test_typed_env(monkeypatch):
    monkeypatch.setenv('FOO', '100')
    monkeypatch.setenv('BAR', 'baz')

    @typycal.typed_env
    class Environment:
        FOO: int
        BAR: str

    env = Environment()
    assert env.FOO == 100
    assert env.BAR == 'baz'


def test_typed_env_with_defaults(monkeypatch):
    @typycal.typed_env
    class Environment:
        SOMETHING_WITH_DEFAULT: str = 'default_val'

    env = Environment()
    assert env.SOMETHING_WITH_DEFAULT == 'default_val'

    monkeypatch.setenv('SOMETHING_WITH_DEFAULT', 'other_val')
    assert env.SOMETHING_WITH_DEFAULT == 'other_val'


def test_typed_env_can_parse_dict(monkeypatch):
    monkeypatch.setenv('JSON_DATA', '{"foo": "bar"}')

    @typycal.typed_env
    class Environment:
        JSON_DATA: dict
        MISSING_DATA: dict
        DATA_W_DEFAULT: dict = {'baz': 'bang'}

    env = Environment()
    assert env.JSON_DATA == {'foo': 'bar'}
    assert env.MISSING_DATA is None
    env.MISSING_DATA = {'bing': 'bong'}
    assert os.getenv('MISSING_DATA') == '{"bing": "bong"}'
    assert env.DATA_W_DEFAULT == {'baz': 'bang'}


def test_typed_env_deleters(monkeypatch):
    monkeypatch.setenv('FOO', 'bar')

    @typycal.typed_env
    class Environment:
        FOO: str
        BAR: str = 'baz'

    env = Environment()
    del env.FOO
    del env.BAR
    assert env.FOO is None
    assert env.BAR == 'baz'


def test_typed_env_warning_on_unsupported_type(when):
    when('warnings').warn(...)

    # noinspection PyUnusedLocal
    @typycal.typed_env
    class Environment:
        # ridiculous type...
        BAD: typing.ContextManager[FileNotFoundError]


def test_typed_env_raises_on_missing_required_vars():
    @typycal.typed_env
    class Environment:
        __required_on_init__ = ('FOO', 'BAR')
        FOO: str
        BAR: str

    with pytest.raises(OSError) as e:
        Environment()
    assert str(e.value) == "Variables 'FOO','BAR' are required, but have not been defined."


def test_typed_env_raises_when_required_vars_not_declared_for_class():
    with pytest.raises(AttributeError):
        # noinspection PyUnusedLocal
        @typycal.typed_env
        class Environment:
            __required_on_init__ = ('FOO', 'NOT_THERE')
            FOO: str
