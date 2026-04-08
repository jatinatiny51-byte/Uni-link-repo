import mysql.connector



class DatabaseConnectionPool:
    _instance = None  # Singleton instance tracker

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DatabaseConnectionPool, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_host="localhost", db_user="root", db_pass="sql2004", db_name="school_db"):
        if getattr(self, '_initialized', False):
            return

        self.config = {
            "host": db_host,
            "user": db_user,
            "password": db_pass,
            "database": db_name,
            "use_pure": True,
            # NEW: Cleans up the connection state automatically when returned to the pool
            "pool_reset_session": True,
            "autocommit": True
        }

        try:
            self._pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="edu_pool",
                pool_size=5,
                **self.config
            )
            self._initialized = True
        except mysql.connector.Error as e:
            raise Exception(f"Database Pool Failure: {e}")

    def get_connection(self):
        """Fetches a connection from the pool and ensures it is actively alive."""
        try:
            conn = self._pool.get_connection()
            # NEW: The Reconnect Guard. If MySQL killed the connection overnight, this revives it.
            if not conn.is_connected():
                conn.reconnect(attempts=2, delay=1)
            return conn
        except mysql.connector.Error as e:
            raise Exception(f"Connection Retrieval Failed: {e}")
