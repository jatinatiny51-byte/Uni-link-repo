import multiprocessing
import time
import queue
from datetime import datetime


class WorkerManager:
    def __init__(self, target_func):
        self.ctx = multiprocessing.get_context('spawn')
        self.task_q = self.ctx.Queue()
        self.result_q = self.ctx.Queue()
        self.target = target_func
        self.process = None
        self.status = "OFFLINE"

    def _spawn_worker(self):
        """Creates a fresh, isolated worker thread."""
        self.process = self.ctx.Process(
            target=self.target,
            args=(self.task_q, self.result_q)
        )
        self.process.daemon = True
        self.process.start()
        self.status = "IDLE"

    def start(self):
        if not self.process or not self.process.is_alive():
            self._spawn_worker()
            return "Supervisor: Worker Spawned."
        return "Supervisor: Worker already active."

    def submit_task(self, mod, cls, mthd, args, timeout=10):
        """Controlled execution with activity monitoring."""
        if self.status == "BUSY":
            return {"status": "ERROR", "data": "Worker Convoluted: Task already in progress."}

        self.status = "BUSY"
        self.task_q.put((mod, cls, mthd, args))

        try:
            # Managed wait for result
            result = self.result_q.get(timeout=timeout)
            self.status = "IDLE"
            return result
        except queue.Empty:
            self.status = "STALLED"
            self.maintenance()  # Attempt to reset a hung worker
            return {"status": "ERROR", "data": "Worker Stalled: Timeout reached."}

    def maintenance(self):
        """Cleans up hung or dead processes."""
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join()
        self._spawn_worker()

    def stop(self):
        self.task_q.put("EXIT")
        if self.process:
            self.process.join(timeout=2)
            self.status = "OFFLINE"
