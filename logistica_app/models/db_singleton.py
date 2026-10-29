import psycopg2
import threading
from django.conf import settings

class DatabaseSingleton:
    _instance = None
    _lock = threading.Lock()
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseSingleton, cls).__new__(cls)
        return cls._instance

    def get_connection(self):
        with self._lock:
            if self._connection is None or self._connection.closed != 0:
                db_config = settings.DATABASES['default']
                self._connection = psycopg2.connect(
                    dbname=db_config['NAME'],
                    user=db_config['USER'],
                    password=db_config['PASSWORD'],
                    host=db_config['HOST'],
                    port=db_config['PORT']
                )
            return self._connection

    def execute(self, query, params=None, fetch=False):
        conn = self.get_connection()
        with conn.cursor() as cursor:
            try:
                cursor.execute(query, params or ())
                if fetch:
                    columns = [col[0] for col in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                conn.commit()
                return None
            except Exception as e:
                conn.rollback()
                raise e