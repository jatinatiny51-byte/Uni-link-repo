import multiprocessing
import queue

# Import your centralized error handler
from App.secure.error import ErrorManager


def worker_runtime(task_queue, result_queue):
    """The isolated background worker."""
    from pro_struct.gatekeeper import BusinessGatekeeper

    # Safely boot the logic tier
    try:
        gatekeeper = BusinessGatekeeper()
    except Exception as e:
        safe_error = ErrorManager.parse(e, context="Worker Boot")
        result_queue.put({"status": "ERROR", "data": safe_error})
        return

    while True:
        try:
            # 1. Fetch the task (This prevents the UnboundLocalError)
            task = task_queue.get(timeout=1)
            if task == "EXIT": break

            # 2. Define the action and arguments
            action, args = task

            # 3. Route the task through the Error Manager
            if hasattr(gatekeeper, action):
                logic_method = getattr(gatekeeper, action)

                # safe_execute catches all logic/SQL faults cleanly
                result = ErrorManager.safe_execute(logic_method, *args)
                result_queue.put({"status": "SUCCESS", "data": result})
            else:
                result = (False, f"Route Guard: Method '{action}' not found in Logic Tier.")
                result_queue.put({"status": "SUCCESS", "data": result})

        except queue.Empty:
            continue
        except KeyboardInterrupt:
            break
        except Exception as e:
            # Catches catastrophic process/OS level errors
            safe_error = ErrorManager.parse(e, context="Worker Queue")
            result_queue.put({"status": "ERROR", "data": safe_error})


class SecureEngine:
    def __init__(self):
        self.ctx = multiprocessing.get_context('spawn')
        self.task_queue = self.ctx.Queue()
        self.result_queue = self.ctx.Queue()
        self.process = None

    def start(self):
        if not self.process or not self.process.is_alive():
            self.process = self.ctx.Process(
                target=worker_runtime,
                args=(self.task_queue, self.result_queue)
            )
            self.process.daemon = True
            self.process.start()

    def execute(self, action, *args):
        self.task_queue.put((action, args))
        try:
            return self.result_queue.get(timeout=10)
        except queue.Empty:
            return {"status": "ERROR", "data": (False, "Process Guard: Worker Timeout.")}

    def stop(self):
        self.task_queue.put("EXIT")
        if self.process:
            self.process.join(timeout=2)
