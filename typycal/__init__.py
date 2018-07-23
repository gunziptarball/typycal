import functools
import re
import typing

_named_group_ptn = re.compile(r'\(\?P<([a-zA-Z0-9_]+)>')

_DICT_BUILTINS = set(dict.__dict__.keys())

_PROPERTY_FACTORY = {
    typing.MutableSequence: None
}

_MetaType = getattr(typing, '_GenericAlias', getattr(typing, 'GenericMeta', None))

# noinspection PyPep8Naming
class typed_str:
    def __init__(self, pattern: str, *attrs):
        self.pattern = re.compile(pattern)
        if not self.pattern.groups:
            raise ValueError(f'Pattern {pattern} does not contain any groups to match.')

        if len(attrs) == 0:
            if self.pattern.groups - len(self.pattern.groupindex) > 0:
                raise ValueError(f'You cannot supply a pattern with both named and unnamed groups.')

            attrs = list(range(self.pattern.groups))
            for g, i in self.pattern.groupindex.items():
                attrs[i - 1] = g
            self.attrs = attrs

        elif len(attrs) != self.pattern.groups:
            raise ValueError(f'Number of attrs provided do not match number of groups in pattern')

        else:
            self.attrs = attrs

    @staticmethod
    def _make_getter(attr: str, t: typing.Type):
        # noinspection PyMissingTypeHints
        def getter(o):
            # noinspection PyProtectedMember
            value = o._matches[attr]
            if value is None:
                return None
            return t(value)

        return getter

    def __call__(self, cls: typing.Type[str]):
        attr_types = {}
        for attr_name, attr_type in typing.get_type_hints(cls).items():
            if attr_type.__class__ != type:
                raise AttributeError(f'Unsupported type: {attr_type}')
            if not (attr_type in (int, float, str, bytes) or issubclass(attr_type, str)):
                raise AttributeError(f'Cannot have an overly complex type for {attr_name}')
            attr_types[attr_name] = attr_type

        for attr in self.attrs:
            if hasattr(cls, attr):
                raise ValueError(f'Bad attribute name {attr}')

            if attr not in attr_types:
                raise AttributeError(f'No type defined for attribute {attr}')

            prop = property(self._make_getter(attr, attr_types[attr]))
            setattr(cls, attr, prop)

        # noinspection PyUnusedLocal
        def new_init(obj: str, *args, **kwargs):
            str.__init__(obj)
            match = self.pattern.match(obj)
            if match is None:
                raise ValueError(f'String values for {cls.__name__} must match pattern {self.pattern.pattern}')

            matches = {k: val for k, val in zip(self.attrs, match.groups())}
            setattr(obj, '_matches', matches)

        cls.__init__ = new_init
        return cls


# noinspection PyPep8Naming
class typed_dict(object):
    def __new__(cls, *args, **kwargs) -> typing.Union['typed_dict', typing.Type[dict]]:
        if len(args) == 1 and isinstance(args[0], type) and len(kwargs) == 0:
            # allow decorator to be used without instantiation.
            return typed_dict()(args[0])
        return super().__new__(cls)

    # noinspection PyReturnFromInit
    def __init__(self, strict: bool = False, initialize_with_none=True):
        self.initialize_with_none = initialize_with_none
        self.strict = strict

    def _add_typed_property(self, cls: typing.Type[dict], attr_name: str, attr_type: typing.Optional[typing.Type]):
        # getter
        getter = self._create_typed_getter(cls, attr_name)

        # setter
        setter = self._create_typed_setter(attr_name, attr_type)

        setattr(cls, attr_name, property(getter, setter, dict.__delitem__))

    def _create_typed_getter(self, cls, attr_name) -> typing.Callable[[dict], typing.Any]:
        def getter(this: dict):
            try:
                return this[attr_name]
            except KeyError:
                pass
            raise AttributeError("'{}' object has no attribute '{}'".format(cls.__name__, attr_name))

        return getter

    def _create_typed_setter(self, attr_name: str, attr_type: typing.Optional[typing.Type]) -> typing.Callable[
        [dict, typing.Any], None]:
        def setter(this: dict, val: typing.Any):
            if val is not None and attr_type is not None and not isinstance(val, attr_type):
                if self.strict:
                    raise TypeError
                val = attr_type(val)
            this[attr_name] = val

        return setter

    def __call__(self, cls: typing.Type[dict]):
        if dict not in cls.mro():
            raise TypeError('You cannot apply typed_dict to a non-dictionary class')
        hints = typing.get_type_hints(cls)
        built_ins = set(hints.keys()).intersection(_DICT_BUILTINS)
        if built_ins:
            raise AttributeError(f'Cannot redefine built-in members {built_ins}')
        type_hints = {k: v for k, v in hints.items() if not hasattr(cls, k)}

        for attr_name, attr_type in type_hints.items():
            # if the type for the hint is not usable for whatever reason,
            # don't try to wrap.
            if not callable(attr_type) or isinstance(attr_type, _MetaType):
                attr_type = None
            # add the property to the dictionary class.
            self._add_typed_property(cls, attr_name, attr_type)

        # allow the option to make sure a "None" value is set for all type-declared
        # attributes

        cls.__init__ = _InitializedKeys(type_hints.keys(), self.initialize_with_none)(cls.__init__)
        return cls


class KeyedProperty(property):

    def __init__(self, key: str, doc: typing.Optional[str] = '', default: typing.Any = None, missing_keys_as_null=True):
        """
        Provides a way to give dictionary objects property-based access.

        This is an alternative to using the ``@typed_dict`` class decorator.

        >>> class Foo(dict):
        ...     bar:str = KeyedProperty('bar')
        ...     trouble:int = KeyedProperty('trouble', missing_keys_as_null=False)
        ...     defaulted:str = KeyedProperty('defaulted', default='dingus')
        ...     from_java_api:dict = KeyedProperty('FromJavaApi', default={})

        >>> foo = Foo(bar='bang', FromJavaApi={'foo': 'bar'})

        Now you see you can access, assign and delete keys as properties:
        >>> foo.bar
        'bang'
        >>> foo.from_java_api
        {'foo': 'bar'}
        >>> foo.bar = 'pow'
        >>> foo.bar
        'pow'
        >>> del foo.bar
        >>> foo.bar is None
        True

        You can override behavior so a true KeyError will be raised if the key is not present...default is to return
        None.
        >>> foo.trouble
        Traceback (most recent call last):
            ...
        KeyError: 'trouble'
        >>> foo.trouble = 10
        >>> foo.trouble + 10
        20

        Default values can also be provided.
        >>> foo.defaulted
        'dingus'
        >>> foo.defaulted = 'other'
        >>> foo.defaulted
        'other'
        """

        def getter(obj: dict):
            if key not in obj and default is not None:
                return default
            if missing_keys_as_null:
                return obj.get(key)
            return obj[key]

        def setter(obj: dict, val):
            obj[key] = val

        def deleter(obj: dict):
            del obj[key]

        super().__init__(getter, setter, deleter, doc)


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
