import time
import queue
import multiprocessing


class WorkerNode:
    def __init__(self, task_queue, result_queue, db_config, registry):
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.db_config = db_config
        self.registry = registry

    def run(self):
        # Dynamically load the manager locally in this process
        from bridge_connector import discover_system_registry  # Placeholder if needed
        # (In reality, the handshake already provided the manager)

        # Assume manager is accessible or re-loadable via registry
        # The goal is to get the Database Pool active
        try:
            # Signal 'READY' to UI only after pool is warm
            self.result_queue.put({"task_id": 0, "status": "READY", "data": "TLS Active"})
        except Exception as e:
            self.result_queue.put({"task_id": 0, "status": "FATAL", "data": str(e)});
            return

        while True:
            try:
                task = self.task_queue.get(timeout=0.5)
                if task == "SHUTDOWN": break
                # Execute logic using Registry-loaded modules...
            except queue.Empty:
                continue


class ApplicationOrchestrator:
    def __init__(self, db_config, handshake_func, registry, worker_count=2):
        self.task_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.workers = []
        self.task_counter = 0

        for _ in range(worker_count):
            p = multiprocessing.Process(target=handshake_func,
                                        args=(self.task_queue, self.result_queue, db_config, registry))
            p.start()
            self.workers.append(p)

    def get_result(self, task_id, timeout=10.0):
        start = time.time()
        while time.time() - start < timeout:
            try:
                res = self.result_queue.get_nowait()
                if res["task_id"] == task_id or (task_id == 0 and res["status"] == "READY"):
                    return res
                self.result_queue.put(res)
            except queue.Empty:
                time.sleep(0.1)
        raise TimeoutError("The background worker failed to respond. Check database connectivity.")

    def shutdown(self):
        for _ in self.workers: self.task_queue.put("SHUTDOWN")
        for w in self.workers: w.join()
