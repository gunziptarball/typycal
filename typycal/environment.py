import functools
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

        set_xform = _SET_XFORMS.get(attr_type, str)
        get_xform = _GET_XFORMS.get(attr_type, attr_type)

        def setter(_, v):
            self._environ_bag[name] = v if v is None else set_xform(v)

        def getter(_):
            val = self._environ_bag.get(name, default)
            return val if val is None else get_xform(val)

        def deleter(_):
            del self._environ_bag[name]

        # ensure default is in environment
        if default and name not in self._environ_bag:
            setter(None, default)

        return property(fget=getter, fset=setter, fdel=deleter)  # type: ignore

    def __new__(cls, *args, **kwargs) -> typing.Union['typed_env', typing.Type]:
        if len(args) == 1 and isinstance(args[0], type) and len(kwargs) == 0:
            # allow decorator to be used without instantiation.
            return typed_env()(args[0])

        return super().__new__(cls)

    def __init__(self, environ: typing.Dict[str, str] = None) -> None:
        self._environ_bag = environ or os.environ

    def _wrap_init(self, init):

        @functools.wraps(init)
        def wrapper(obj, *args, **kwargs):
            required_envs_on_init = getattr(obj, '__required_on_init__', None)
            if required_envs_on_init is not None:
                missing_vars = self._find_missing(required_envs_on_init)
                if missing_vars:
                    if len(missing_vars) == 1:
                        raise EnvironmentError(f"Variable '{missing_vars[0]}' is required, but has not been defined.")
                    else:
                        var_list = "','".join(missing_vars)
                        raise EnvironmentError(f"Variables '{var_list}' are required, but have not been defined.")
            init(obj, *args, **kwargs)

        return wrapper

    def __call__(self, cls: type):
        hints = typing.get_type_hints(cls)

        required_envs_on_init = getattr(cls, '__required_on_init__', None)
        if required_envs_on_init is not None:
            undeclared_requireds = ','.join(set(required_envs_on_init).difference(hints.keys()))
            if undeclared_requireds:
                raise AttributeError(f"Variables {undeclared_requireds} listed as required, but not declared in class")

        for attr_name, attr_type in hints.items():
            # if the type for the hint is not usable for whatever reason,
            # don't try to wrap.
            if not callable(attr_type) or isinstance(attr_type, _MetaType):
                warnings.warn(f'Unsupported type: {attr_type} for {cls.__name__}.{attr_name}')
                attr_type = str

            accessor = self._environ(attr_name, attr_type, getattr(cls, attr_name, None))
            setattr(cls, attr_name, accessor)

        setattr(cls, '__init__', self._wrap_init(cls.__init__))
        return cls

    def _find_missing(self, required_vars: typing.Collection[str]) -> typing.List[str]:
        return [v for v in required_vars if v not in self._environ_bag or self._environ_bag[v] is None]
