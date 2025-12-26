import importlib.metadata

from docutils import writers

version = importlib.metadata.version('docutils')


def _instance_from_name(name):
    """
    As of docutils 0.22, writer_name got merged into writer.
    ``writer_name`` is now deprecated.
    ``writer`` now supports a string and will automatically
    get the writer class instance, but previous versions won't,
    so perform the adaptation.
    """
    return writers.get_writer_class(name)()


def identity(x):
    return x


writer = identity if version >= '0.22' else _instance_from_name
