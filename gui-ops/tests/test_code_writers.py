import pytest

from ..code_writers import *

class AbstractCodeWriterTester(object):
    def test_bound_name(self):
        assert self.writer.bound_name == self.expected_bound_name_1
        assert self.second.bound_name == self.expected_bound_name_2

    def test_code(self):
        assert self.writer.code == self.expected_code


class TestCVCodeWriter(AbstractCodeWriterTester):
    def setup(self):
        CVCodeWriter.creation_counter = 0  # reset before each test
        self.writer = CVCodeWriter(name="test_cv",
                                   class_name="SomeClassOfCV",
                                   f="foo",
                                   bar=1.0,
                                   baz="qux",
                                   quux=[1.0, 2.0, 3.0])
        self.second = CVCodeWriter(name="extra",
                                   class_name="OtherClassCV",
                                   f="blah")
        self.expected_bound_name_1 = "cv_1"
        self.expected_bound_name_2 = "cv_2"

        # these tricks are to handle the order of args in the internal dict
        kwarg_strs = {
            'name': 'name="test_cv"',
            'f': 'f=foo',
            'bar': 'bar=1.0',
            'baz': 'baz="qux"',
            'quux': 'quux=[1.0, 2.0, 3.0]'
        }
        kwarg_part = ", ".join(kwarg_strs[name]
                               for name in self.writer.kwargs)
        self.expected_code = ('cv_1 = paths.SomeClassOfCV(' + kwarg_part
                              + ')')

class TestVolumeCodeWriter(AbstractCodeWriterTester):
    def setup(self):
        VolumeCodeWriter.creation_counter = 0  # reset before each test
        self.writer = VolumeCodeWriter(class_name="CVDefinedVolume",
                                       is_state=True,
                                       collectivevariable="foo",
                                       lambda_min=0.0,
                                       lambda_max=1.0,
                                       name="bar")
        self.second = VolumeCodeWriter(class_name="PeriodicCVDefinedVolume",
                                       is_state=False,
                                       collectivevariable="baz",
                                       lambda_min=0.0,
                                       lambda_max=1.0,
                                       period_min=-2.0,
                                       period_max=2.0)
        self.expected_bound_name_1 = "volume_1"
        self.expected_bound_name_2 = "volume_2"

        kwarg_strs = {
            'collectivevariable': 'collectivevariable=foo',
            'lambda_min': 'lambda_min=0.0',
            'lambda_max': 'lambda_max=1.0',
        }
        kwarg_part = ", ".join(kwarg_strs[name]
                               for name in self.writer.kwargs)
        self.expected_code = ("volume_1 = paths.CVDefinedVolume("
                              + kwarg_part + ").named('bar')")

    def test_unnamed(self):
        kwarg_strs = {
            'collectivevariable': "collectivevariable=baz",
            'lambda_min': 'lambda_min=0.0',
            'lambda_max': 'lambda_max=1.0',
            'period_min': 'period_min=-2.0',
            'period_max': 'period_max=2.0'
        }
        kwarg_part = ", ".join(kwarg_strs[name]
                               for name in self.second.kwargs)
        expected = ("volume_2 = paths.PeriodicCVDefinedVolume("
                    + kwarg_part + ")")
        assert self.second.code == expected
