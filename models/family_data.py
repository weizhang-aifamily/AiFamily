# family_data.py
from typing import Dict, Any, Optional, List
from dbconnect.dbconn import db

class FamilyData:

    @staticmethod
    def save_combo_member_dish_log(combo: Dict[str, Any], members: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        保存套餐成员菜品日志到三个关联表
        """
        try:
            if not combo or not members:
                return {
                    'success': True,
                    'message': '没有需要保存的套餐或成员数据',
                    'total_affected': 0,
                    'details': []
                }

            # 获取当前日期
            from datetime import datetime, date
            current_date = date.today()
            current_time = datetime.now()

            total_affected = 0
            details = []

            owner_id = combo.get('owner_id')

            # 1. 插入主日志表 (ejia_combo_log)
            combo_log_sql = """
                INSERT INTO ejia_combo_log (
                    owner_id, combo_id, eat_date, meal_type, 
                    actual_portion, need_nutrients, actual_nutrients, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            combo_log_params = (
                owner_id,
                combo.get('combo_id'),
                current_date,
                combo.get('meal_type'),
                combo.get('actual_portion'),
                str(combo.get('need_nutrients', '')),
                str(combo.get('actual_nutrients', '')),
                current_time
            )

            combo_log_id = db.execute_return_id(combo_log_sql, combo_log_params)

            # 2. 插入成员日志表 (ejia_combo_member_log)
            member_affected = 0
            member_log_sql = """
                INSERT INTO ejia_combo_member_log (
                    owner_id, combo_log_id, member_id, created_at
                ) VALUES (%s, %s, %s, %s)
            """
            for member in members:
                member_log_params = (
                    owner_id,
                    combo_log_id,
                    str(member.get('member_id')),
                    current_time
                )
                member_affected += db.execute(member_log_sql, member_log_params)

            # 3. 插入菜品日志表 (ejia_combo_dish_log)
            dishes = combo.get('dishes', [])
            dish_affected = 0

            dish_log_sql = """
                INSERT INTO ejia_combo_dish_log (
                    owner_id, combo_log_id, dish_id, created_at
                ) VALUES (%s, %s, %s, %s)
            """

            for dish in dishes:
                dish_log_params = (
                    owner_id,
                    combo_log_id,
                    str(dish.get('dish_id')),
                    current_time
                )
                dish_affected += db.execute(dish_log_sql, dish_log_params)

            total_affected += (1 + member_affected + dish_affected)

            details.append({
                'owner_id': owner_id,
                'combo_log_id': combo_log_id,
                'dishes_count': len(dishes),
                'status': 'saved'
            })

            return {
                'success': True,
                'message': f'成功保存 {len(details)} 个成员的菜品日志，共 {total_affected} 条记录',
                'total_affected': total_affected,
                'details': details
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'保存菜品日志失败: {str(e)}',
                'total_affected': 0,
                'details': []
            }

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