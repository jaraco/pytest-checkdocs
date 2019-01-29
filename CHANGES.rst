v1.2.0
======

Rely on importlib_metadata 0.8 to find local distribution.

Add hacky workaround for when package uses 'src' package layout. See
`importlib_metadata 42 <https://gitlab.com/python-devs/importlib_metadata/issues/42>`_
for more details.

v1.1.1
======

Fix package metadata to include the module.

v1.1.0
======

Instead of invoking setup.py, rely on
`importlib_metadata <https://pypi.org/project/importlib_metadata>`_
to load the long description.

v1.0.0
======

Initial implementation.
