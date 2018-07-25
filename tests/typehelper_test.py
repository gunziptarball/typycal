import typing

import _pytest.monkeypatch
import pytest
from hamcrest import assert_that, equal_to, none
import setup
import typycal


def test_simple():
    @typycal.typed_dict
    class TypedDict(dict):
        some_string: str
        some_number: int
        some_list: typing.List[int]
        some_class_attribute = 'keep this!'
        some_blank: list = None

    d = TypedDict(some_string='foo', some_number='20', some_list=[1, 2, 3, 4], some_class_attribute='replace this!')

    assert_that(d.some_string, equal_to('foo'))
    assert_that(d.some_number, equal_to(20), 'should cast string to number')
    assert_that(d.some_list, equal_to([1, 2, 3, 4]), 'should leave complex type hints alone')
    assert_that(d.some_class_attribute, equal_to('keep this!'), 'should not tamper with existing attributes')
    assert_that(d, equal_to({
        'some_string': 'foo',
        'some_number': 20,
        'some_list': [1, 2, 3, 4],
        'some_class_attribute': 'replace this!'
    }))


def test_complex_types():
    class A:
        foo: str

        def __init__(self, foo: str):
            self.foo = foo

    @typycal.typed_dict
    class B(dict):
        a: A

    @typycal.typed_dict
    class C(dict):
        b: B

    assert_that(C(b=B(a=A('bar'))).b.a.foo, equal_to('bar'))


def test_strict():
    @typycal.typed_dict(strict=True)
    class D(dict):
        c: str

    with pytest.raises(TypeError):
        D(c=123)


def test_nulls():
    @typycal.typed_dict(strict=True, initialize_with_none=False)
    class D(dict):
        c: str

    with pytest.raises(AttributeError):
        d = D(q=456)
        assert d.c


def test_typed_dict_only_takes_dict_classes() -> None:
    with pytest.raises(TypeError):
        @typycal.typed_dict
        class Bad(object):
            dingus: bool

        assert_that(Bad)


@pytest.mark.parametrize('has_defaults,expected', (
        (True, {'foo': 2, 'bar': None}),
        (False, {'foo': 2})
), ids=('has defaults', 'no defaults'))
def test_none_initialization(has_defaults, expected):
    @typycal.typed_dict(initialize_with_none=has_defaults)
    class SomeClass(dict):
        foo: int
        bar: int

    o = SomeClass(foo=2)
    assert_that(o, equal_to(expected))


# noinspection PyPep8Naming
@pytest.fixture(name='FruitQty')
def _FruitQty():
    @typycal.typed_str(r'(?P<num>[0-9]+) (?P<fruit>.+)')
    class FruitQty(str):
        num: int
        fruit: str

    return FruitQty


def test_typed_str(FruitQty):
    fruit_qty = FruitQty('34 bananas')
    assert_that(fruit_qty.num, equal_to(34))
    assert_that(fruit_qty.fruit, equal_to('bananas'))


def test_typed_str_fails(FruitQty):
    with pytest.raises(ValueError):
        FruitQty('blahblahasdf')


def test_typed_str_with_nulls():
    @typycal.typed_str(r'(?P<required>[a-z]+)(?:\-(?P<optional>\d+))?')
    class SomeThing(str):
        required: str
        optional: int

    thing1 = SomeThing('foo-123')
    assert_that(thing1.required, equal_to('foo'))
    assert_that(thing1.optional, equal_to(123))
    thing2 = SomeThing('bar')
    assert_that(thing2.required, equal_to('bar'))
    assert_that(thing2.optional, none())


# noinspection PyUnusedLocal
@pytest.mark.parametrize('pattern,args,exc', [
    ('1234', (), ValueError),
    (r'(?P<foo>.),(bar)', (), ValueError),
    (r'(?P<foo>.),(bar)', ('bar',), ValueError),
    (r'(foo).(bar)', ('foo',), ValueError),
    (r'(?P<foo>).(baz)', ('foo',), ValueError),
    (r'(?P<baz>)', (), AttributeError),
    (r'(baz)', ('baz',), AttributeError)
])
def test_raises_with_bad_regex(pattern, args, exc):
    with pytest.raises(exc):
        @typycal.typed_str(pattern, *args)
        class BadStr(str):
            foo: str
            bar: str


@pytest.mark.parametrize('_type', (typing.Any, object, 42))
def test_complex_types_not_supported_yet(_type):
    with pytest.raises(AttributeError):
        @typycal.typed_str('(foo)', 'foo')
        class BadTypes(str):
            foo: _type


def test_cannot_define_reserved_types():
    with pytest.raises(ValueError):
        @typycal.typed_str(r'(\d+)', 'count')
        class BadNames(str):
            count: int

    with pytest.raises(AttributeError):
        @typycal.typed_dict
        class BadDict(dict):
            items: list


def test_formatting():
    @typycal.typed_str(r'^([0-9]+) things', 'qty', template='{qty} things')
    class Things(str):
        qty: int

    things = Things('20 things')
    assert things.qty == 20
    things.qty = 50
    assert things.qty == 50
    assert str(things) == '50 things'


@pytest.mark.parametrize('travis_env,travis_tag_env', (
        ('true', 'v0.5.1'),
        ('false', 'v0.5.0')
))
def test_get_version_fails(travis_env, travis_tag_env, monkeypatch: _pytest.monkeypatch.MonkeyPatch):
    import sys
    if 'upload' in sys.argv:
        sys.argv.remove('upload')
    assert setup.verify_version('0.5.0') == '0.5.0'

    sys.argv.append('upload')
    monkeypatch.setenv('TRAVIS', travis_env)
    monkeypatch.setenv('TRAVIS_TAG', travis_tag_env)
    with pytest.raises(Exception):
        setup.verify_version('0.5.0')


def test_get_version_succeeds(monkeypatch: _pytest.monkeypatch.MonkeyPatch):
    import sys
    if 'upload' in sys.argv:
        sys.argv.remove('upload')
    assert setup.verify_version('0.5.1') == '0.5.1'

    sys.argv.append('upload')
    monkeypatch.setenv('TRAVIS', 'true')
    monkeypatch.setenv('TRAVIS_TAG', 'v0.5.1')
    assert setup.verify_version('0.5.1') == '0.5.1'
