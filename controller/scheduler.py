import logging
import datetime

from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.blocking import BlockingScheduler, BaseScheduler
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__file__)


class Scheduler():

    scheduler: BaseScheduler = None

    def start(self, blocking=False):
        logger.debug("starting scheduler")
        if blocking:
            self.scheduler = BlockingScheduler()
        else:
            self.scheduler = BackgroundScheduler()

        self.scheduler.start()

    def start_job(self, name: str, process_to_run, seconds: int, immediate=False):
        logger.debug(f"starting job for {name} with ")
        trig = IntervalTrigger(seconds=seconds)
        if immediate:
            start_date = datetime.datetime.now() - datetime.timedelta(seconds=seconds) + datetime.timedelta(seconds=3)
            trig.start_date = start_date.astimezone()
        self.scheduler.add_job(id=name, name=name, func=process_to_run, trigger=trig)

    def stop_job(self, name: str):
        job = self.scheduler.get_job(name)
        if job is None:
            return
        logger.debug(f"stopping job for {name}")
        self.scheduler.remove_job(name)
