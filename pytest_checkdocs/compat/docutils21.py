from __future__ import annotations

import importlib.metadata
from typing import Any, Callable

from docutils import writers

version = importlib.metadata.version('docutils')


def _instance_from_name(name: str) -> writers.Writer[Any]:
    """
    As of docutils 0.22, writer_name got merged into writer.
    ``writer_name`` is now deprecated.
    ``writer`` now supports a string and will automatically
    get the writer class instance, but previous versions won't,
    so perform the adaptation.
    """
    return writers.get_writer_class(name)()


def identity(name: str) -> str:
    return name


writer: Callable[[str], str | writers.Writer[Any]] = (
    identity if version >= '0.22' else _instance_from_name
)
