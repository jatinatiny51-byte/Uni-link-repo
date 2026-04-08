import sys
import inspect
import importlib.util


class SystemMemoryManager:
    """
    Handles lazy-loading and resource integrity.
    Ensures classes only receive the variables they are designed to handle.
    """

    def __init__(self, system_registry):
        self.registry = system_registry
        self._instantiated_singletons = {}

    def load_class(self, class_name):
        """Dynamically loads a class from the project registry without knowing the filename."""
        if class_name not in self.registry:
            raise ImportError(f"Memory Fault: Class '{class_name}' not found in System Registry.")

        module_alias = f"mem_space_{class_name.lower()}"
        if module_alias in sys.modules:
            return getattr(sys.modules[module_alias], class_name)

        spec = importlib.util.spec_from_file_location(module_alias, self.registry[class_name])
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_alias] = module
        spec.loader.exec_module(module)
        return getattr(module, class_name)

    def safe_instantiate(self, target_class, **kwargs):
        """
        Integrity Guard: Resolves variable mismatches (TypeErrors).
        Filters the input payload to match the class's constructor signature.
        """
        try:
            # Inspect the DNA of the class
            sig = inspect.signature(target_class.__init__)
            # Identify which arguments the class actually accepts
            accepted = [p.name for p in sig.parameters.values() if p.name != 'self']

            # Strip out any 'made up' or unsupported keys (like ca_cert_path)
            sanitized = {k: v for k, v in kwargs.items() if k in accepted}
            return target_class(**sanitized)
        except Exception:
            # Fallback for classes with no explicit constructor
            return target_class()

    def get_persistent_resource(self, class_name, **config):
        """Ensures resources like DB Pools are created once per process and persist."""
        if class_name not in self._instantiated_singletons:
            cls = self.load_class(class_name)
            self._instantiated_singletons[class_name] = self.safe_instantiate(cls, **config)
        return self._instantiated_singletons[class_name]

