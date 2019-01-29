import textwrap
import contextlib
import itertools

import pytest
import docutils.core
import importlib_metadata


def pytest_collect_file(path, parent):
    """Filter files down to which ones should be checked."""
    return CheckdocsItem(path, parent) if path.basename == 'setup.py' else None


class CheckdocsItem(pytest.Item, pytest.File):

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
        resolvers = importlib_metadata.Distribution._discover_resolvers()
        dists = itertools.chain.from_iterable(
            resolver(path=['.', 'src'])
            for resolver in resolvers
        )
        dist, = dists
        return dist

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
            source=value,
            writer_name="html4css1",
            settings_overrides=docutils_settings)
        return parts['whole']
