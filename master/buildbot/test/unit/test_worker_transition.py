# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

import mock
import new
import re
import sys

from twisted.trial import unittest

from buildbot.test.util.warnings import assertNotProducesWarnings
from buildbot.test.util.warnings import assertProducesWarning
from buildbot.worker_transition import DeprecatedWorkerAPIWarning
from buildbot.worker_transition import DeprecatedWorkerNameWarning
from buildbot.worker_transition import WorkerAPICompatMixin
from buildbot.worker_transition import _compat_name
from buildbot.worker_transition import define_old_worker_func
from buildbot.worker_transition import define_old_worker_method
from buildbot.worker_transition import define_old_worker_property
from buildbot.worker_transition import deprecatedWorkerModuleAttribute
from twisted.python.deprecate import deprecatedModuleAttribute
from twisted.python.versions import Version


class CompatNameGeneration(unittest.TestCase):

    def test_generic_rename(self):
        self.assertEqual(_compat_name("Worker"), "Slave")
        self.assertEqual(_compat_name("worker"), "slave")
        self.assertEqual(_compat_name("SomeWorkerStuff"), "SomeSlaveStuff")
        self.assertEqual(_compat_name("theworkerstuff"), "theslavestuff")

        self.assertRaises(AssertionError, _compat_name, "worKer")

    def test_dummy_rename(self):
        self.assertEqual(
            _compat_name("SomeWorker", compat_name="BuildSlave"),
            "BuildSlave")

        # Deprecated name by definition must contain "slave"
        self.assertRaises(AssertionError, _compat_name, "worker",
                          compat_name="somestr")
        # New name always contains "worker" instead of "slave".
        self.assertRaises(AssertionError, _compat_name, "somestr",
                          compat_name="slave")


