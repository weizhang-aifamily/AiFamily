from dbconnect.dbconn import db


class DietRecord:
    @staticmethod
    def get_food_ranking(member_id, days=7, limit=3):
        """获取饮食排名数据（逻辑层）"""
        result = db.query("""
                          SELECT f.food_name AS name,
                                 COUNT(*) AS count,
                GROUP_CONCAT(DISTINCT ft.tag_name SEPARATOR '|') AS tags
                          FROM member_food_log mfl
                              JOIN foods f
                          ON mfl.food_id = f.food_id
                              LEFT JOIN food_tags ft ON f.food_id = ft.food_id
                          WHERE mfl.member_id = %s
                            AND mfl.consumed_at >= DATE_SUB(NOW()
                              , INTERVAL %s DAY)
                          GROUP BY f.food_id
                          ORDER BY count DESC
                              LIMIT %s
                          """, (member_id, days, limit))

        return [{
            "name": row['name'],
            "count": row['count'],
            "tags": row['tags'].split('|') if row['tags'] else []
        } for row in result] if result else []