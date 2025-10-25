# nutrient_target_updater.py
import sys
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

from dbconnect.dbconn import db
from models.nutrition_data import NutritionData

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

    """营养目标更新器 """

    def get_member_nutrient_targets(self, member: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """获取成员营养目标 - 直接从RDI表获取，包含RDI和UL数据"""
        try:
            age = int(float(member.get('age', 30)))
            gender = member.get('gender', 'male')

            # 直接从RDI表获取数据
            rdi_data = NutritionData.get_user_rdi(age, gender)
            # 获取所有UL值
            rdi_ul_data = NutritionData.get_user_rdi_ul(age, gender)

            # 合并RDI和UL数据
            targets = {}

            # 首先处理所有RDI数据
            for nutrient_name, nutrient_info in rdi_data.items():
                targets[nutrient_name] = {
                    'amount': nutrient_info['amount'],
                    'unit': nutrient_info['unit']
                }

                # 如果该营养素有UL数据，则添加UL信息
                if nutrient_name in rdi_ul_data:
                    ul_info = rdi_ul_data[nutrient_name]
                    targets[nutrient_name]['amount_ul'] = ul_info['amount_ul']
                    targets[nutrient_name]['unit_ul'] = ul_info['unit_ul']
                else:
                    # 如果没有UL数据，设为None或空值
                    targets[nutrient_name]['amount_ul'] = None
                    targets[nutrient_name]['unit_ul'] = None

            print(f"   ↳ 从RDI表获取 {len(targets)} 个营养素目标（包含RDI和UL数据）")
            return targets

        except Exception as e:
            print(f"从RDI表获取营养目标失败: {str(e)}")
            return {}

    def update_member_nutrient_targets(self, member_id: int, targets: Dict[str, Dict[str, Any]]) -> bool:
        """更新成员营养目标到数据库"""
        try:
            today = date.today()

            for nutrient_code, target_content in targets.items():
                amount = target_content['amount']
                unit = target_content['unit']
                amount_ul = target_content['amount_ul']
                unit_ul = target_content['unit_ul']
                # 检查是否已存在记录
                check_sql = """
                    SELECT id FROM ejia_member_daily_nutrient 
                    WHERE member_id = %s AND nutrient_code = %s AND updated_at = %s
                """
                existing = db.query(check_sql, [member_id, nutrient_code, today])

                if existing:
                    # 更新现有记录
                    update_sql = """
                        UPDATE ejia_member_daily_nutrient 
                        SET need_qty = %s, unit = %s, max_qty = %s, unit_ul = %s
                        WHERE member_id = %s AND nutrient_code = %s AND updated_at = %s
                    """
                    db.execute(update_sql, [amount, unit, amount_ul, unit_ul, member_id, nutrient_code, today])
                    print(f"   ↳ 更新营养素 {nutrient_code}: {amount}")
                else:
                    # 插入新记录
                    insert_sql = """
                        INSERT INTO ejia_member_daily_nutrient 
                        (member_id, nutrient_code, need_qty, unit, max_qty, unit_ul,updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    db.execute(insert_sql, [member_id, nutrient_code, amount, unit, amount_ul, unit_ul, today])
                    print(f"   ↳ 新增营养素 {nutrient_code}: {amount}")

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

    def calculate_actual_nutrient_needs(self, member_id: int, base_targets: Dict[str, Dict[str, Any]]) -> Dict[
        str, Dict[str, Any]]:
        """计算实际营养需求（基础目标 × 饮食需求百分比调整），返回包含unit的数据"""
        try:
            # 获取成员的饮食需求偏移值
            sql = """
                SELECT r.nutrient as nutrient_code, r.offset_val, r.is_positive
                FROM ejia_enum_diet_need_nutrient_rule r
                join ejia_member_diet_need n on r.need_code = n.need_code
                WHERE member_id = %s
            """
            diet_needs = db.query(sql, [member_id])

            # 复制基础目标结构，包含amount和unit
            actual_needs = {}
            for nutrient_code, nutrient_info in base_targets.items():
                actual_needs[nutrient_code] = {
                    'amount': nutrient_info['amount'],
                    'unit': nutrient_info['unit']
                }

            # 应用百分比调整
            for diet_need in diet_needs:
                nutrient_code = diet_need['nutrient_code']
                offset_percentage = diet_need['offset_val']  # 现在表示百分比，如1.00表示1%
                is_positive = diet_need['is_positive']

                if nutrient_code in actual_needs:
                    base_value = actual_needs[nutrient_code]['amount']
                    unit = actual_needs[nutrient_code]['unit']

                    # 根据正负标志计算调整后的值
                    if is_positive:
                        # 正向调整：增加百分比
                        adjustment_factor = 1 + (offset_percentage / 100)
                        adjusted_value = base_value * adjustment_factor
                        actual_needs[nutrient_code]['amount'] = adjusted_value
                        print(
                            f"   ↳ 应用正向调整 {nutrient_code}: {base_value} × (1 + {offset_percentage}%) = {adjusted_value:.2f} {unit}")
                    else:
                        # 负向调整：减少百分比
                        adjustment_factor = 1 - (offset_percentage / 100)
                        adjusted_value = base_value * adjustment_factor
                        actual_needs[nutrient_code]['amount'] = adjusted_value
                        print(
                            f"   ↳ 应用负向调整 {nutrient_code}: {base_value} × (1 - {offset_percentage}%) = {adjusted_value:.2f} {unit}")
                else:
                    # 如果基础目标中没有该营养素，根据正负标志设置初始值
                    if is_positive:
                        actual_needs[nutrient_code] = {
                            'amount': offset_percentage,
                            'unit': 'g'  # 默认单位，可以根据需要调整
                        }
                        print(f"   ↳ 新增营养素 {nutrient_code}: {offset_percentage} g")
                    else:
                        # 对于负向调整但基础值不存在的情况，可以设置为0或者保持原逻辑
                        actual_needs[nutrient_code] = {
                            'amount': 0,
                            'unit': 'g'  # 默认单位
                        }
                        print(f"   ↳ 新增营养素 {nutrient_code}: 0 g (负向调整但无基础值)")

            return actual_needs

        except Exception as e:
            print(f"计算成员 {member_id} 实际营养需求时出错: {str(e)}")
            return base_targets  # 出错时返回基础目标

    def update_actual_nutrient_needs(self, member_id: int, actual_needs: Dict[str, Dict[str, Any]],
                                     member: Dict[str, Any]) -> bool:
        """更新实际营养需求到 ejia_member_daily_nutrient_actual 表，使用UL表数据，包含unit字段"""
        try:
            today = date.today()
            age = int(float(member.get('age', 30)))
            gender = member.get('gender', 'B')

            # 获取所有UL值
            ul_values = NutritionData.get_user_rdi_ul(age, gender)

            print(f"   ↳ 获取到 {len(ul_values)} 个营养素的UL值")

            for nutrient_code, need_info in actual_needs.items():
                need_qty = need_info['amount']
                unit = need_info['unit']

                # 从UL值字典中获取，如果没有则使用备用计算
                max_qty = None
                unit_ul = None
                if nutrient_code in ul_values:
                    max_qty = ul_values[nutrient_code]['amount_ul']
                    unit_ul = ul_values[nutrient_code]['unit_ul']
                    print(f"   ↳ 营养素 {nutrient_code} 使用UL数据: {max_qty} {unit_ul}")

                # 设置最小需求量为实际需求的80%
                min_qty = round(need_qty * 0.8, 3)

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
                        SET need_qty = %s, unit = %s, min_qty = %s, max_qty = %s, unit_ul = %s
                        WHERE member_id = %s AND nutrient_code = %s AND updated_at = %s
                    """
                    db.execute(update_sql,
                               [need_qty, unit, min_qty, max_qty, unit_ul, member_id, nutrient_code, today])
                    print(
                        f"   ↳ 更新实际需求 {nutrient_code}: {need_qty} {unit} (范围: {min_qty}-{max_qty} {unit_ul})")
                else:
                    # 插入新记录
                    insert_sql = """
                        INSERT INTO ejia_member_daily_nutrient_actual 
                        (member_id, nutrient_code, need_qty, unit, updated_at, min_qty, max_qty, unit_ul)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    db.execute(insert_sql,
                               [member_id, nutrient_code, need_qty, unit, today, min_qty, max_qty, unit_ul])
                    print(
                        f"   ↳ 新增实际需求 {nutrient_code}: {need_qty} {unit} (范围: {min_qty}-{max_qty} {unit_ul})")

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
                base_targets = self.get_member_nutrient_targets(member)

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