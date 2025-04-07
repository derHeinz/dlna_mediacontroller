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

    def start_job(self, name: str, process_to_run, seconds: int):
        logger.debug(f"starting job for {name} with ")
        trig = CronTrigger(second=('*/' + str(seconds)))
        self.scheduler.add_job(id=name, name=name, func=process_to_run, trigger=trig)

    def stop_job(self, name: str):
        job = self.scheduler.get_job(name)
        if job is None:
            return
        logger.debug(f"stopping job for {name}")
        self.scheduler.remove_job(name)
