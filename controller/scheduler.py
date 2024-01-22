import logging

from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.blocking import BlockingScheduler, BaseScheduler
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__file__)


class Scheduler():

    scheduler: BaseScheduler = None
    JOB_NAME = "Media Observer"

    def start(self, blocking=False):
        logger.debug("starting scheduler")
        if blocking:
            self.scheduler = BlockingScheduler()
        else:
            self.scheduler = BackgroundScheduler()

        self.scheduler.start()

    def start_job(self, process_to_run):
        logger.debug("starting observer job")
        trig = CronTrigger(second='*/10')  # (minute='*/1') # /5
        self.scheduler.add_job(id=self.JOB_NAME, func=process_to_run, trigger=trig)

    def stop_job(self):
        job = self.scheduler.get_job(self.JOB_NAME)
        if job is None:
            return
        logger.debug("stopping observer job")
        self.scheduler.remove_job(self.JOB_NAME)
