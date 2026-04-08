import time
from mysql.connector import Error


class QueryExecutor:
    def __init__(self, pool_manager, validator):
        self.pool_manager = pool_manager
        self.validator = validator

    def execute_read(self, role, table, query, params=()):
        if not self.validator.can_access(role, table, "SELECT"):
            raise PermissionError(f"Access Denied: Role '{role}' cannot SELECT from '{table}'.")

        params = self.validator.sanitize_input(params)
        retries = 3

        for attempt in range(retries):
            conn = None
            cursor = None
            try:
                conn = self.pool_manager.get_connection()
                if not conn.is_connected():
                    conn.ping(reconnect=True, attempts=3, delay=2)

                # The stale data killer (flushes the snapshot)
                conn.commit()

                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params)
                result = cursor.fetchall()

                return result

            except Error:
                if attempt == retries - 1:
                    raise
                time.sleep(1)

            finally:
                # CONTEXTUAL FIX: Safely returns the connection to the pool unconditionally
                if cursor:
                    cursor.close()
                if conn and conn.is_connected():
                    conn.close()

    def execute_write(self, role, table, action, query, params=()):
        if not self.validator.can_access(role, table, action):
            raise PermissionError(f"Access Denied: Role '{role}' cannot {action} in '{table}'.")

        params = self.validator.sanitize_input(params)
        retries = 3

        for attempt in range(retries):
            conn = None
            cursor = None
            try:
                conn = self.pool_manager.get_connection()
                if not conn.is_connected():
                    conn.ping(reconnect=True, attempts=3, delay=2)

                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                affected_rows = cursor.rowcount

                return affected_rows

            except Error:
                if attempt == retries - 1:
                    raise
                time.sleep(1)

            finally:
                # CONTEXTUAL FIX: Safely returns the connection to the pool unconditionally
                if cursor:
                    cursor.close()
                if conn and conn.is_connected():
                    conn.close()
