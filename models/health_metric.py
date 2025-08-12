from datetime import datetime
from dbconnect.dbconn import db

class HealthMetric:

    @staticmethod
    def get_latest_metrics(member_id):
        """获取各项指标最新值（逻辑层）"""
        # 获取所有指标类型
        metric_types = db.query("""
                                SELECT metric_id, metric_code
                                FROM health_metric_type
                                WHERE is_system = 1
                                """)

        latest_metrics = {}
        for mt in metric_types:
            metric = db.query("""
                              SELECT m.*, t.metric_name, t.unit
                              FROM member_health_metric m
                                       JOIN health_metric_type t ON m.metric_id = t.metric_id
                              WHERE m.member_id = %s
                                AND m.metric_id = %s
                              ORDER BY m.measure_time DESC LIMIT 1
                              """, (member_id, mt['metric_id']))

            if metric:
                latest_metrics[mt['metric_code']] = metric[0]

        return latest_metrics
    @staticmethod
    def get_all_metrics(member_id):
        """获取所有健康指标（逻辑层）"""
        return db.query("""
                        SELECT t.metric_name,
                               m.metric_value,
                               t.unit,
                               m.measure_time,
                               t.normal_range,
                               m.status
                        FROM member_health_metric m
                                 JOIN health_metric_type t ON m.metric_id = t.metric_id
                        WHERE m.member_id = %s
                        ORDER BY m.measure_time DESC
                        """, (member_id,))

    @staticmethod
    def get_nutrition_data(member_id):
        """获取营养数据（逻辑层）"""
        # 获取近7天营养数据平均值
        result = db.query("""
                          SELECT t.metric_name                                     AS label,
                                 ROUND(AVG(m.metric_value))                        AS current_value,
                                 t.normal_range                                    AS target_value,
                                 t.unit,
                                 ROUND(AVG(m.metric_value) / t.normal_range * 100) AS percent
                          FROM member_health_metric m
                                   JOIN health_metric_type t ON m.metric_id = t.metric_id
                          WHERE m.member_id = %s
                            AND t.metric_code IN ('ENERGY', 'PROTEIN', 'CALCIUM', 'IRON', 'ZINC', 'SODIUM')
                            AND m.measure_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                          GROUP BY t.metric_id
                          """, (member_id,))

        return [{
            "label": row['label'],
            "current": row['current_value'],
            "target": row['target_value'],
            "unit": row['unit'],
            "percent": f"{row['percent']}%"
        } for row in result] if result else []
    @staticmethod
    def get_latest_value(member_id, metric_code):
        """获取最新指标值"""
        result = db.query("""
                          SELECT m.metric_value
                          FROM member_health_metric m
                                   JOIN health_metric_type t ON m.metric_id = t.metric_id
                          WHERE m.member_id = %s
                            AND t.metric_code = %s
                          ORDER BY m.measure_time DESC LIMIT 1
                          """, (member_id, metric_code))
        return result[0]['metric_value'] if result else None

    @staticmethod
    def get_health_status(member_id):
        """获取健康状态（逻辑层）"""
        # 获取关键指标
        bmi = HealthMetric.get_latest_value(member_id, 'BMI')
        calcium = HealthMetric.get_latest_value(member_id, 'CALCIUM')
        sodium = HealthMetric.get_latest_value(member_id, 'SODIUM')

        return {
            "bmi": bmi,
            "calcium": calcium,
            "sodium": sodium
        }
    @staticmethod
    def get_by_member(member_id):
        """获取成员所有健康指标"""
        return db.query("""
            SELECT m.*, t.metric_name, t.unit, t.normal_range
            FROM member_health_metric m
            JOIN health_metric_type t ON m.metric_id = t.metric_id
            WHERE m.member_id = %s
            ORDER BY m.measure_time DESC
        """, (member_id,))

    @staticmethod
    def create(member_id, metric_data):
        """添加健康指标记录"""
        sql = """
        INSERT INTO member_health_metric
        (member_id, metric_id, metric_value, measure_time, data_source, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (
            member_id,
            metric_data['metric_id'],
            metric_data['metric_value'],
            metric_data.get('measure_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            metric_data.get('data_source', 'MANUAL'),
            metric_data.get('status')
        )
        db.query(sql, params)
        return db.query("SELECT LAST_INSERT_ID()")[0]['LAST_INSERT_ID()']

    @staticmethod
    def get_latest(member_id, metric_code):
        """获取成员特定指标的最新记录"""
        result = db.query("""
            SELECT m.* FROM member_health_metric m
            JOIN health_metric_type t ON m.metric_id = t.metric_id
            WHERE m.member_id = %s AND t.metric_code = %s
            ORDER BY m.measure_time DESC LIMIT 1
        """, (member_id, metric_code))
        return result[0] if result else None