import time
import queue
import sys
import importlib.util
import multiprocessing


class WorkerNode:
    """Background execution node that maintains safe, distinct state."""

    def __init__(self, task_queue, result_queue, db_config, registry):
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.db_config = db_config
        self.registry = registry

    def run(self):
        # 1. Load the Memory Manager from the registry
        spec = importlib.util.spec_from_file_location("local_mem", self.registry["SystemMemoryManager"])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        memory = mod.SystemMemoryManager(self.registry)

        try:
            # 2. Synchronize the Database Pool distinctly for this process
            db_pool = memory.get_persistent_resource("DatabaseConnectionPool", **self.db_config)
            # Signal the UI that the connection is active and warm
            self.result_queue.put({"task_id": 0, "status": "READY", "data": "IPC Handshake Successful"})
        except Exception as e:
            self.result_queue.put({"task_id": 0, "status": "FATAL", "data": str(e)});
            return

        while True:
            try:
                task = self.task_queue.get(timeout=0.5)
                if task == "SHUTDOWN": break

                tid, target, method, profile, args, kwargs = task

                # 3. Execute logic using lazy-loaded classes
                LogicClass = memory.load_class(target)

                # Check if logic requires the DB pool
                import inspect
                if 'pool' in inspect.signature(LogicClass.__init__).parameters:
                    instance = memory.safe_instantiate(LogicClass, pool=db_pool)
                else:
                    instance = memory.safe_instantiate(LogicClass)

                result = getattr(instance, method)(*args, **kwargs)
                self.result_queue.put({"task_id": tid, "status": "SUCCESS", "data": result})

            except queue.Empty:
                continue
            except Exception as e:
                self.result_queue.put({"task_id": tid, "status": "ERROR", "data": str(e)})


class ApplicationOrchestrator:
    def __init__(self, db_config, bootstrapper, registry, worker_count=2):
        self.task_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.workers = []
        self.task_counter = 0

        for _ in range(worker_count):
            p = multiprocessing.Process(target=bootstrapper,
                                        args=(self.task_queue, self.result_queue, db_config, registry))
            p.start()
            self.workers.append(p)

    def dispatch(self, target, method, profile, *args, **kwargs):
        self.task_counter += 1
        self.task_queue.put((self.task_counter, target, method, profile, args, kwargs))
        return self.task_counter

    def get_result(self, task_id, timeout=10.0):
        """Fetches results from the IPC queue with dynamic timeout handling."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                res = self.result_queue.get_nowait()
                if res["task_id"] == task_id or (task_id == 0 and res["status"] == "READY"):
                    return res
                self.result_queue.put(res)
            except queue.Empty:
                time.sleep(0.1)
        raise TimeoutError("IPC Context Limit Exceeded: Background worker failed to respond.")

    def shutdown(self):
        for _ in self.workers: self.task_queue.put("SHUTDOWN")
        for w in self.workers: w.join()

