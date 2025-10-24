# common_nutrient_calculator.py
from collections import defaultdict
from typing import Dict, Any, List

from ejiacanAI.dish2_combo_models import Dish
from models.nutrition_data import NutritionData
from models.nutrient_config import MEAL_RATIO
from models.nutrition_models import NutritionAnalysisInput


class CommonNutrientCalculator:
    """共用营养计算器 - 确保套餐生成和营养分析使用相同逻辑"""

    # -------------------------------------------------
    # 2. 计算每日需求（基于 MemberNeedNutrient）
    # -------------------------------------------------
    @staticmethod
    def get_daily_range(members: List[Dict]) -> Dict[str, Dict[str, float]]:
        """计算每日营养需求范围，使用 CommonNutrientCalculator 逻辑"""
        ranges = defaultdict(lambda: {"min": 0.0, "max": 0.0, "need": 0.0})

        # 为每个成员计算营养需求（使用 CommonNutrientCalculator）
        for member in members:
            daily_targets = NutritionData.get_daily_nutrient_targets_actual(member)

            # 累加到总需求中
            for nutrient_code, target_content in daily_targets.items():
                # 设置 min 和 max 范围（±20%）
                target_need = target_content['amount']
                nutrient_min = target_need * 0.8
                amount_ul = target_content.get('amount_ul')
                nutrient_max = amount_ul if amount_ul is not None else target_need * 1.2
                nutrient_need = target_need

                ranges[nutrient_code]["min"] += nutrient_min
                ranges[nutrient_code]["max"] += nutrient_max
                ranges[nutrient_code]["need"] += nutrient_need

        return dict(ranges)

    @staticmethod
    def get_meal_nutrient_targets_actual(user_input: NutritionAnalysisInput, meal_type: str) -> Dict[str, float]:
        """
        计算单餐营养目标

        Args:
            user_input: 用户输入数据
            meal_type: 餐次类型 'breakfast'|'lunch'|'dinner'|'all'

        Returns:
            Dict[str, float]: 单餐营养目标
        """
        try:
            # 将 NutritionAnalysisInput 转换为成员字典格式
            member_data = {
                'age': user_input.age,
                'gender': user_input.gender,
                'height_cm': user_input.height_cm,
                'weight_kg': user_input.weight_kg,
                'ageGroup': user_input.ageGroup,
                'member_id': getattr(user_input, 'id', None)  # 如果有member_id也传入
            }

            # 获取每日营养目标（优先使用实际数据）
            daily_targets = NutritionData.get_daily_nutrient_targets_actual(member_data)
            daily_targets_amount_only = {
                nutrient_code: target_info.get('amount', 0.0)
                for nutrient_code, target_info in daily_targets.items()
            }
            if meal_type == 'all':
                return daily_targets_amount_only.copy()

            ratio = MEAL_RATIO.get(meal_type, 1.0)
            meal_targets = {}

            for nutrient, daily_value in daily_targets_amount_only.items():
                # 特殊处理：热量使用round，其他营养素保留小数位
                if nutrient == 'calories':
                    meal_targets[nutrient] = round(daily_value * ratio)
                elif nutrient in ['protein', 'fat', 'carbohydrate']:
                    meal_targets[nutrient] = round(daily_value * ratio * 10) / 10
                else:
                    meal_targets[nutrient] = round(daily_value * ratio, 2)

            return meal_targets

        except Exception as e:
            print(f"计算单餐营养目标时出错: {str(e)}")
