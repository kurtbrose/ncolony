# Copyright (c) Moshe Zadka
# See LICENSE for details.
"""Tests for ncolony.reaperlib"""

## pylint: disable=redundant-unittest-assert

from cStringIO import StringIO
import signal
import sys
import unittest

from ncolony import reaperlib

class TestReap(unittest.TestCase):

    """Test process reaping"""

    def setUp(self):
        self.wait = None
        def _wait():
            return self.wait()
        self.reactor = reaperlib.SyncReactor(args=None, install=None,
                                             run=None, sleep=None, wait=_wait)

    def test_simple(self):
        """Test reaping our child"""
        waitCount = [0]
        def _wait():
            waitCount[0] += 1
            return 5, None
        self.wait = _wait
        reaperlib.reap(self.reactor, 5)
        self.assertEquals(waitCount[0], 1)

    def test_TwoIterations(self):
        """Test reaping adopted children"""
        pids = [6, 5]
        def _wait():
            return pids.pop(0), None
        self.wait = _wait
        reaperlib.reap(self.reactor, 5)
        self.assertEquals(pids, [])

class TestInstall(unittest.TestCase):

    """Test signal installation"""

    def test_installSignals(self):
        """Signal installation adds handlers for all signals

        Also, signal processor stops further processing"""
        handlers = {}
        def _install(signum, value):
            handlers[signum] = value
        reactor = reaperlib.SyncReactor(args=None, install=_install,
                                        run=None, sleep=None, wait=None)
        reaperlib.installSignals(reactor)
        self.assertEquals(set(handlers), set([signal.SIGTERM, signal.SIGINT, signal.SIGALRM]))
        self.assertEquals(len(set(handlers.itervalues())), 1)
        caller = next(handlers.itervalues())
        with self.assertRaises(SystemError):
            caller(12, None)
        self.assertEquals(len(set(handlers.itervalues())), 1)
        ignore = next(handlers.itervalues())
        self.assertEquals(ignore, signal.SIG_IGN)

class TestParser(unittest.TestCase):

    """Test reaperlib.PARSER"""

    def test_parser_fail_no_args(self):
        """Fail when there are no arguments"""
        with self.assertRaises(SystemExit):
            reaperlib.PARSER.parse_args([])

    def test_parser_success(self):
        """Return args which are given"""
        args = reaperlib.PARSER.parse_args(['a', 'b', 'c'])
        self.assertEquals(args.command, ['a', 'b', 'c'])

class DummyProcess(object):

    """Pretend to be a process"""

    pid = 124

    def poll(self):
        """Not done yet"""
        pass

    def kill(self):
        """That is not dead which can eternal lie"""
        pass

    def terminate(self):
        """And in strange aeons, even death may die"""
        pass

