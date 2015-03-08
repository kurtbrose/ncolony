# Copyright (c) Moshe Zadka
# See LICENSE for details.
"""Test event processing"""
import json
import unittest

from zope.interface import verify

from twisted.python import log

from ncolony import process_events
from ncolony import interfaces

class DummyProcessMonitor(object):

    """Something that looks like a process monitor"""

    def __init__(self):
        """Initialize to record which events we got"""
        self.events = []

    # pylint: disable=too-many-arguments
    def addProcess(self, name, args, uid=None, gid=None, env=None):
        """Add a process

        TODO: document arguments
        """
        if env is None:
            env = {}
        self.events.append(('ADD', name, args, uid, gid, env))
    # pylint: enable=too-many-arguments

    def removeProcess(self, name):
        """Remove a process

        TODO: document arguments
        """
        self.events.append(('REMOVE', name))

    def stopProcess(self, name):
        """Stop (really, restart) a process.

        TODO: document arguments
        """
        self.events.append(('RESTART', name))

    def restartAll(self):
        """Restart all processes
        """
        self.events.append(('RESTART-ALL',))

class TestReceiver(unittest.TestCase):

    """Test the event receiver"""

    def setUp(self):
        """Initialize the test"""
        self.monitor = DummyProcessMonitor()
        self.receiver = process_events.Receiver(self.monitor)
        self.assertFalse(self.monitor.events)
        self.logMessages = []
        def _observer(msg):
            self.logMessages.append(''.join(msg['message']))
        self.addCleanup(log.removeObserver, _observer)
        log.addObserver(_observer)
        self.assertFalse(self.logMessages)

    def test_recorder_is_good(self):
        """Test that the recorder implements the right interface"""
        self.assertTrue(verify.verifyObject(interfaces.IMonitorEventReceiver, self.receiver))

    def test_add_simple(self):
        """Test a simple process addition"""
        message = json.dumps(dict(args=['/bin/echo', 'hello']))
        self.receiver.add('hello', message)
        self.assertEquals(self.monitor.events,
                          [('ADD', 'hello', ['/bin/echo', 'hello'], None, None, {})])
        self.assertEquals(self.logMessages, ['Added monitored process: hello'])

    def test_add_complicated(self):
        """Test a process addition with all the optional arguments"""
        message = json.dumps(dict(args=['/bin/echo', 'hello'], uid=0, gid=0, env={'world': '616'}))
        self.receiver.add('hello', message)
        self.assertEquals(self.monitor.events,
                          [('ADD', 'hello', ['/bin/echo', 'hello'], 0, 0, {'world': '616'})])
        self.assertEquals(self.logMessages, ['Added monitored process: hello'])

    def test_add_with_junk(self):
        """Test a process addition with all the optional arguments"""
        message = json.dumps(dict(something=1, args=['/bin/echo', 'hello']))
        self.receiver.add('hello', message)
        self.assertEquals(self.monitor.events,
                          [('ADD', 'hello', ['/bin/echo', 'hello'], None, None, {})])
        self.assertEquals(self.logMessages, ['Added monitored process: hello'])

    def test_remove(self):
        """Test a process removal"""
        self.receiver.remove('hello')
        self.assertEquals(self.monitor.events,
                          [('REMOVE', 'hello')])
        self.assertEquals(self.logMessages, ['Removed monitored process: hello'])

    def test_restart(self):
        """Test a process restart"""
        message = json.dumps(dict(type='RESTART', name='hello'))
        self.receiver.message(message)
        self.assertEquals(self.monitor.events,
                          [('RESTART', 'hello')])
        self.assertEquals(self.logMessages, ['Restarting monitored process: hello'])

    def test_unknown_message(self):
        """Test that we reject unknown messages"""
        message = json.dumps(dict(type='LALALA', name='goodbye'))
        with self.assertRaises(ValueError):
            self.receiver.message(message)

    def test_restart_all(self):
        """Test a global restart"""
        message = json.dumps(dict(type='RESTART-ALL'))
        self.receiver.message(message)
        self.assertEquals(self.monitor.events,
                          [('RESTART-ALL',)])
        self.assertEquals(self.logMessages, ['Restarting all monitored processes'])