class Test_deprecatedWorkerModuleAttribute(unittest.TestCase):

    def test_produces_warning(self):
        Worker = type("Worker", (object,), {})
        buildbot_module = new.module('buildbot_module')
        buildbot_module.Worker = Worker
        with mock.patch.dict(sys.modules,
                             {'buildbot_module': buildbot_module}):
            scope = buildbot_module.__dict__
            deprecatedWorkerModuleAttribute(scope, Worker)

            # Overwrite with Twisted's module wrapper.
            import buildbot_module

        with assertNotProducesWarnings(DeprecatedWorkerAPIWarning):
            W = buildbot_module.Worker
        self.assertIdentical(W, Worker)

        with assertProducesWarning(
                DeprecatedWorkerNameWarning,
                message_pattern=r"buildbot_module\.Slave was deprecated in "
                                r"Buildbot 0.9.0: Use Worker instead."):
            S = buildbot_module.Slave
        self.assertIdentical(S, Worker)

    def test_not_catched_warning(self):
        buildbot_module = new.module('buildbot_module')
        buildbot_module.deprecated_attr = 1
        with mock.patch.dict(sys.modules,
                             {'buildbot_module': buildbot_module}):
            deprecatedModuleAttribute(Version("Buildbot", 0, 9, 0),
                                      "test message",
                                      "buildbot_module",
                                      "deprecated_attr")

            # Overwrite with Twisted's module wrapper.
            import buildbot_module

        warnings = self.flushWarnings([self.test_not_catched_warning])
        self.assertEqual(len(warnings), 0)

        # Should produce warning
        buildbot_module.deprecated_attr

        warnings = self.flushWarnings([self.test_not_catched_warning])
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['category'], DeprecationWarning)
        self.assertIn("test message", warnings[0]['message'])

    def test_explicit_compat_name(self):
        Worker = type("Worker", (object,), {})
        buildbot_module = new.module('buildbot_module')
        buildbot_module.Worker = Worker
        with mock.patch.dict(sys.modules,
                             {'buildbot_module': buildbot_module}):
            scope = buildbot_module.__dict__
            deprecatedWorkerModuleAttribute(
                scope, Worker, compat_name="BuildSlave")

            # Overwrite with Twisted's module wrapper.
            import buildbot_module

        with assertNotProducesWarnings(DeprecatedWorkerAPIWarning):
            W = buildbot_module.Worker
        self.assertIdentical(W, Worker)

        with assertProducesWarning(
                DeprecatedWorkerNameWarning,
                message_pattern=r"buildbot_module\.BuildSlave was deprecated in "
                                r"Buildbot 0.9.0: Use Worker instead."):
            S = buildbot_module.BuildSlave
        self.assertIdentical(S, Worker)

    def test_explicit_new_name(self):
        BuildSlave = type("BuildSlave", (object,), {})
        buildbot_module = new.module('buildbot_module')
        buildbot_module.BuildSlave = BuildSlave
        with mock.patch.dict(sys.modules,
                             {'buildbot_module': buildbot_module}):
            scope = buildbot_module.__dict__
            deprecatedWorkerModuleAttribute(
                scope, BuildSlave,
                compat_name="BuildSlave",
                new_name="Worker")

            # Overwrite with Twisted's module wrapper.
            import buildbot_module

        with assertProducesWarning(
                DeprecatedWorkerNameWarning,
                message_pattern=r"buildbot_module\.BuildSlave was deprecated in "
                                r"Buildbot 0.9.0: Use Worker instead."):
            S = buildbot_module.BuildSlave
        self.assertIdentical(S, BuildSlave)

    def test_explicit_new_name_empty(self):
        BuildSlave = type("BuildSlave", (object,), {})
        buildbot_module = new.module('buildbot_module')
        buildbot_module.BuildSlave = BuildSlave
        with mock.patch.dict(sys.modules,
                             {'buildbot_module': buildbot_module}):
            scope = buildbot_module.__dict__
            deprecatedWorkerModuleAttribute(
                scope, BuildSlave,
                compat_name="BuildSlave",
                new_name="")

            # Overwrite with Twisted's module wrapper.
            import buildbot_module

        with assertProducesWarning(
                DeprecatedWorkerNameWarning,
                message_pattern=re.escape(
                    "buildbot_module.BuildSlave was deprecated in "
                    "Buildbot 0.9.0: Don't use it.")):
            S = buildbot_module.BuildSlave
        self.assertIdentical(S, BuildSlave)

    def test_module_reload(self):
        Worker = type("Worker", (object,), {})
        buildbot_module = new.module('buildbot_module')
        buildbot_module.Worker = Worker
        with mock.patch.dict(sys.modules,
                             {'buildbot_module': buildbot_module}):
            scope = buildbot_module.__dict__
            deprecatedWorkerModuleAttribute(scope, Worker)
            # Overwrite with Twisted's module wrapper.
            import buildbot_module

            # Module reload is effectively re-run of module contents.
            Worker = type("Worker", (object,), {})
            buildbot_module.Worker = Worker
            scope = buildbot_module.__dict__
            deprecatedWorkerModuleAttribute(scope, Worker)
            # Overwrite with Twisted's module wrapper.
            import buildbot_module

        with assertNotProducesWarnings(DeprecatedWorkerAPIWarning):
            W = buildbot_module.Worker
        self.assertIdentical(W, Worker)

        with assertProducesWarning(
                DeprecatedWorkerNameWarning,
                message_pattern=r"buildbot_module\.Slave was deprecated in "
                                r"Buildbot 0.9.0: Use Worker instead."):
            S = buildbot_module.Slave
        self.assertIdentical(S, Worker)


class PropertyWrapper(unittest.TestCase):

    def test_property_wrapper(self):
        class C(object):

            @property
            def workername(self):
                return "name"
            define_old_worker_property(locals(), "workername")

        c = C()

        with assertNotProducesWarnings(DeprecatedWorkerAPIWarning):
            self.assertEqual(c.workername, "name")

        with assertProducesWarning(DeprecatedWorkerNameWarning):
            self.assertEqual(c.slavename, "name")


class MethodWrapper(unittest.TestCase):

    def test_method_wrapper(self):
        class C(object):

            def updateWorker(self, res):
                return res
            define_old_worker_method(locals(), updateWorker)

        c = C()

        with assertNotProducesWarnings(DeprecatedWorkerAPIWarning):
            self.assertEqual(c.updateWorker("test"), "test")

        with assertProducesWarning(DeprecatedWorkerNameWarning):
            self.assertEqual(c.updateSlave("test"), "test")

    def test_method_meta(self):
        class C(object):

            def updateWorker(self, res):
                """docstring"""
                return res
            define_old_worker_method(locals(), updateWorker)

        self.assertEqual(C.updateSlave.__module__, C.updateWorker.__module__)
        self.assertEqual(C.updateSlave.__doc__, C.updateWorker.__doc__)

    def test_method_mocking(self):
        class C(object):

            def updateWorker(self, res):
                return res
            define_old_worker_method(locals(), updateWorker)

        c = C()

        c.updateWorker = mock.Mock(return_value="mocked")

        with assertNotProducesWarnings(DeprecatedWorkerAPIWarning):
            self.assertEqual(c.updateWorker("test"), "mocked")

        with assertProducesWarning(DeprecatedWorkerNameWarning):
            self.assertEqual(c.updateSlave("test"), "mocked")


