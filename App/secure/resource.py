import sys
import inspect
import importlib.util


class ResourceManager:
    """
    Manages distinct memory loading within a process.
    Prevents TypeErrors by dynamically filtering class signatures.
    """

    def __init__(self, registry):
        self.registry = registry
        self._instantiated_resources = {}

    def get_logic_class(self, class_name):
        """Lazy-loads a class from the dynamic registry map."""
        if class_name not in self.registry:
            raise ImportError(f"Memory Fault: {class_name} not found in System Registry.")

        module_name = f"mem_space_{class_name.lower()}"
        if module_name in sys.modules:
            return getattr(sys.modules[module_name], class_name)

        spec = importlib.util.spec_from_file_location(module_name, self.registry[class_name])
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return getattr(module, class_name)

    def safe_invoke(self, target_class, **kwargs):
        """
        Integrity Function: Prevents 'unexpected keyword' fatal errors.
        Filters inputs to match the constructor's DNA.
        """
        sig = inspect.signature(target_class.__init__)
        # Identify params the class actually accepts (excluding 'self' and generic kwargs)
        accepted = [p.name for p in sig.parameters.values() if p.name != 'self']

        # Filter the dictionary to ensure variables do not cause a fatal mismatch
        sanitized = {k: v for k, v in kwargs.items() if k in accepted}
        return target_class(**sanitized)

    def get_singleton(self, class_name, **config):
        """Maintains a persistent resource (like a DB Pool) within the process."""
        if class_name not in self._instantiated_resources:
            cls = self.get_logic_class(class_name)
            self._instantiated_resources[class_name] = self.safe_invoke(cls, **config)
        return self._instantiated_resources[class_name]

