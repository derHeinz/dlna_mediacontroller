from controller.scheduler import Scheduler
import unittest
from unittest.mock import patch, call


class TestIntegrator(unittest.TestCase):

    def _testee(self):
        return Scheduler()
    
    def _noop(self):
        pass

    def test_start(self):
        s = self._testee()
        s.start()

        self.assertIsNotNone(s.scheduler)
        self.assertEqual(True, s.scheduler.running)

    def test_stop_job_without_start_job(self):
        s = self._testee()
        s.start()

        self.assertEqual(0, len(s.scheduler.get_jobs()))  # no jobs
        s.stop_job()
        self.assertEqual(0, len(s.scheduler.get_jobs()))  # no jobs

    def test_start_stop_jobs(self):
        s = self._testee()
        s.start()

        self.assertEqual(0, len(s.scheduler.get_jobs()))  # no jobs
        s.start_job(self._noop)
        self.assertEqual(1, len(s.scheduler.get_jobs()))  # 1 job
        s.stop_job()
        self.assertEqual(0, len(s.scheduler.get_jobs()))  # no jobs
