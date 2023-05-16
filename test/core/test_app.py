import unittest

from core import app


class AppTest(unittest.TestCase):

    def test_performance_monitor(self):
        pm = app.PerformanceMonitor()
        with pm:
            pm('foo')

        with pm:
            pm('bar')

        data = str(pm).split('\n')
        self.assertIn('foo', data[0])
        self.assertIn('bar', data[1])