class FunctionWrapper(unittest.TestCase):

    def test_function_wrapper(self):
        def updateWorker(res):
            return res
        locals = {}
        define_old_worker_func(locals, updateWorker)

        self.assertIn("updateSlave", locals)

        with assertNotProducesWarnings(DeprecatedWorkerAPIWarning):
            self.assertEqual(updateWorker("test"), "test")

        with assertProducesWarning(DeprecatedWorkerNameWarning):
            self.assertEqual(locals["updateSlave"]("test"), "test")

    def test_func_meta(self):
        def updateWorker(self, res):
            """docstring"""
            return res
        locals = {}
        define_old_worker_func(locals, updateWorker)

        self.assertEqual(locals["updateSlave"].__module__,
                         updateWorker.__module__)
        self.assertEqual(locals["updateSlave"].__doc__,
                         updateWorker.__doc__)

    def test_module_reload(self):
        # pylint: disable=function-redefined
        locals = {}

        def updateWorker(res):
            return res

        define_old_worker_func(locals, updateWorker)

        self.assertIn("updateSlave", locals)

        # "Reload" module
        def updateWorker(res):
            return res

        define_old_worker_func(locals, updateWorker)

        self.assertIn("updateSlave", locals)


class AttributeMixin(unittest.TestCase):

    def test_attribute(self):
        class C(WorkerAPICompatMixin):

            def __init__(self):
                self.workers = [1, 2, 3]
                self._registerOldWorkerAttr("workers", name="buildslaves")

                self.workernames = ["a", "b", "c"]
                self._registerOldWorkerAttr("workernames")

        with assertNotProducesWarnings(DeprecatedWorkerAPIWarning):
            c = C()

            self.assertEqual(c.workers, [1, 2, 3])
            self.assertEqual(c.workernames, ["a", "b", "c"])

        with assertProducesWarning(DeprecatedWorkerNameWarning):
            self.assertEqual(c.buildslaves, [1, 2, 3])

        with assertProducesWarning(DeprecatedWorkerNameWarning):
            self.assertEqual(c.slavenames, ["a", "b", "c"])

    def test_attribute_setter(self):
        class C(WorkerAPICompatMixin):

            def __init__(self):
                self.workers = None
                self._registerOldWorkerAttr("workers", name="buildslaves")

                self.workernames = None
                self._registerOldWorkerAttr("workernames")

        with assertNotProducesWarnings(DeprecatedWorkerAPIWarning):
            c = C()

            c.workers = [1, 2, 3]
            c.workernames = ["a", "b", "c"]

        self.assertEqual(c.workers, [1, 2, 3])
        self.assertEqual(c.workernames, ["a", "b", "c"])

        with assertProducesWarning(DeprecatedWorkerNameWarning):
            c.buildslaves = [1, 2, 3]
        self.assertEqual(c.workers, [1, 2, 3])

        with assertProducesWarning(DeprecatedWorkerNameWarning):
            c.slavenames = ["a", "b", "c"]
        self.assertEqual(c.workernames, ["a", "b", "c"])

    def test_attribute_error(self):
        class C(WorkerAPICompatMixin):
            pass

        c = C()

        self.assertRaisesRegexp(
            AttributeError,
            "'C' object has no attribute 'abc'",
            lambda: c.abc)

    def test_static_attribute(self):
        class C(WorkerAPICompatMixin):
            value = 1

        c = C()

        self.assertEqual(c.value, 1)

    def test_properties(self):
        class C(WorkerAPICompatMixin):

            def __init__(self):
                self._value = 1

            @property
            def value(self):
                return self._value

            @value.setter
            def value(self, value):
                self._value = value

            @value.deleter
            def value(self):
                del self._value

        c = C()

        self.assertEqual(c._value, 1)
        self.assertEqual(c.value, 1)

        c.value = 2

        self.assertEqual(c._value, 2)
        self.assertEqual(c.value, 2)

        del c.value

        self.assertFalse(hasattr(c, "_value"))
        self.assertFalse(hasattr(c, "value"))
