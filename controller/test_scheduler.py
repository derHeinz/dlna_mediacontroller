from controller.scheduler import Scheduler
import unittest


class TestScheduler(unittest.TestCase):

    DEFAULT_NAME = 'asdf'
    DEFAULT_INTERVAL = 10

    def _testee(self) -> Scheduler:
        return Scheduler()

    def _noop(self):
        pass

    def test_start(self):
        s = self._testee()
        s.start()

        self.assertIsNotNone(s.scheduler)
        self.assertEqual(True, s.scheduler.running)

    def test_start_stop_different_jobs(self):
        s = self._testee()
        s.start()

        s.start_job(self.DEFAULT_NAME, self._noop, self.DEFAULT_INTERVAL)
        s.start_job('foo', self._noop, self.DEFAULT_INTERVAL)
        self.assertEqual(2, len(s.scheduler.get_jobs()))
        s.stop_job(self.DEFAULT_NAME)
        self.assertEqual(1, len(s.scheduler.get_jobs()))
        self.assertTrue(s.scheduler.get_jobs()[0].id.endswith('foo'))

    def test_stop_job_without_start_job(self):
        s = self._testee()
        s.start()

        self.assertEqual(0, len(s.scheduler.get_jobs()))  # no jobs
        s.stop_job(self.DEFAULT_NAME)
        self.assertEqual(0, len(s.scheduler.get_jobs()))  # no jobs

    def test_start_stop_jobs(self):
        s = self._testee()
        s.start()

        self.assertEqual(0, len(s.scheduler.get_jobs()))  # no jobs
        s.start_job(self.DEFAULT_NAME, self._noop, self.DEFAULT_INTERVAL)
        self.assertEqual(1, len(s.scheduler.get_jobs()))  # 1 job
        s.stop_job(self.DEFAULT_NAME)
        self.assertEqual(0, len(s.scheduler.get_jobs()))  # no jobs

    def test_start_job_immediate(self):
        s = self._testee()
        s.start()

        self.assertEqual(0, len(s.scheduler.get_jobs()))  # no jobs
        s.start_job(self.DEFAULT_NAME, self._noop, self.DEFAULT_INTERVAL, immediate=True)
        self.assertEqual(1, len(s.scheduler.get_jobs()))  # 1 job
