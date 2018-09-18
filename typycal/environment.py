import json
import os
import typing
import warnings

_MetaType = getattr(typing, '_GenericAlias', getattr(typing, 'GenericMeta', None))

_GET_XFORMS: typing.Dict[type, typing.Callable[[str], typing.Any]] = {
    dict: lambda s: s and (s if isinstance(s, dict) else json.loads(s))
}

_SET_XFORMS: typing.Dict[type, typing.Callable[[typing.Any], str]] = {
    dict: lambda d: d and json.dumps(d)
}


class typed_env:
    def _environ(self, name: str,
                 attr_type: type,
                 default: str = None):

        env_getter = os.getenv if not self._environ_bag else self._environ_bag.get

        set_xform = _SET_XFORMS.get(attr_type, str)
        get_xform = _GET_XFORMS.get(attr_type, attr_type)

        def setter(_, v):
            os.environ[name] = v if v is None else set_xform(v)

        def getter(_):
            val = env_getter(name, default)
            return val if val is None else get_xform(val)

        def deleter(_):
            del os.environ[name]

        # ensure default is in environment
        if default and name not in os.environ:
            setter(None, default)

        return property(fget=getter, fset=setter, fdel=deleter)  # type: ignore

    def __new__(cls, *args, **kwargs) -> typing.Union['typed_env', typing.Type]:
        if len(args) == 1 and isinstance(args[0], type) and len(kwargs) == 0:
            # allow decorator to be used without instantiation.
            return typed_env()(args[0])
        return super().__new__(cls)

    def __init__(self, environ: typing.Dict[str, str] = None) -> None:
        self._environ_bag = environ or os.environ

    def __call__(self, cls: type):
        for attr_name, attr_type in typing.get_type_hints(cls).items():
            # if the type for the hint is not usable for whatever reason,
            # don't try to wrap.
            if not callable(attr_type) or isinstance(attr_type, _MetaType):
                warnings.warn(f'Unsupported type: {attr_type} for {cls.__name__}.{attr_name}')
                attr_type = str

            accessor = self._environ(attr_name, attr_type, getattr(cls, attr_name, None))
            setattr(cls, attr_name, accessor)
        return cls
