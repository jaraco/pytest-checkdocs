import textwrap
import contextlib
import re

import pytest
import docutils.core
import pep517.meta
from jaraco.functools import pass_none


def pytest_collect_file(path, parent):
    """Filter files down to which ones should be checked."""
    return (
        CheckdocsItem.from_parent(parent, fspath=path)
        if path.basename == 'setup.py'
        else None
    )


class Description(str):
    @classmethod
    def from_md(cls, md):
        cleaned = cls.repair_field(md.get('Description')) or md.get_payload()
        desc = cls(cleaned)
        desc.content_type = md.get('Description-Content-Type', 'text/x-rst')
        return desc

    @staticmethod
    @pass_none
    def repair_field(raw):
        """
        When the description is found as a field, the first
        line is not indented, but subsequent lines are indented
        with 8 spaces. Adjust by indenting the first line
        8 spaces and then dedent.
        """
        return textwrap.dedent(' ' * 8 + raw)


class CheckdocsItem(pytest.Item, pytest.File):
    def __init__(self, fspath, parent):
        # ugly hack to add support for fspath parameter
        # Ref pytest-dev/pytest#6928
        super().__init__(fspath, parent)

    @classmethod
    def from_parent(cls, parent, fspath):
        """
        Compatibility shim to support
        """
        try:
            return super().from_parent(parent, fspath=fspath)
        except AttributeError:
            # pytest < 5.4
            return cls(fspath, parent)

    def runtest(self):
        desc = self.get_long_description()
        method_name = f"run_{re.sub('[-/]', '_', desc.content_type)}"
        getattr(self, method_name)(desc)

    def run_text_markdown(self, desc):
        "stubbed"

    def run_text_x_rst(self, desc):
        with self.monkey_patch_system_message() as reports:
            self.rst2html(desc)
        assert not reports

    @contextlib.contextmanager
    def monkey_patch_system_message(self):
        reports = []
        orig = docutils.utils.Reporter.system_message

        def system_message(reporter, level, message, *children, **kwargs):
            result = orig(reporter, level, message, *children, **kwargs)
            if level >= reporter.WARNING_LEVEL:
                # All reST failures preventing doc publishing go to reports
                # and thus will result to failed checkdocs run
                reports.append(message)

            return result

        docutils.utils.Reporter.system_message = system_message
        yield reports
        docutils.utils.Reporter.system_message = orig

    def get_long_description(self):
        return Description.from_md(pep517.meta.load('.').metadata)

    @staticmethod
    def rst2html(value):
        docutils_settings = {}
        parts = docutils.core.publish_parts(
            source=value, writer_name="html4css1", settings_overrides=docutils_settings
        )
        return parts['whole']
