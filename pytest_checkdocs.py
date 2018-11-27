import contextlib
import sys
import subprocess

import pytest
import docutils.core


def pytest_collect_file(path, parent):
    """Filter files down to which ones should be checked."""
    return CheckdocsItem(path, parent) if path.basename == 'setup.py' else None


class CheckdocsItem(pytest.Item, pytest.File):

    def runtest(self):
        self.reports = []
        with self.monkey_patch_system_message():
            self.rst2html(self.get_long_description())
        assert not self.reports

    @contextlib.contextmanager
    def monkey_patch_system_message(self):
        orig = docutils.utils.Reporter.system_message

        def system_message(reporter, level, message, *children, **kwargs):
            result = orig(reporter, level, message, *children, **kwargs)
            if level >= reporter.WARNING_LEVEL:
                # All reST failures preventing doc publishing go to reports
                # and thus will result to failed checkdocs run
                self.reports.append(message)

            return result

        docutils.utils.Reporter.system_message = system_message
        yield
        docutils.utils.Reporter.system_message = orig

    def get_long_description(self):
        cmd = [sys.executable, 'setup.py', '--long-description']
        return subprocess.check_output(
            cmd, universal_newlines=True)

    @staticmethod
    def rst2html(value):
        docutils_settings = {}
        parts = docutils.core.publish_parts(
            source=value,
            writer_name="html4css1",
            settings_overrides=docutils_settings)
        return parts['whole']
