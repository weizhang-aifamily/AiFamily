# nutrient_target_updater.py
import sys
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

from dbconnect.dbconn import db
from models.nutrition_data import NutritionData
from models.common_nutrient_calculator import CommonNutrientCalculator

class NutrientTargetUpdater:
    """营养目标更新器"""

    def __init__(self):
        self.nutrition_data = NutritionData()

    def get_all_family_members(self) -> List[Dict[str, Any]]:
        """获取所有家庭成员信息"""
        sql = """
            SELECT 
                id as member_id,
                name,
                gender,
                CAST(age AS UNSIGNED) as age,
                COALESCE(age_group, 'middle') as ageGroup,
                height_cm,
                weight_kg,
                COALESCE(exerciseFrequency, 'moderate') as exerciseFrequency,
                COALESCE(exerciseDuration, 'medium') as exerciseDuration,
                COALESCE(exerciseIntensity, 'medium') as exerciseIntensity
            FROM ejia_user_family_member 
            WHERE height_cm IS NOT NULL 
                AND weight_kg IS NOT NULL 
                AND age IS NOT NULL
        """
        return db.query(sql)

    """营养目标更新器 - 使用共用计算逻辑"""

    def calculate_member_nutrient_targets(self, member: Dict[str, Any]) -> Dict[str, float]:
        """计算成员营养目标 - 直接从RDI表获取"""
        try:
            age = int(float(member.get('age', 30)))
            gender = member.get('gender', 'male')

            # 直接从RDI表获取数据
            rdi_data = NutritionData.get_user_rdi(age, gender)

            # 转换为目标格式
            targets = {}
            for nutrient_name, nutrient_info in rdi_data.items():
                targets[nutrient_name] = nutrient_info['amount']

            print(f"   ↳ 从RDI表获取 {len(targets)} 个营养素目标")
            return targets

        except Exception as e:
            print(f"从RDI表获取营养目标失败: {str(e)}")
            return self._fallback_calculate_targets(member)

    def _fallback_calculate_targets(self, member: Dict[str, Any]) -> Dict[str, float]:
        """降级计算方法（保持原有逻辑）"""
        try:
            rdi_data = NutritionData.get_user_rdi(
                int(float(member['age'])),
                member['gender']
            )
            targets = {}
            for nutrient_name, nutrient_info in rdi_data.items():
                targets[nutrient_name] = nutrient_info['amount']
            return targets
        except Exception as e:
            print(f"降级计算也失败: {str(e)}")
            return {}

    def calculate_max_quantity(self, nutrient_name: str, target_value: float) -> float:
        """计算营养素的最大安全摄入量（使用更精确的计算）"""
        # 安全上限系数（基于营养学标准）
        safety_factors = {
            'calories': 1.3,  # 热量最多超30%
            'protein': 2.0,  # 蛋白质最多2倍
            'fat': 1.5,  # 脂肪最多1.5倍
            'carbohydrate': 1.5,  # 碳水最多1.5倍
            'calcium': 2.5,  # 钙最多2.5倍
            'iron': 3.0,  # 铁最多3倍
            'vitamin_c': 5.0,  # 维生素C最多5倍
            'vitamin_a': 3.0,  # 维生素A最多3倍
            'sodium': 2.0,  # 钠最多2倍
            'dietary_fiber': 2.0,  # 膳食纤维最多2倍
        }

        factor = safety_factors.get(nutrient_name, 2.0)
        max_qty = target_value * factor

        # 根据营养素类型进行精度处理
        if nutrient_name in ['calories']:
            return round(max_qty)
        elif nutrient_name in ['protein', 'fat', 'carbohydrate']:
            return round(max_qty * 10) / 10
        else:
            return round(max_qty * 1000) / 1000  # 保留3位小数

    def update_member_nutrient_targets(self, member_id: int, targets: Dict[str, float]) -> bool:
        """更新成员营养目标到数据库"""
        try:
            today = date.today()

            for nutrient_name, target_value in targets.items():
                # 直接使用nutrient_name作为nutrient_code（假设nutrient_rdi表中的nutrient字段就是代码）
                nutrient_code = nutrient_name

                # 检查是否已存在记录
                check_sql = """
                    SELECT id FROM ejia_member_daily_nutrient 
                    WHERE member_id = %s AND nutrient_code = %s AND updated_at = %s
                """
                existing = db.query(check_sql, [member_id, nutrient_code, today])

                # 计算最大安全量
                max_qty = self.calculate_max_quantity(nutrient_name, target_value)

                if existing:
                    # 更新现有记录
                    update_sql = """
                        UPDATE ejia_member_daily_nutrient 
                        SET need_qty = %s, max_qty = %s
                        WHERE member_id = %s AND nutrient_code = %s AND updated_at = %s
                    """
                    db.execute(update_sql, [target_value, max_qty, member_id, nutrient_code, today])
                    print(f"   ↳ 更新营养素 {nutrient_name}: {target_value}")
                else:
                    # 插入新记录
                    insert_sql = """
                        INSERT INTO ejia_member_daily_nutrient 
                        (member_id, nutrient_code, need_qty, updated_at, max_qty)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    db.execute(insert_sql, [member_id, nutrient_code, target_value, today, max_qty])
                    print(f"   ↳ 新增营养素 {nutrient_name}: {target_value}")

            return True

        except Exception as e:
            print(f"更新成员 {member_id} 营养目标时出错: {str(e)}")
            return False

    def cleanup_old_records(self, days_to_keep: int = 30):
        """清理旧的营养目标记录"""
        try:
            cutoff_date = date.today()
            cleanup_sql = """
                DELETE FROM ejia_member_daily_nutrient 
                WHERE updated_at < %s
            """
            result = db.execute(cleanup_sql, [cutoff_date])
            print(f"🗑️  1清理了 {result} 条 {days_to_keep} 天前的旧记录")
            cleanup_sql2 = """
                DELETE FROM ejia_member_daily_nutrient_actual 
                WHERE updated_at < %s
            """
            result = db.execute(cleanup_sql2, [cutoff_date])
            print(f"🗑️  2清理了 {result} 条 {days_to_keep} 天前的旧记录")
        except Exception as e:
            print(f"清理旧记录时出错: {str(e)}")

    def calculate_actual_nutrient_needs(self, member_id: int, base_targets: Dict[str, float]) -> Dict[str, float]:
        """计算实际营养需求（基础目标 × 饮食需求百分比调整）"""
        try:
            # 获取成员的饮食需求偏移值
            sql = """
                SELECT nutrient_code, offset_val, is_positive
                FROM ejia_member_diet_need 
                WHERE member_id = %s AND offset_val IS NOT NULL
            """
            diet_needs = db.query(sql, [member_id])

            actual_needs = base_targets.copy()  # 复制基础目标

            # 应用百分比调整
            for diet_need in diet_needs:
                nutrient_code = diet_need['nutrient_code']
                offset_percentage = diet_need['offset_val']  # 现在表示百分比，如1.00表示1%
                is_positive = diet_need['is_positive']

                if nutrient_code in actual_needs:
                    base_value = actual_needs[nutrient_code]

                    # 根据正负标志计算调整后的值
                    if is_positive:
                        # 正向调整：增加百分比
                        adjustment_factor = 1 + (offset_percentage / 100)
                        actual_needs[nutrient_code] = base_value * adjustment_factor
                        print(
                            f"   ↳ 应用正向调整 {nutrient_code}: {base_value} × (1 + {offset_percentage}%) = {actual_needs[nutrient_code]:.2f}")
                    else:
                        # 负向调整：减少百分比
                        adjustment_factor = 1 - (offset_percentage / 100)
                        actual_needs[nutrient_code] = base_value * adjustment_factor
                        print(
                            f"   ↳ 应用负向调整 {nutrient_code}: {base_value} × (1 - {offset_percentage}%) = {actual_needs[nutrient_code]:.2f}")
                else:
                    # 如果基础目标中没有该营养素，根据正负标志设置初始值
                    if is_positive:
                        actual_needs[nutrient_code] = offset_percentage
                        print(f"   ↳ 新增营养素 {nutrient_code}: {offset_percentage}")
                    else:
                        # 对于负向调整但基础值不存在的情况，可以设置为0或者保持原逻辑
                        actual_needs[nutrient_code] = 0
                        print(f"   ↳ 新增营养素 {nutrient_code}: 0 (负向调整但无基础值)")

            return actual_needs

        except Exception as e:
            print(f"计算成员 {member_id} 实际营养需求时出错: {str(e)}")
            return base_targets  # 出错时返回基础目标

    def update_actual_nutrient_needs(self, member_id: int, actual_needs: Dict[str, float],
                                     member: Dict[str, Any]) -> bool:
        """更新实际营养需求到 ejia_member_daily_nutrient_actual 表，使用UL表数据"""
        try:
            today = date.today()
            age = int(float(member.get('age', 30)))
            gender = member.get('gender', 'B')

            # 获取所有UL值
            ul_values = NutritionData.get_user_rdi_ul(age, gender)

            print(f"   ↳ 获取到 {len(ul_values)} 个营养素的UL值")

            for nutrient_code, need_qty in actual_needs.items():
                # 从UL值字典中获取，如果没有则使用备用计算
                max_need_qty = ul_values.get(nutrient_code)
                if max_need_qty is None:
                    max_need_qty = self.calculate_max_quantity(nutrient_code, need_qty)
                    print(f"   ↳ 营养素 {nutrient_code} 无UL数据，使用计算值: {max_need_qty}")

                # 设置最小需求量为实际需求的80%
                min_need_qty = round(need_qty * 0.8, 3)

                # 检查是否已存在记录
                check_sql = """
                    SELECT id FROM ejia_member_daily_nutrient_actual 
                    WHERE member_id = %s AND nutrient_code = %s AND updated_at = %s
                """
                existing = db.query(check_sql, [member_id, nutrient_code, today])

                if existing:
                    # 更新现有记录
                    update_sql = """
                        UPDATE ejia_member_daily_nutrient_actual 
                        SET need_qty = %s, min_need_qty = %s, max_need_qty = %s
                        WHERE member_id = %s AND nutrient_code = %s AND updated_at = %s
                    """
                    db.execute(update_sql, [need_qty, min_need_qty, max_need_qty, member_id, nutrient_code, today])
                    print(f"   ↳ 更新实际需求 {nutrient_code}: {need_qty} (范围: {min_need_qty}-{max_need_qty})")
                else:
                    # 插入新记录
                    insert_sql = """
                        INSERT INTO ejia_member_daily_nutrient_actual 
                        (member_id, nutrient_code, need_qty, updated_at, min_need_qty, max_need_qty)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    db.execute(insert_sql, [member_id, nutrient_code, need_qty, today, min_need_qty, max_need_qty])
                    print(f"   ↳ 新增实际需求 {nutrient_code}: {need_qty} (范围: {min_need_qty}-{max_need_qty})")

            return True

        except Exception as e:
            print(f"更新成员 {member_id} 实际营养需求时出错: {str(e)}")
            return False

    def run_daily_update(self):
        """执行每日更新"""
        print(f"🚀 开始执行营养目标更新 - {datetime.now()}")

        # 获取所有家庭成员
        members = self.get_all_family_members()
        print(f"👥 找到 {len(members)} 个家庭成员")

        success_count = 0
        error_count = 0

        for member in members:
            try:
                print(f"\n📊 正在计算 {member['name']} 的营养目标...")

                # 计算基础营养目标 - 直接从RDI获取
                base_targets = self.calculate_member_nutrient_targets(member)

                if base_targets:
                    # 1. 更新基础目标到 ejia_member_daily_nutrient
                    if self.update_member_nutrient_targets(member['member_id'], base_targets):

                        # 2. 计算实际营养需求（基础目标 + 饮食需求偏移值）
                        actual_needs = self.calculate_actual_nutrient_needs(member['member_id'], base_targets)

                        # 3. 更新实际需求到 ejia_member_daily_nutrient_actual
                        if self.update_actual_nutrient_needs(member['member_id'], actual_needs, member):
                            success_count += 1
                            print(
                                f"✅ 成功更新成员 {member['name']} 的 {len(base_targets)} 个基础目标和 {len(actual_needs)} 个实际需求")
                        else:
                            error_count += 1
                            print(f"❌ 更新成员 {member['name']} 实际需求失败")
                    else:
                        error_count += 1
                        print(f"❌ 更新成员 {member['name']} 基础目标失败")
                else:
                    error_count += 1
                    print(f"⚠️ 无法计算成员 {member['name']} 的营养目标")

            except Exception as e:
                error_count += 1
                print(f"💥 处理成员 {member['name']} 时出错: {str(e)}")

        # 清理旧记录
        self.cleanup_old_records()

        print(f"\n🎯 更新完成 - 成功: {success_count}, 失败: {error_count}")
        return success_count, error_count


def main():
    """主函数"""
    updater = NutrientTargetUpdater()
    success_count, error_count = updater.run_daily_update()

    if error_count == 0:
        print("🎉 所有成员营养目标更新成功！")
    else:
        print(f"⚠️  {error_count} 个成员更新失败，请检查日志")


if __name__ == "__main__":
    main()