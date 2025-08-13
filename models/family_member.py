from datetime import datetime
from dbconnect.dbconn import db  # 导入数据库实例
from models.health_metric import HealthMetric
class FamilyMember:
    @staticmethod
    def get_basic_info(member_id):
        """获取成员基本信息（逻辑层）"""
        member = FamilyMember.get_by_id(member_id)
        if not member:
            return None

        # 不再需要 strptime 转换，因为 birth_date 已经是 date 对象
        birth_date = member['birth_date']
        today = datetime.now().date()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

        # 获取身高体重
        height = HealthMetric.get_latest_value(member_id, 'HEIGHT')
        weight = HealthMetric.get_latest_value(member_id, 'WEIGHT')

        return {
            "name": member['name'],
            "age": age,
            "height": height,
            "weight": weight,
            "relation": member['relation']
        }
    @staticmethod
    def get_with_metrics(member_id):
        """获取成员详情及健康指标"""
        member = FamilyMember.get_by_id(member_id)
        if not member:
            return None

        # 获取身高体重数据
        metrics = HealthMetric.get_by_member(member_id)

        # 添加到成员数据中
        for metric in metrics:
            if metric['metric_code'] == 'HEIGHT':
                member['height'] = metric['metric_value']
            elif metric['metric_code'] == 'WEIGHT':
                member['weight'] = metric['metric_value']
            elif metric['metric_code'] == 'BMI':
                member['bmi'] = metric['metric_value']

        return member
    @staticmethod
    def get_all():
        """获取所有家庭成员"""
        return db.query(
            "SELECT * FROM family_member WHERE is_deleted = 0 ORDER BY create_time DESC"
        )

    @staticmethod
    def get_by_id(member_id):
        """根据ID获取成员详情"""
        result = db.query(
            "SELECT * FROM family_member WHERE member_id = %s AND is_deleted = 0",
            (member_id,)
        )
        return result[0] if result else None

    @staticmethod
    def create(member_data):
        """创建新成员"""
        sql = """
              INSERT INTO family_member
                  (family_id, name, avatar, gender, birth_date, relation, is_primary)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        params = (
            member_data['family_id'],
            member_data['name'],
            member_data.get('avatar'),
            member_data['gender'],
            member_data['birth_date'],
            member_data['relation'],
            member_data.get('is_primary', 0)
        )
        db.query(sql, params)
        return db.query("SELECT LAST_INSERT_ID()")[0]['LAST_INSERT_ID()']

    @staticmethod
    def update(member_id, update_data):
        """更新成员信息"""
        fields = []
        params = []
        for field, value in update_data.items():
            fields.append(f"{field} = %s")
            params.append(value)
        params.append(member_id)

        sql = f"UPDATE family_member SET {', '.join(fields)} WHERE member_id = %s"
        return db.query(sql, params)

    @staticmethod
    def delete(member_id):
        """软删除成员"""
        return db.query(
            "UPDATE family_member SET is_deleted = 1 WHERE member_id = %s",
            (member_id,)
        )

    @staticmethod
    def search(keyword):
        """搜索成员"""
        return db.query(
            "SELECT * FROM family_member WHERE name LIKE %s AND is_deleted = 0",
            (f"%{keyword}%",)
        )