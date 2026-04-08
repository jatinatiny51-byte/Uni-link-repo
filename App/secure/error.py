import sys
import queue

# Graceful fallback in case the worker process fails to import MySQL
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False


class ErrorManager:
    """
    Centralized Error Handling Module.
    Catches, categorizes, and sanitizes all system faults.
    """

    @staticmethod
    def parse(error, context="System"):
        """Analyzes the exact error type and returns a safe, readable string."""
        err_type = type(error).__name__
        err_msg = str(error)

        # 1. SQL & DATA CONNECTION FAULTS
        if MYSQL_AVAILABLE and isinstance(error, mysql.connector.Error):
            if error.errno == 1045:
                return (False, "Database Guard: Access Denied. Check credentials (root/sql2004).")
            elif error.errno == 2003:
                return (False, "Database Guard: Cannot connect to MySQL Server. Is it running?")
            elif error.errno == 1054:
                return (False, f"Data Guard: Schema mismatch (Unknown Column). Detail: {err_msg}")
            else:
                return (False, f"SQL Fault [{error.errno}]: {err_msg}")

        # 2. SUB-PROCESS & THREADING FAULTS
        elif isinstance(error, queue.Empty):
            return (False, "Process Guard: Worker Timeout. The backend took too long to respond.")
        elif err_type in ["BrokenPipeError", "EOFError"]:
            return (False, "Process Guard: The background worker crashed or disconnected unexpectedly.")

        # 3. CRASH & MEMORY PROBLEMS
        elif isinstance(error, MemoryError):
            return (False, "Crash Guard: Critical memory limit reached. Halting task.")
        elif isinstance(error, KeyboardInterrupt):
            return (False, "System Guard: Manual interrupt (Ctrl+C) detected. Closing cleanly.")

        # 4. PAGE ISSUES & ROUTING (Action not found)
        elif isinstance(error, AttributeError):
            if "BusinessGatekeeper" in err_msg:
                return (False, "Route Guard: The requested feature or page does not exist in the Logic tier.")
            return (False, f"Module Error: {err_msg}")

        # 5. DATA & PROCESS LOGIC (Missing arguments, bad formatting)
        elif isinstance(error, TypeError) and "positional arguments" in err_msg:
            return (False, "Logic Guard: Invalid data submitted. System expected different parameters.")

        # FALLBACK: Catch-all for undefined errors
        return (False, f"Unhandled Exception in [{context}]: {err_type} - {err_msg}")

    @staticmethod
    def safe_execute(func, *args, **kwargs):
        """
        Universal wrapper. Wraps any function execution to ensure it never
        crashes the caller, always returning the standard (Boolean, Message) format.
        """
        try:
            result = func(*args, **kwargs)
            # Ensure the result is in the expected tuple format
            if isinstance(result, tuple) and len(result) == 2:
                return result
            return (True, result)
        except Exception as e:
            return ErrorManager.parse(e, context=func.__name__)
