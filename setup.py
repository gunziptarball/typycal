from distutils.core import setup
import sys

if sys.version_info.major < 3 or sys.version_info.minor < 6:
    raise RuntimeError("Only Python 3.6 and greater is supported.")

setup(
    name='typycal',
    description='Easily add type intelligence to simple Python objects',
    version='0.4.0',
    packages=['typycal'],
    url='https://github.com/cardinal-health/typycal',
    author='Cardinal Health',
    author_email='jackson.gilman@cardinalhealth.com',
    maintainer='Jackson J. Gilman',
    maintainer_email='jackson.gilman@cardinalhealth.com',
    license='Apache License 2.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Quality Assurance'
    ],
)
