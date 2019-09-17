from queue import Queue, Empty
import time
import threading  # todo: prefer asyncio to threading!

from dysart.services.service import Service
from dysart.messages.errors import JobError


class Job:
    """
    a job to be run by the scheduler
    """

    def __init__(self, operation, callback):
        self.operation = operation
        self.callback = callback

    def run(self):
        self.operation()


class JobScheduler(Service):
    """
    A blocking JobScheduler class that does nothing on startup and stop,
    and simply executes the requested command and callback. Basically a no-op
    layer of indirection.
    """

    def __init__(self):
        super().__init__()
        self._is_running = False

    def is_running(self):
        return self._is_running

    def _start(self):
        self._is_running = True

    def _stop(self):
        self._is_running = False

    def put_job(self, job):
        """Puts a job into the (not really real) queue."""
        self.run_job(job)

    def run_job(self, job):
        """Runs a job. Does its operation, executes its callback."""
        job.operation()
        job.callback()


class AsyncJobScheduler(Queue, JobScheduler):
    """
    This is a future JobScheduler class that will probably use asyncio to
    dispatch jobs. It's not doing anything or really being used right now.
    """

    loop_rate = 1

    def __init__(self):
        super().__init__()
        self._is_running = False
        self.loop_thread = threading.Thread(target=self.loop)

    @property
    def jobs(self):
        return self.queue

    def get_job(self):
        """Selects the next job to be run"""
        new_job = self.get_nowait()
        return new_job

    def put_job(self, job):
        """Puts a job into the queue."""
        self.put(job)

    def run_job(self):
        """Fetch a job from the queue, run it and issue the callback."""
        try:
            job = self.get_job()
        except Empty as e:
            return
        # run the job
        try:
            job.run()
        except Exception:
            JobError()
        # issue callback
        job.callback()

    def loop(self):
        # TODO: should use a lock or condition rather than a bool.
        while self._is_running:
            with cv:
                while self.empty():
                    cv.wait()
            try:
                self.run_job()
            except Exception:
                raise JobError
            time.sleep(1 / self.loop_rate)

    def is_running(self):
        return self.loop_thread.is_alive()

    def _start(self):
        self._is_running = True
        self.loop_thread.start()

    def _stop(self):
        self._is_running = False
        self.loop_thread.stop()
        self.loop_thread.join()
        # make a new thread instance
        # self.loop_thread = threading.Thread(target=self.loop)


def make_test_job(i):
    def operation():
        print(f'I\'m done! ({i})')

    def callback():
        print('I\'m calling back!')
    return Job(operation, callback)


def make_test_scheduler():
    jobs = [make_test_job(i) for i in range(10)]
    sched = JobScheduler()
    for job in jobs:
        sched.put_job(job)
    return sched, jobs
