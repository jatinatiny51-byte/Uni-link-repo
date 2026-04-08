import os
import sys
import re
import time
import inspect
import importlib.util
import multiprocessing


# ==========================================
# 1. DYNAMIC SYSTEM DISCOVERY (No Hardcoded Paths)
# ==========================================
def discover_project_registry():
    """
    Scans the entire project directory tree starting from the script's location.
    Maps every class name found in any .py file to its absolute disk path.
    """
    registry = {}
    # Dynamically determine the root based on this file's location
    root_dir = os.path.dirname(os.path.abspath(__file__))

    for root, _, files in os.walk(root_dir):
        # Skip environment and system folders
        if any(x in root for x in [".venv", "__pycache__", ".git", ".idea"]):
            continue
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8') as src:
                        # Find all class definitions in the file
                        found_classes = re.findall(r'^class\s+([A-Za-z0-9_]+)', src.read(), re.MULTILINE)
                        for c in found_classes:
                            registry[c] = path
                except:
                    continue
    return registry


def dynamic_loader(class_name, registry):
    """Instantly loads a class from disk using the absolute path in the registry."""
    if class_name not in registry:
        raise ImportError(f"CRITICAL: Component '{class_name}' was not discovered in the project.")

    # Check if already loaded in the current process memory
    module_name = f"active_module_{class_name.lower()}"
    if module_name in sys.modules:
        return getattr(sys.modules[module_name], class_name)

    spec = importlib.util.spec_from_file_location(module_name, registry[class_name])
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)


# ==========================================
# 2. INPUT TRANSFER & INTEGRITY GUARD
# ==========================================
def adaptive_invoker(target_class, **kwargs):
    """
    Solves the 'Unexpected Keyword' TypeError.
    Inspects the target class's signature and only passes the data it can handle.
    """
    try:
        sig = inspect.signature(target_class.__init__)
        # Identify which arguments the class actually wants
        allowed = [p.name for p in sig.parameters.values() if p.name != 'self']
        # Filter the input dictionary to match the class's 'DNA'
        sanitized_args = {k: v for k, v in kwargs.items() if k in allowed}
        return target_class(**sanitized_args)
    except:
        return target_class()


# ==========================================
# 3. THE WORKER BOOTSTRAPPER (IPC)
# ==========================================
def worker_handshake(task_queue, result_queue, db_config, registry):
    """
    This function runs inside the new background process.
    It inherits the registry and establishes the connection line.
    """
    # Load required backend modules via the registry
    WorkerNode = dynamic_loader("WorkerNode", registry)
    PoolClass = dynamic_loader("DatabaseConnectionPool", registry)

    # Sanitize the db_config for this specific Pool version
    safe_config = adaptive_invoker(PoolClass, **db_config)

    # Initialize the worker process
    # Note: WorkerNode logic should be set to use the provided registry internally
    worker = WorkerNode(task_queue, result_queue, db_config, registry)
    worker.run()


class SystemBridge:
    """
    The UI's single point of contact.
    Handles the dispatch of tasks to the multi-process orchestrator.
    """

    def __init__(self, orchestrator, registry):
        self.orchestrator = orchestrator
        self.registry = registry

    def request_action(self, module_name, method_name, profile=None, *args, **kwargs):
        """Dispatches a UI input to the background logic nodes."""
        if profile is None:
            profile = {"timeout": 10.0}  # Default dynamic leash

        task_id = self.orchestrator.dispatch(module_name, method_name, profile, *args, **kwargs)
        return self.orchestrator.get_result(task_id, timeout=profile["timeout"])

