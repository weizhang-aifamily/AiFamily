import pymysql
from pymysql.cursors import DictCursor

class Database:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'Dd2009zw#',
            'database': 'ejiacan',
            'cursorclass': DictCursor
        }

    def get_connection(self):
        return pymysql.connect(**self.config)

    def query(self, sql, params=None):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                return cur.fetchall()

    def execute(self, sql, params=None):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                conn.commit()
                return cur.rowcount

# 创建全局实例
db = Database()