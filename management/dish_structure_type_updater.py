# nutrient_target_updater.py
import sys
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

from dbconnect.dbconn import db
from ejiacanAI.dish2_combo_models import Dish
from models.nutrition_data import NutritionData

class DishStructureTypeUpdater:
    """营养目标更新器"""

    def __init__(self):
        self.nutrition_data = NutritionData()

    def classify_dish_structure_type(dish: Dish) -> str:
        """判断菜品属于哪个类别"""
        dish_tags = getattr(dish, 'dish_tags', {}) or {}

        # 1. 优先使用 dish_tags 中的明确分类
        # 主食判断
        staple_tags = dish_tags.get('staple', [])
        for tag in staple_tags:
            code = tag.get('code', '')
            if code == 'yes':  # 明确标记为主食
                return 'staple'

        # 2. 使用 vege 标签进行荤素分类
        vege_tags = dish_tags.get('vege', [])
        for tag in vege_tags:
            code = tag.get('code', '')
            # 荤菜类别
            if code in ['meat','seafood']:
                return 'main_dish'
            # 素菜类别
            elif code in ['vege', 'vegan', 'egg']:
                return 'side_dish'

        # 3. 使用 category 判断汤品
        category_tags = dish_tags.get('category', [])
        for tag in category_tags:
            code = tag.get('code', '')
            if code in ['soup']:  # 汤品烹饪方法
                return 'soup'
        # 3. 使用 people 判断baby_food
        category_tags = dish_tags.get('people', [])
        for tag in category_tags:
            code = tag.get('code', '')
            if code in ['baby']:
                return 'baby_food'

        # 4. 根据营养素含量进行智能判断
        nutrients = getattr(dish, 'nutrients', {}) or {}
        protein = nutrients.get('Protein', 0)
        carbs = nutrients.get('Carbohydrate', 0)

        # 高碳水且低蛋白的可能是主食
        if carbs > 40 and protein < 10:
            return 'staple'

        # 高蛋白的可能是主菜
        if protein > 20:
            return 'main_dish'
        elif protein > 8:
            return 'side_dish'

        # 5. 最终默认分类
        # 如果以上都无法判断，保守地分类为配菜
        return 'side_dish'

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