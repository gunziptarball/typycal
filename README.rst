====================================================
`typycal` -- A handy tool to make type-aware classes
====================================================

.. image:: https://img.shields.io/pypi/v/typycal.svg
    :target: https://pypi.org/project/typycal/

.. image:: https://img.shields.io/pypi/pyversions/typycal.svg
    :target: https://pypi.org/project/typycal/

.. image:: https://travis-ci.org/cardinal-health/typycal.svg?branch=master
    :target: https://travis-ci.org/cardinal-health/typycal

.. image:: https://coveralls.io/repos/github/cardinal-health/typycal/badge.svg?branch=master
    :target: https://coveralls.io/github/cardinal-health/typycal?branch=master

.. note::

    Yes, Python 3.7 introduced data classes, which basically provide the
    majority of features this library offers.  Future development will likely cover helpers
    for this new feature.

This lightweight library is for the developer who enjoys the assistance provided
by Python's type annotations.

^^^^^^^^^^^^^
``typed_env``
^^^^^^^^^^^^^

If your Python program relies on a custom os environment, it can be difficult to remember the string names for all those variables.  This decorator will provide a means to deal with your environment in an object-oriented fashion.

>>> from typycal import typed_env
>>> import os
>>> import pathlib

For example, say your program obtains database connection info from the environment

>>> os.environ.update({'DB_HOSTNAME': 'localhost', 'DB_PORT': '3306'})
>>> os.getenv('DB_PORT')
'3306'

You can itemize all the environment variables you use in one class

>>> @typed_env
... class Environment:
...     DB_HOSTNAME: str
...     DB_PORT: int
...     DB_USER: str = 'default_user'
...     README_PATH: pathlib.Path = 'README.rst'
...     JSON_DATA: dict = {'foo': 'bar'}

Then you can create a singleton instance for use by the rest of your program

>>> env = Environment()

And your variables will be typed appropriately

>>> (env.DB_HOSTNAME, env.DB_PORT, env.DB_USER)
('localhost', 3306, 'default_user')

And maintained in env properly

>>> os.getenv('JSON_DATA')
'{"foo": "bar"}'

You can do some neat things...

>>> assert env.README_PATH.exists()

^^^^^^^^^^^^^^
``typed_dict``
^^^^^^^^^^^^^^

This decorator offers a simple, declarative means of converting a plain Python dictionary or string object into a type-aware object, with properties to access a defined set of keys.

Developers working with REST APIs or any data loaded as a dictionary can use typycal to effectively design "contracts" with their code, and ideally end up with more readable software

That said, since the release of Python 3.7, you likely will be better served with data classes.

Let's say you have a settings file sitting somewhere, and it's loaded into your
project as a dictionary (such as `json.load`, `yaml.safe_load`, etc...):

.. code:: json

    {
        "db": {
            "username": "maxwell",
            "password": "SECRET",
            "port": "5432",
            "use_ssl": false
        },
        "log_level": "DEBUG"
    }


...let's say this configuration gets real messy real quick.  It can be a
real pain to have to remember the names of all your keys for what
becomes a Python `dict`.  So, here's an easy way to wrap your project's
configuration in a type-aware object

>>> from typycal import typed_dict
>>> @typed_dict
... class DBConfig(dict):
...    username: str
...    password: str
...    port: int
...    use_ssl: bool

>>> @typed_dict
... class ProjectConfig(dict):
...     log_level: str
...     db: DBConfig

>>> settings = {
...     "db": {
...             'username': 'maxwell',
...             'password': 'SECRET',
...             'port': '5432',
...         },
...     'log_level': 'DEBUG'
... }
>>> config = ProjectConfig(settings)


>>> config.db.username == 'maxwell'
True

>>> config.db.port == 5432
True

See that?  Even though you passed a string for the port, because you explicitly defined the type, it was cast for you!
Now, let's try to access a missing property

>>> config.db.use_ssl is None
True

Note, an AttributeError wasn't raised because by default, `typed_dict` will decorate your class so that any unset
values which you have declared a type for will be set to `None`  You can disable this as follows

>>> @typed_dict(initialize_with_none=False)
... class StricterConfig(dict):
...        foo: str
...        bar: int

>>> StricterConfig({'foo': 30}).bar
Traceback (most recent call last):
    ...
AttributeError: 'StricterConfig' object has no attribute 'bar'

This makes the object-like treatment of the `dict` behave closer to how Python would yell at you about accessing
missing object attributes.

^^^^^^^^^^^^^
``typed_str``
^^^^^^^^^^^^^

Another handy thing this library gives you is a way to quickly validate a string with a regex, and then store the group
match values as attributes on the str, and access them.  Here's a (roughly) complete example


>>> model_pattern = r"([0-9]{4}) (Ford|Toyota) (.+)"

>>> from typycal import typed_str
>>> @typed_str(model_pattern, 'year', 'make', 'name')
... class CarModel(str):
...        year: int
...        make: str
...        name: str

>>> @typed_str(r'(?P<color>[A-Za-z]+) (?P<model>.+)')
... class Car(str):
...     color: str
...     model: CarModel

>>> my_car = Car('Brown 1985 Ford Crown Victoria')

Now we can get attributes for the matches!

>>> my_car.color == "Brown"
True

Nesting and types are honored as well!

>>> my_car.model.year == 1985
True

You can provide a template string as well to support (kinda) mutability.

>>> @typed_str(r'^([0-9]+) things', 'qty', template='{qty} things')
... class Things(str):
...     qty:int

>>> things = Things('20 things')
>>> things.qty = 50
>>> things
50 things

Note however, this only changes the behavior of ``__str__`` and ``__repr__``.  See the comparison of
the "new" value vs the original string value:

>>> things == '50 things', things == '20 things'
(False, True)

...so you'll need to explicity cast

>>> str(things) == '50 things'
True

----------
Change Log
----------

See CHANGELOG.rst