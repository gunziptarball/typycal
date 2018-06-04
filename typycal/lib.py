import functools
import re
import typing

_named_group_ptn = re.compile(r'\(\?P<([a-zA-Z0-9_]+)>')


def _create_typed_getter(cls, attr_name) -> typing.Callable[[dict], typing.Any]:
    def getter(self: dict):
        try:
            return self[attr_name]
        except KeyError:
            pass
        raise AttributeError("'{}' object has no attribute '{}'".format(cls.__name__, attr_name))

    return getter


def _create_typed_setter(attr_name: str, attr_type: typing.Optional[typing.Type],
                         strict: bool) -> typing.Callable[[dict, typing.Any], None]:
    def setter(self: dict, val: typing.Any):
        if val is not None and attr_type is not None and not isinstance(val, attr_type):
            if strict:
                raise TypeError
            val = attr_type(val)
        self[attr_name] = val

    return setter


def _add_typed_property(cls: typing.Type[dict], attr_name: str, attr_type: typing.Optional[typing.Type], strict: bool):
    # getter
    getter = _create_typed_getter(cls, attr_name)

    # setter
    setter = _create_typed_setter(attr_name, attr_type, strict)

    setattr(cls, attr_name, property(getter, setter, dict.__delitem__))


class _InitializedKeys:
    """simple decorator to make sure dict values are initialized"""

    def __init__(self, keys: typing.Iterable[str], initialize_with_none: bool):
        self.keys = keys
        self.initialize_with_none = initialize_with_none

    def __call__(self, func: typing.Callable):
        @functools.wraps(func)
        def wrapped(obj: dict, *args, **kwargs):
            func(obj, *args, **kwargs)
            for k in self.keys:
                if k in obj:
                    v = getattr(obj, k)
                    setattr(obj, k, v)
                elif self.initialize_with_none:
                    setattr(obj, k, None)

        return wrapped
