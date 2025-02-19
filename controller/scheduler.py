import logging

from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.blocking import BlockingScheduler, BaseScheduler
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__file__)


class Scheduler():

    scheduler: BaseScheduler = None
    JOB_NAME_PREFIX = "Media_Observer_"


    def start(self, blocking=False):
        logger.debug("starting scheduler")
        if blocking:
            self.scheduler = BlockingScheduler()
        else:
            self.scheduler = BackgroundScheduler()

        self.scheduler.start()

    def _job_name(self, name: str):
        return self.JOB_NAME_PREFIX + name

    def start_job(self, name: str, process_to_run):
        logger.debug(f"starting observer job for {name}")
        trig = CronTrigger(second='*/10')
        self.scheduler.add_job(id=self._job_name(name), name=self._job_name(name), func=process_to_run, trigger=trig)

    def stop_job(self, name: str):
        job = self.scheduler.get_job(self._job_name(name))
        if job is None:
            return
        logger.debug(f"stopping observer job for {name}")
        self.scheduler.remove_job(self._job_name(name))
