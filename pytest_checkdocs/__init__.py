import contextlib
import re
import warnings

import pytest
import docutils.core
from build.util import project_wheel_metadata as load_metadata

from .py310compat import metadata as md


project_files = 'setup.py', 'setup.cfg', 'pyproject.toml'


@contextlib.contextmanager
def _suppress_deprecation():
    # pypa/pep517#122
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore', 'Text file object support is deprecated', module='tomli'
        )
        yield


def pytest_collect_file(path, parent):
    if path.basename not in project_files:
        return
    return CheckdocsItem.from_parent(parent, name='project')


class Description(str):
    @classmethod
    def from_md(cls, md):
        desc = cls(md.get('Description'))
        desc.content_type = md.get('Description-Content-Type', 'text/x-rst')
        return desc


class CheckdocsItem(pytest.Item):
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
        with _suppress_deprecation():
            return Description.from_md(ensure_clean(load_metadata('.')))

    @staticmethod
    def rst2html(value):
        docutils_settings = {}
        parts = docutils.core.publish_parts(
            source=value, writer_name="html4css1", settings_overrides=docutils_settings
        )
        return parts['whole']


def ensure_clean(metadata):
    """
    On Python 3.8 and later, pep517.meta returns a PathDistribution
    without clean metadata. Employ the adapter that comes with
    importlib_metadata 4 to get clean metadata.
    """
    try:
        metadata.json
    except AttributeError:
        metadata = md._adapters.Message(metadata)
    return metadata
