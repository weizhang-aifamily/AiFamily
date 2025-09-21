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

    def executemany(self, sql, seq_of_params):
        """
        批量执行同一条 SQL 语句
        :param sql:               带占位符的 SQL 模板
        :param seq_of_params:     序列，每个元素为一条参数元组/列表/字典
        :return:                  累计影响的行数
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(sql, seq_of_params)
                conn.commit()
                return cur.rowcount

# 创建全局实例
db = Database()