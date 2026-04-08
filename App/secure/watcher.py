import os
import sys
import importlib.util


def dynamic_class_binder(class_name):
    project_root = os.path.dirname(os.path.abspath(__file__))
    for root, dirs, files in os.walk(project_root):
        if any(x in root for x in [".venv", "__pycache__", ".git", ".idea"]): continue
        for file in files:
            if file.endswith(".py") and file != os.path.basename(__file__):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        if f"class {class_name}" in f.read():
                            module_name = f"dynamic_{class_name.lower()}"
                            spec = importlib.util.spec_from_file_location(module_name, full_path)
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[module_name] = module
                            spec.loader.exec_module(module)
                            return getattr(module, class_name)
                except Exception:
                    continue
    raise ImportError(f"Logic '{class_name}' not found.")


class SecurityWatchdog:
    def __init__(self, query_executor):
        self.executor = query_executor

    def check_connection_health(self):
        """
        Actively ping the DB to catch closures or abrupt errors
        before starting a heavy transaction.
        """
        try:
            result = self.executor.execute_read(
                role="Teacher",
                table="teachers",
                query="SELECT 1 AS health_check"
            )
            return True if result else False
        except Exception:
            return False

    def sanitize_payload(self, raw_data):
        """
        Validates structure and enforces strict length boundaries
        to prevent buffer overflow, leaving SQL injection defense to the QueryExecutor.
        """
        if not isinstance(raw_data, dict):
            raise TypeError("Payload must be a dictionary.")

        sanitized = {}
        max_lengths = {
            "title": 150,
            "link_url": 255,
            "category": 50
        }

        for key, value in raw_data.items():
            if isinstance(value, str):
                clean_val = value.strip()
                limit = max_lengths.get(key, 500)

                if len(clean_val) > limit:
                    raise ValueError(f"Input for '{key}' exceeds maximum length of {limit} characters.")

                sanitized[key] = clean_val
            else:
                sanitized[key] = value

        return sanitized
