from __future__ import annotations

import contextlib
import pathlib
import re
import sys
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

import docutils.core
import docutils.nodes
import docutils.utils
import pytest
from jaraco.packaging import metadata

from .compat import docutils21

if TYPE_CHECKING:
    if sys.version_info >= (3, 12):
        from importlib.metadata import PackageMetadata
    else:
        from importlib_metadata import PackageMetadata

    from _pytest.nodes import Node
    from typing_extensions import Self

project_files = 'setup.py', 'setup.cfg', 'pyproject.toml'


def pytest_collect_file(file_path: pathlib.Path, parent: Node) -> CheckdocsItem | None:
    if file_path.name not in project_files:
        return None
    return CheckdocsItem.from_parent(parent, name='project')


class Description(str):
    content_type: str = ""

    @classmethod
    def from_md(cls, md: PackageMetadata) -> Self:
        desc = cls(md.get('Description'))
        desc.content_type = md.get('Description-Content-Type', 'text/x-rst')
        return desc


class CheckdocsItem(pytest.Item):
    def runtest(self) -> None:
        desc = self.get_long_description()
        method_name = f"run_{re.sub('[-/]', '_', desc.content_type)}"
        getattr(self, method_name)(desc)

    def run_text_markdown(self, desc: str) -> None:
        "stubbed"

    def run_text_x_rst(self, desc: str) -> None:
        with self.monkey_patch_system_message() as reports:
            self.rst2html(desc)
        assert not reports

    @contextlib.contextmanager
    def monkey_patch_system_message(self) -> Iterator[list[str | Exception]]:
        reports: list[str | Exception] = []
        orig = docutils.utils.Reporter.system_message

        def system_message(
            reporter: docutils.utils.Reporter,
            level: int,
            message: str | Exception,
            *children: docutils.nodes.Node,
            **kwargs: Any,
        ) -> docutils.nodes.system_message:
            result = orig(reporter, level, message, *children, **kwargs)
            if level >= reporter.WARNING_LEVEL:
                # All reST failures preventing doc publishing go to reports
                # and thus will result to failed checkdocs run
                reports.append(message)

            return result

        docutils.utils.Reporter.system_message = system_message  # type: ignore[assignment] # type-stubs expands the kwargs
        yield reports
        docutils.utils.Reporter.system_message = orig  # type: ignore[method-assign]

    def get_long_description(self) -> Description:
        return Description.from_md(metadata.load('.'))

    @staticmethod
    def rst2html(value: str) -> str | bytes:
        return docutils.core.publish_parts(
            source=value,
            writer=docutils21.writer('html4css1'),
        )['whole']
