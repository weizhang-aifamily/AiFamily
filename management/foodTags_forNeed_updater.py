# food_nutrient_tagger.py
import sys
import os
from typing import List, Dict, Any, Optional
from models.nutrient_config import NUTRIENT_MAPPING

from dbconnect.dbconn import db
from ejiacanAI.dish2_combo_models import Food


class FoodNutrientTagger:
    """食物营养素标签器 - 根据饮食需求规则为食物打标签"""

    def __init__(self):
        self.nutrient_rules = {}

    def load_nutrient_rules(self) -> List[Dict[str, Any]]:
        """从数据库加载营养素判断规则"""
        try:
            sql = """
                SELECT 
                    need_code,
                    nutrient_name_cn,
                    comparison_operator,
                    threshold_value,
                    unit,
                    description,
                    nutrient
                FROM ejia_enum_diet_need_nutrient_rule
                ORDER BY need_code, id
            """
            rules = db.query(sql)
            print(f"📋 加载了 {len(rules)} 条营养素判断规则")
            return rules
        except Exception as e:
            print(f"❌ 加载营养素判断规则失败: {str(e)}")
            return []

    def get_food_nutrition_data(self, batch_size: int = 1000) -> List[Food]:
        """获取食物营养成分数据并返回Food对象列表"""
        try:
            sql = """
                SELECT 
                    foodCode as foodCode,
                    foodName as foodName,
                    category1 as category1,
                    category2 as category2,
                    edible as edible,
                    water as water,
                    energyKCal as energyKCal,
                    energyKJ as energyKJ,
                    protein as protein,
                    fat as fat,
                    CHO as CHO,
                    dietaryFiber as dietaryFiber,
                    cholesterol as cholesterol,
                    ash as ash,
                    vitaminA as vitaminA,
                    carotene as carotene,
                    retinol as retinol,
                    thiamin as thiamin,
                    riboflavin as riboflavin,
                    niacin as niacin,
                    vitaminC as vitaminC,
                    vitaminETotal as vitaminETotal,
                    vitaminE1 as vitaminE1,
                    vitaminE2 as vitaminE2,
                    vitaminE3 as vitaminE3,
                    Ca as Ca,
                    P as P,
                    K as K,
                    Na as Na,
                    Mg as Mg,
                    Fe as Fe,
                    Zn as Zn,
                    Se as Se,
                    Cu as Cu,
                    Mn as Mn,
                    remark as remark
                FROM food_nutrition 
                WHERE foodCode IS NOT NULL
                LIMIT %s
            """
            raw_foods = db.query(sql, [batch_size])

            # 转换为Food对象
            foods = []
            for raw_food in raw_foods:
                food = Food(
                    food_id=raw_food['foodCode'],  # 使用foodCode作为food_id
                    food_amount_grams=100,  # 默认100g，因为营养成分数据都是基于100g的
                    foodCode=raw_food['foodCode'],
                    foodName=raw_food['foodName'],
                    category1=raw_food['category1'],
                    category2=raw_food.get('category2'),
                    is_main_food='unknown',  # 默认值，可以根据需要调整
                    # 营养成分字段
                    edible=raw_food.get('edible'),
                    water=raw_food.get('water'),
                    energyKCal=raw_food.get('energyKCal'),
                    energyKJ=raw_food.get('energyKJ'),
                    protein=raw_food.get('protein'),
                    fat=raw_food.get('fat'),
                    CHO=raw_food.get('CHO'),
                    dietaryFiber=raw_food.get('dietaryFiber'),
                    cholesterol=raw_food.get('cholesterol'),
                    ash=raw_food.get('ash'),
                    vitaminA=raw_food.get('vitaminA'),
                    carotene=raw_food.get('carotene'),
                    retinol=raw_food.get('retinol'),
                    thiamin=raw_food.get('thiamin'),
                    riboflavin=raw_food.get('riboflavin'),
                    niacin=raw_food.get('niacin'),
                    vitaminC=raw_food.get('vitaminC'),
                    vitaminETotal=raw_food.get('vitaminETotal'),
                    vitaminE1=raw_food.get('vitaminE1'),
                    vitaminE2=raw_food.get('vitaminE2'),
                    vitaminE3=raw_food.get('vitaminE3'),
                    Ca=raw_food.get('Ca'),
                    P=raw_food.get('P'),
                    K=raw_food.get('K'),
                    Na=raw_food.get('Na'),
                    Mg=raw_food.get('Mg'),
                    Fe=raw_food.get('Fe'),
                    Zn=raw_food.get('Zn'),
                    Se=raw_food.get('Se'),
                    Cu=raw_food.get('Cu'),
                    Mn=raw_food.get('Mn'),
                    remark=raw_food.get('remark')
                )
                foods.append(food)

            print(f"🍎 获取了 {len(foods)} 种食物的营养成分数据")
            return foods
        except Exception as e:
            print(f"❌ 获取食物营养成分数据失败: {str(e)}")
            return []

    def check_nutrient_condition(self, food: Food, rule: Dict[str, Any]) -> bool:
        """检查食物是否符合某个营养素规则"""
        try:
            nutrient_field = None
            nutrient_value = None

            # 根据rule中的nutrient字段找到对应的数据库字段
            rule_nutrient = rule.get('nutrient', '').strip()

            # 在映射表中查找对应的字段名
            for db_field, english_name in NUTRIENT_MAPPING.items():
                if english_name.lower() == rule_nutrient.lower():
                    nutrient_field = db_field
                    break

            if not nutrient_field:
                print(f"⚠️  未找到营养素 {rule_nutrient} 对应的数据库字段")
                return False

            # 获取食物的营养素值
            nutrient_value = getattr(food, nutrient_field, None)
            if nutrient_value is None:
                return False

            threshold = float(rule['threshold_value'])
            operator = rule['comparison_operator']

            # 根据比较运算符进行判断
            if operator == '>=':
                return nutrient_value >= threshold
            elif operator == '>':
                return nutrient_value > threshold
            elif operator == '<=':
                return nutrient_value <= threshold
            elif operator == '<':
                return nutrient_value < threshold
            else:
                print(f"⚠️  不支持的比较运算符: {operator}")
                return False

        except Exception as e:
            print(f"❌ 检查营养素条件时出错: {str(e)}, 规则: {rule}")
            return False

    def calculate_food_tags(self, food: Food, rules: List[Dict[str, Any]]) -> List[str]:
        """计算食物的标签列表"""
        tags = []

        for rule in rules:
            if self.check_nutrient_condition(food, rule):
                need_code = rule['need_code']
                if need_code and need_code not in tags:
                    tags.append(need_code)
                    print(f"   ↳ {food.foodName} 符合 {need_code} 标准: {rule['description']}")

        return tags

    def update_food_tags(self, food_code: int, tags: List[str]) -> bool:
        """更新食物的标签到数据库"""
        try:
            if not tags:
                # 如果没有标签，设置为空
                tags_str = None
            else:
                # 将标签列表转换为逗号分隔的字符串
                tags_str = ','.join(tags)

            update_sql = """
                UPDATE food_nutrition 
                SET tags_for_need = %s 
                WHERE foodCode = %s
            """
            result = db.execute(update_sql, [tags_str, food_code])

            if result:
                if tags:
                    print(f"   ✅ 更新食物 {food_code} 标签: {tags_str}")
                else:
                    print(f"   ✅ 清除食物 {food_code} 标签")
                return True
            else:
                print(f"❌ 更新食物 {food_code} 标签失败")
                return False

        except Exception as e:
            print(f"❌ 更新食物标签时出错: {str(e)}")
            return False

    def run_tagging_process(self, batch_size: int = 1000):
        """执行食物标签处理流程"""
        print(f"🚀 开始执行食物营养素标签处理")

        # 1. 加载营养素规则
        rules = self.load_nutrient_rules()
        if not rules:
            print("❌ 无法加载营养素规则，终止处理")
            return 0, 0

        # 2. 获取食物数据
        foods = self.get_food_nutrition_data(batch_size)
        if not foods:
            print("❌ 无法获取食物数据，终止处理")
            return 0, 0

        success_count = 0
        error_count = 0

        # 3. 为每种食物计算标签
        for food in foods:
            try:
                print(f"\n📊 正在处理食物: {food.foodName} (代码: {food.foodCode})")

                # 计算标签
                tags = self.calculate_food_tags(food, rules)

                # 更新到数据库
                if self.update_food_tags(food.foodCode, tags):
                    success_count += 1
                    if tags:
                        print(f"✅ 成功为 {food.foodName} 设置标签: {', '.join(tags)}")
                    else:
                        print(f"ℹ️  {food.foodName} 未符合任何标签标准")
                else:
                    error_count += 1
                    print(f"❌ 更新 {food.foodName} 标签失败")

            except Exception as e:
                error_count += 1
                print(f"💥 处理食物 {food.foodName} 时出错: {str(e)}")

        print(f"\n🎯 标签处理完成 - 成功: {success_count}, 失败: {error_count}")
        return success_count, error_count


def main():
    """主函数"""
    tagger = FoodNutrientTagger()
    success_count, error_count = tagger.run_tagging_process()

    if error_count == 0:
        print("🎉 所有食物标签处理成功！")
    else:
        print(f"⚠️  {error_count} 个食物处理失败，请检查日志")


if __name__ == "__main__":
    main()