class TestBaseMain(unittest.TestCase):

    """Test abstract main"""

    def test_simple(self):
        """Happy path works"""
        handlers = {}
        def _install(signum, value):
            handlers[signum] = value
        args = []
        def _run(command):
            args[:] = command
            ret = DummyProcess()
            ret.poll = lambda: 0
            return ret
        waitCount = [0]
        def _wait():
            waitCount[0] += 1
            return DummyProcess.pid, None
        naps = []
        def _sleep(tm):
            naps.append(tm)
        reactor = reaperlib.SyncReactor(args=[None, 'ls'], install=_install,
                                        run=_run, sleep=_sleep, wait=_wait)
        reaperlib.baseMain(reactor)
        self.assertEquals(waitCount[0], 1)
        self.assertEquals(naps, [])
        self.assertEquals(set(handlers), set([signal.SIGTERM, signal.SIGINT, signal.SIGALRM]))
        self.assertEquals(args, ['ls'])

    def test_ctrl_c(self):
        """KeyboardInterrupt works"""
        handlers = {}
        def _install(signum, value):
            handlers[signum] = value
        def _run(dummyCommand):
            ret = DummyProcess()
            ret.poll = lambda: 0
            return ret
        def _wait():
            raise KeyboardInterrupt()
        def _sleep(dummyTm):
            pass
        reactor = reaperlib.SyncReactor(args=[None, 'ls'], install=_install,
                                        run=_run, sleep=_sleep, wait=_wait)
        reaperlib.baseMain(reactor)
        self.assertTrue(True)

    def test_system_error(self):
        """System error (generated by signals) works"""
        handlers = {}
        def _install(signum, value):
            handlers[signum] = value
        def _run(dummyCommand):
            ret = DummyProcess()
            ret.poll = lambda: 0
            return ret
        def _wait():
            raise SystemError()
        def _sleep(dummyTm):
            pass
        reactor = reaperlib.SyncReactor(args=[None, 'ls'], install=_install,
                                        run=_run, sleep=_sleep, wait=_wait)
        reaperlib.baseMain(reactor)
        self.assertTrue(True)

    def test_value_error(self):
        """Random errors generate a traceback"""
        handlers = {}
        def _install(signum, value):
            handlers[signum] = value
        def _run(dummyCommand):
            ret = DummyProcess()
            ret.poll = lambda: 0
            return ret
        def _wait():
            raise ValueError()
        def _sleep(dummyTm):
            pass
        reactor = reaperlib.SyncReactor(args=[None, 'ls'], install=_install,
                                        run=_run, sleep=_sleep, wait=_wait)
        oldStderr = sys.stderr
        def _cleanup():
            sys.stderr = oldStderr
        self.addCleanup(_cleanup)
        sys.stderr = StringIO()
        reaperlib.baseMain(reactor)
        ## pylint: disable=no-member
        lines = sys.stderr.getvalue().splitlines()
        ## pylint: enable=no-member
        _cleanup()
        dummyBaseMain, = (line for line in lines if line.endswith('in baseMain'))

    def test_termination(self):
        """Terminating processes when we go down"""
        handlers = {}
        def _install(signum, value):
            handlers[signum] = value
        def _wait():
            raise ValueError()
        sleeps = []
        def _sleep(tm):
            sleeps.append(tm)
        terminations = [0]
        killings = [0]
        polls = [None, None, 0, 0]
        def _run(dummyCommand):
            ret = DummyProcess()
            def _terminate():
                terminations[0] += 1
            def _kill():
                killings[0] += 1
            def _poll():
                return polls.pop(0)
            ret.terminate = _terminate
            ret.kill = _kill
            ret.poll = _poll
            return ret
        reactor = reaperlib.SyncReactor(args=[None, 'ls'], install=_install,
                                        run=_run, sleep=_sleep, wait=_wait)
        oldStderr = sys.stderr
        def _cleanup():
            sys.stderr = oldStderr
        self.addCleanup(_cleanup)
        sys.stderr = StringIO()
        reaperlib.baseMain(reactor)
        self.assertEquals(terminations[0], 1)
        self.assertEquals(killings[0], 0)
        self.assertEquals(sleeps, [1, 1])
        self.assertEquals(polls, [0])

    def test_killing(self):
        """Killing processes that don't die after 30 seconds"""
        handlers = {}
        def _install(signum, value):
            handlers[signum] = value
        def _wait():
            raise ValueError()
        sleeps = []
        def _sleep(tm):
            sleeps.append(tm)
        terminations = [0]
        killings = [0]
        def _run(dummyCommand):
            ret = DummyProcess()
            def _terminate():
                terminations[0] += 1
            def _kill():
                killings[0] += 1
            def _poll():
                return None
            ret.terminate = _terminate
            ret.kill = _kill
            ret.poll = _poll
            return ret
        reactor = reaperlib.SyncReactor(args=[None, 'ls'], install=_install,
                                        run=_run, sleep=_sleep, wait=_wait)
        oldStderr = sys.stderr
        def _cleanup():
            sys.stderr = oldStderr
        self.addCleanup(_cleanup)
        sys.stderr = StringIO()
        reaperlib.baseMain(reactor)
        self.assertEquals(terminations[0], 1)
        self.assertEquals(sleeps, [1]*30)
        self.assertEquals(killings[0], 1)

class TestMain(unittest.TestCase):

    """Test real main"""

    def test_main(self):
        """Main is composed of baseMain and the right SyncReactor"""
        self.assertIsInstance(reaperlib.main, reaperlib.functools.partial)
        self.assertIs(reaperlib.main.func, reaperlib.baseMain)
        self.assertFalse(reaperlib.main.keywords)
        reactor, = reaperlib.main.args
        self.assertIs(reactor.args, sys.argv)
        self.assertIs(reactor.install, signal.signal)
        self.assertIs(reactor.run, reaperlib.subprocess.Popen)
        self.assertIs(reactor.sleep, reaperlib.time.sleep)
        self.assertIs(reactor.wait, reaperlib.os.wait)
