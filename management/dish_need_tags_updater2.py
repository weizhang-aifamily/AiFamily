# dish_need_tags_updater2.py
import sys
import os
from typing import List, Dict, Any, Optional
from management.dish_data import DishData
from dbconnect.dbconn import db


class DishNeedTaggerBatch:
    """菜品需求标签批量更新器 - 全部调用现有方法"""

    def get_all_dishes(self) -> List[Dict[str, Any]]:
        """获取所有有效菜品"""
        try:
            sql = "SELECT id, name FROM ejia_dish WHERE status = 1"
            dishes = db.query(sql)
            print(f"🍽️  获取了 {len(dishes)} 个有效菜品")
            return dishes
        except Exception as e:
            print(f"❌ 获取菜品列表失败: {str(e)}")
            return []

    def process_single_dish(self, dish_id: int, dish_name: str) -> bool:
        """处理单个菜品 - 完全复用needtag_dish逻辑"""
        try:
            print(f"\n📊 正在处理菜品: {dish_name} (ID: {dish_id})")

            # 1. 读规则
            rules = DishData.get_need_rule()

            # 2. 获取食材营养信息
            rows = DishData.get_dish_food_nut(dish_id)
            if not rows:
                print("    ℹ️  该菜品无食材信息")
                return False

            print(f"    包含 {len(rows)} 种食材")

            # 3. 算营养 - 直接调用 DishData 的方法
            total = DishData.calc_per_100g_raw(rows)
            if not total:
                print("    ℹ️  无法计算菜品营养成分")
                return False

            # 4. 比阈值
            hit_codes = []
            for rule in rules:
                val = total.get(rule.nutrient)
                if val is None:
                    continue
                ok = False
                if rule.comparison_operator == ">=":
                    ok = val >= rule.threshold_value
                elif rule.comparison_operator == "<=":
                    ok = val <= rule.threshold_value
                if ok:
                    hit_codes.append(rule.need_code)
                    print(f"     ✅ {rule.need_code}: {val:.2f} {rule.comparison_operator} {rule.threshold_value}")

            # 5. 写标签
            DishData.update_dish_needtag(dish_id, hit_codes)

            if hit_codes:
                print(f"    ✅ 成功设置标签: {', '.join(hit_codes)}")
            else:
                print(f"    ℹ️  未符合任何标签标准")
            return True

        except Exception as e:
            print(f"💥 处理菜品 {dish_name} 时出错: {str(e)}")
            return False

    def run_batch_tagging(self):
        """批量执行菜品标签更新"""
        print("🚀 开始执行菜品需求标签批量更新")

        dishes = self.get_all_dishes()
        if not dishes:
            print("❌ 无法获取菜品数据，终止处理")
            return 0, 0

        success_count = 0
        error_count = 0

        for dish in dishes:
            if self.process_single_dish(dish['id'], dish['name']):
                success_count += 1
            else:
                error_count += 1

        print(f"\n🎯 批量更新完成 - 成功: {success_count}, 失败: {error_count}")
        return success_count, error_count


def main():
    """主函数"""
    tagger = DishNeedTaggerBatch()
    success_count, error_count = tagger.run_batch_tagging()

    if error_count == 0:
        print("🎉 所有菜品标签更新成功！")
    else:
        print(f"⚠️  {error_count} 个菜品更新失败，请检查日志")


if __name__ == "__main__":
    main()