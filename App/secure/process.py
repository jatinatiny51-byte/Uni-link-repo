
import time
import queue
import sys
import importlib.util
import multiprocessing


def load_from_registry(class_name, registry):
    """Loads a module dynamically using the central registry map."""
    if class_name not in registry:
        raise ImportError(f"CRITICAL: '{class_name}' not found in System Registry.")

    module_name = f"dynamic_{class_name.lower()}"
    if module_name in sys.modules:
        return getattr(sys.modules[module_name], class_name)

    full_path = registry[class_name]
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)


class WorkerNode:
    """A background process that uses the ErrorGuard to safely load dependencies."""

    def __init__(self, task_queue, result_queue, db_config, system_registry):
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.db_config = db_config
        self.registry = system_registry
        self._module_cache = {}
        self.db_pool = None

        # Load the Error Handler immediately
        self.ErrorHandler = load_from_registry("SystemErrorHandler", self.registry)

    def _get_module(self, class_name, dynamic_cache_limit):
        current_time = time.time()

        # Guard the registry load
        self.ErrorHandler.validate_registry_load(class_name, self.registry)

        if class_name in self._module_cache:
            self._module_cache[class_name] = (self._module_cache[class_name][0], current_time)
            return self._module_cache[class_name][0]

        loaded_class = load_from_registry(class_name, self.registry)

        while len(self._module_cache) >= dynamic_cache_limit:
            oldest_key = min(self._module_cache.keys(), key=lambda k: self._module_cache[k][1])
            del self._module_cache[oldest_key]

        self._module_cache[class_name] = (loaded_class, current_time)
        return loaded_class

    def run(self):
        try:
            PoolClass = load_from_registry("DatabaseConnectionPool", self.registry)

            # --- THE FIX: Safe Instantiation ---
            # The Guard strips out 'ca_cert_path' if the DB pool doesn't ask for it
            self.db_pool = self.ErrorHandler.safe_instantiate(PoolClass, **self.db_config)

        except Exception:
            error_payload = self.ErrorHandler.format_ipc_error()
            self.result_queue.put({"task_id": -1, "status": "FATAL", "data": error_payload["data"]})
            return  # Kill the worker if it can't connect to the DB

        while True:
            try:
                task = self.task_queue.get(timeout=0.5)
                if task == "SHUTDOWN":
                    if self.db_pool: self.db_pool.shutdown()
                    break

                task_id, target_class, method_name, profile, args, kwargs = task
                cache_limit = profile.get("cache_size", 3)

                LogicClass = self._get_module(target_class, cache_limit)

                # --- THE FIX: Safe Instantiation for Logic Modules ---
                if hasattr(LogicClass, '__init__') and 'pool' in LogicClass.__init__.__code__.co_varnames:
                    instance = self.ErrorHandler.safe_instantiate(LogicClass, pool=self.db_pool)
                else:
                    instance = self.ErrorHandler.safe_instantiate(LogicClass)

                method = getattr(instance, method_name)
                result = method(*args, **kwargs)

                self.result_queue.put({"task_id": task_id, "status": "SUCCESS", "data": result})

            except queue.Empty:
                continue
            except Exception:
                # The Guard intercepts the crash and formats it cleanly for the UI
                error_payload = self.ErrorHandler.format_ipc_error()
                self.result_queue.put({"task_id": task_id, "status": "ERROR", "data": error_payload["data"]})


class ApplicationOrchestrator:
    def __init__(self, db_config, worker_target, system_registry, worker_count=4):
        self.task_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.workers = []
        self.task_counter = 0
        self.active_timeouts = {}

        for _ in range(worker_count):
            w = multiprocessing.Process(
                target=worker_target,
                args=(self.task_queue, self.result_queue, db_config, system_registry)
            )
            w.start()
            self.workers.append(w)

    def dispatch_task(self, target_class, method_name, task_profile=None, *args, **kwargs):
        if task_profile is None:
            task_profile = {"timeout": 5.0, "cache_size": 3}

        self.task_counter += 1
        task_id = self.task_counter
        self.active_timeouts[task_id] = task_profile.get("timeout", 5.0)

        self.task_queue.put((task_id, target_class, method_name, task_profile, args, kwargs))
        return task_id

    def fetch_result(self, task_id):
        timeout_limit = self.active_timeouts.get(task_id, 5.0)
        start_time = time.time()

        while time.time() - start_time < timeout_limit:
            try:
                result = self.result_queue.get_nowait()
                if result["task_id"] == task_id:
                    del self.active_timeouts[task_id]
                    if result["status"] == "ERROR" or result["status"] == "FATAL":
                        raise Exception(result["data"])
                    return result["data"]
                else:
                    self.result_queue.put(result)
            except queue.Empty:
                time.sleep(0.05)

        if task_id in self.active_timeouts:
            del self.active_timeouts[task_id]
        raise TimeoutError(f"Task {task_id} exceeded its context limit of {timeout_limit} seconds.")

    def shutdown(self):
        for _ in self.workers:
            self.task_queue.put("SHUTDOWN")
        for w in self.workers:
            w.join()
