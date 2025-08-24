import pulp
from typing import List, Dict
from ejiacanAI.models import Dish, FamilyNeed


class ILPRecommender:
    def __init__(self):
        # 直接使用 PULP_CBC_CMD，这是最稳定的选项
        self.solver = pulp.PULP_CBC_CMD(msg=False)

    def recommend(self, dishes: List[Dish], need: FamilyNeed, top_k: int = 5) -> List[Dict]:
        # 创建问题实例
        prob = pulp.LpProblem('FamilyMenuOptimization', pulp.LpMaximize)

        # 创建菜品映射
        dish_map = {d.id: d for d in dishes}

        # 创建决策变量
        decision_vars = {}
        for dish in dishes:
            for servings in range(1, dish.max_servings + 1):
                var_name = f"dish_{dish.id}_servings_{servings}"
                decision_vars[(dish.id, servings)] = pulp.LpVariable(var_name, cat='Binary')

        # 计算总营养摄入量
        def total_nutrient(nutrient_name):
            return pulp.lpSum(
                var * servings * getattr(dish_map[dish_id], nutrient_name) * dish_map[dish_id].default_portion_g / 100.0
                for (dish_id, servings), var in decision_vars.items()
            )

        # 设置目标函数
        total_calcium = total_nutrient('calcium')
        total_iron = total_nutrient('iron')

        # 防止除零错误
        calcium_target = max(float(need.calcium_target), 1.0)
        iron_target = max(float(need.iron_target), 1.0)

        prob += total_calcium / calcium_target + total_iron / iron_target

        # 添加约束条件
        prob += total_calcium >= need.calcium_target, "calcium_min"
        prob += total_iron >= need.iron_target, "iron_min"
        prob += total_nutrient('sodium') <= need.sodium_limit, "sodium_max"
        prob += total_nutrient('purine') <= need.purine_limit, "purine_max"
        prob += total_nutrient('kcal') <= need.kcal_limit, "kcal_max"
        prob += pulp.lpSum(decision_vars.values()) <= top_k, "max_dishes"

        # 求解
        status = prob.solve(self.solver)

        # 提取结果
        result = []
        for (dish_id, servings), var in decision_vars.items():
            if pulp.value(var) == 1:
                dish = dish_map[dish_id]
                result.append({
                    'dish_id': dish.id,
                    'name': dish.name,
                    'emoji': dish.emoji,
                    'servings': servings,
                    'portion_g': dish.default_portion_g * servings
                })

        return result