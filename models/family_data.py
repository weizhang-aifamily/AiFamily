# family_data.py
from typing import Dict, Any, Optional, List
from dbconnect.dbconn import db

class FamilyData:

    @staticmethod
    def insert_family_member(member_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        插入新的家庭成员
        """
        sql = """
            INSERT INTO ejia_user_family_member (
                id, name, gender, age, age_group, height_cm, weight_kg,
                exerciseFrequency, exerciseDuration, exerciseIntensity
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        params = (
            member_data['member_id'],
            member_data['name'],
            member_data['gender'],
            member_data['age'],
            member_data['ageGroup'],
            member_data['height_cm'],
            member_data['weight_kg'],
            member_data['exerciseFrequency'],
            member_data['exerciseDuration'],
            member_data['exerciseIntensity']
        )

        result = db.execute(sql, params)

        return {
            'success': True,
            'message': '家庭成员添加成功',
            'member_id': member_data['member_id'],
            'affected_rows': result
        }

    @staticmethod
    def update_family_member(member_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新现有家庭成员信息
        """
        sql = """
            UPDATE ejia_user_family_member 
            SET name = %s,
                gender = %s,
                age = %s,
                age_group = %s,
                height_cm = %s,
                weight_kg = %s,
                exerciseFrequency = %s,
                exerciseDuration = %s,
                exerciseIntensity = %s,
                pal = NULL  -- 根据业务逻辑可能需要重新计算
            WHERE id = %s
        """

        params = (
            member_data['name'],
            member_data['gender'],
            member_data['age'],
            member_data['ageGroup'],
            member_data['height_cm'],
            member_data['weight_kg'],
            member_data['exerciseFrequency'],
            member_data['exerciseDuration'],
            member_data['exerciseIntensity'],
            member_data['member_id']
        )

        result = db.execute(sql, params)

        return {
            'success': True,
            'message': '家庭成员信息更新成功',
            'member_id': member_data['member_id'],
            'affected_rows': result
        }

    @staticmethod
    def update_family_members_batch(members_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量更新多个家庭成员信息
        """
        try:
            if not members_data:
                return {
                    'success': True,
                    'message': '没有需要更新的成员数据',
                    'total_affected': 0,
                    'details': []
                }

            # 构建批量更新的SQL
            sql = """
                UPDATE ejia_user_family_member 
                SET name = %s,
                    gender = %s,
                    age = %s,
                    age_group = %s,
                    height_cm = %s,
                    weight_kg = %s,
                    exerciseFrequency = %s,
                    exerciseDuration = %s,
                    exerciseIntensity = %s,
                    pal = NULL
                WHERE id = %s
            """

            # 准备批量参数
            params_list = []
            for member in members_data:
                params = (
                    member['name'],
                    member['gender'],
                    member['age'],
                    member['ageGroup'],
                    member['height_cm'],
                    member['weight_kg'],
                    member['exerciseFrequency'],
                    member['exerciseDuration'],
                    member['exerciseIntensity'],
                    member['member_id']
                )
                params_list.append(params)

            # 执行批量更新
            total_affected = db.executemany(sql, params_list)

            # 构建详细结果
            details = []
            for member in members_data:
                details.append({
                    'member_id': member['member_id'],
                    'name': member['name'],
                    'status': 'updated'
                })

            return {
                'success': True,
                'message': f'成功批量更新 {total_affected} 个家庭成员信息',
                'total_affected': total_affected,
                'details': details
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'批量更新失败: {str(e)}',
                'total_affected': 0,
                'details': []
            }

    @staticmethod
    def get_family_member(member_id: int) -> Optional[Dict[str, Any]]:
        """
        根据成员ID获取家庭成员信息
        """
        sql = """
            SELECT 
                id as member_id,
                name,
                gender,
                age,
                age_group as ageGroup,
                height_cm,
                weight_kg,
                exerciseFrequency,
                exerciseDuration,
                exerciseIntensity,
                relation,
                birthday,
                pal,
                owner_id,
                family_id
            FROM ejia_user_family_member 
            WHERE id = %s
        """

        result = db.query_one(sql, (member_id,))
        return dict(result) if result else None

    @staticmethod
    def delete_family_member(member_id: int) -> Dict[str, Any]:
        """
        删除家庭成员
        """
        try:
            sql = "DELETE FROM ejia_user_family_member WHERE id = %s"
            result = db.execute(sql, (member_id,))

            return {
                'success': True,
                'message': '家庭成员删除成功',
                'member_id': member_id,
                'affected_rows': result
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'删除失败: {str(e)}',
                'member_id': member_id
            }