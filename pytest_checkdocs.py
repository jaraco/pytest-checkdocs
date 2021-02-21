import textwrap
import contextlib

import pytest
import docutils.core
import importlib_metadata
from more_itertools import first


def pytest_collect_file(path, parent):
    """Filter files down to which ones should be checked."""
    return (
        CheckdocsItem.from_parent(parent, fspath=path)
        if path.basename == 'setup.py'
        else None
    )


class CheckdocsItem(pytest.Item, pytest.File):
    def __init__(self, fspath, parent):
        # ugly hack to add support for fspath parameter
        # Ref pytest-dev/pytest#6928
        super(CheckdocsItem, self).__init__(fspath, parent)

    @classmethod
    def from_parent(cls, parent, fspath):
        """
        Compatibility shim to support
        """
        try:
            return super(CheckdocsItem, cls).from_parent(parent, fspath=fspath)
        except AttributeError:
            # pytest < 5.4
            return cls(fspath, parent)

    def runtest(self):
        with self.monkey_patch_system_message() as reports:
            self.rst2html(self.get_long_description())
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

    def _find_local_distribution(self):
        return first(importlib_metadata.distributions(path=['.', 'src']))

    def get_long_description(self):
        # egg-info
        desc = self._find_local_distribution().metadata['Description']
        # the format is to indent lines 2 and later with 8 spaces, so
        # add 8 spaces to the beginning and then dedent.
        return textwrap.dedent(' ' * 8 + desc)

    @staticmethod
    def rst2html(value):
        docutils_settings = {}
        parts = docutils.core.publish_parts(
            source=value, writer_name="html4css1", settings_overrides=docutils_settings
        )
        return parts['whole']
