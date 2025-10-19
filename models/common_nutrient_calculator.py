# common_nutrient_calculator.py
from collections import defaultdict
from typing import Dict, Any, List
from models.nutrition_data import NutritionData
from models.nutrient_config import MEAL_RATIO
from models.nutrition_models import NutritionAnalysisInput


class CommonNutrientCalculator:
    """共用营养计算器 - 确保套餐生成和营养分析使用相同逻辑"""

    @staticmethod
    def calculate_daily_nutrient_targets(member: Dict[str, Any]) -> Dict[str, float]:
        """
        计算成员每日营养目标（与营养分析器相同逻辑）
        """
        try:
            # 1. 参数验证和类型转换
            age = int(float(member.get('age', 30)))
            gender = member.get('gender', 'male')
            height_cm = float(member.get('height_cm', 170))
            weight_kg = float(member.get('weight_kg', 65))
            age_group = member.get('ageGroup', 'middle')

            # 2. 获取RDI数据
            rdi_data = NutritionData.get_user_rdi(age, gender)

            # 4. 按营养素类型分别计算
            targets = {}

            # 热量：直接使用BMR
            calories_rdi = rdi_data.get('EnergyKCal')
            if calories_rdi:
                calories_amount = calories_rdi['amount']
                targets['Calories'] = round(calories_amount * 10) / 10  # 保留1位小数

            # 蛋白质：按体重计算
            protein_rdi = rdi_data.get('Protein')
            if protein_rdi:
                protein_amount = protein_rdi['amount']
                targets['Protein'] = round(protein_amount * 10) / 10  # 保留1位小数

            # 修正：脂肪计算 - 使用正确的能量转换
            fat_rdi = rdi_data.get('Fat', {'amount': 0.25})
            # 脂肪供能比例 × 总热量 ÷ 9（1克脂肪=9千卡）
            fat_grams = fat_rdi['amount']
            targets['Fat'] = round(fat_grams * 10) / 10  # 保留1位小数

            # 修正：碳水计算 - 使用正确的能量转换
            carbs_rdi = rdi_data.get('Carbohydrate', {'amount': 0.55})
            # 碳水供能比例 × 总热量 ÷ 4（1克碳水=4千卡）
            carbs_grams = carbs_rdi['amount']
            targets['Carbohydrate'] = round(carbs_grams * 10) / 10  # 保留1位小数

            # 其他营养素直接使用RDI值（如钙、铁、维生素等）
            for nutrient_name, nutrient_info in rdi_data.items():
                if nutrient_name not in ['Protein', 'Fat', 'Carbohydrate']:
                    # 对于矿物质和维生素，直接使用RDI值
                    targets[nutrient_name] = round(nutrient_info['amount'])

            # 调试输出
            print(f"调试营养计算 - EnergyKCal: {targets.get('Calories')}, 蛋白质: {targets.get('Protein')}, "
                  f"脂肪: {targets.get('Fat')}, 碳水: {targets.get('Carbohydrate')}")

            return targets

        except Exception as e:
            print(f"计算成员营养目标时出错: {str(e)}")
            # 降级处理：返回基础值
            return CommonNutrientCalculator._get_fallback_targets(member)

    # 在 CommonNutrientCalculator 中添加
    @staticmethod
    def get_unified_daily_nutrient_targets(member: Dict[str, Any]) -> Dict[str, float]:
        """
        统一获取每日营养目标：优先使用实际数据，如果没有则使用计算值
        """
        # 1. 尝试获取实际数据
        actual_targets = NutritionData.get_daily_nutrient_targets_actual(member)

        # 2. 如果有实际数据且不为空，直接返回
        if actual_targets:
            return actual_targets

        # 3. 否则使用计算值
        return CommonNutrientCalculator.calculate_daily_nutrient_targets(member)

    # -------------------------------------------------
    # 2. 计算每日需求（基于 MemberNeedNutrient）
    # -------------------------------------------------
    @staticmethod
    def calc_daily_range(members: List[Dict]) -> Dict[str, Dict[str, float]]:
        """计算每日营养需求范围，使用 CommonNutrientCalculator 逻辑"""
        ranges = defaultdict(lambda: {"min": 0.0, "max": 0.0, "need": 0.0})

        # 为每个成员计算营养需求（使用 CommonNutrientCalculator）
        for member in members:
            daily_targets = CommonNutrientCalculator.get_unified_daily_nutrient_targets(member)

            # 累加到总需求中
            for nutrient_code, target_value in daily_targets.items():
                # 设置 min 和 max 范围（±20%）
                nutrient_min = target_value * 0.8
                nutrient_max = target_value * 1.2
                nutrient_need = target_value

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
            daily_targets = CommonNutrientCalculator.get_unified_daily_nutrient_targets(member_data)

            if meal_type == 'all':
                return daily_targets.copy()

            ratio = MEAL_RATIO.get(meal_type, 1.0)
            meal_targets = {}

            for nutrient, daily_value in daily_targets.items():
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

    @staticmethod
    def _get_fallback_targets(member: Dict[str, Any]) -> Dict[str, float]:
        """降级计算方法（与营养分析器保持一致）"""
        weight_kg = float(member.get('weight_kg', 65))
        height_cm = float(member.get('height_cm', 170))
        age = int(float(member.get('age', 30)))
        gender = member.get('gender', 'male')

        # 计算基础BMR
        bmr = NutritionData.calculate_advanced_bmr(
            height_cm, weight_kg, age, gender, 'middle'
        )

        return {
            'Calories': round(bmr),
            'Protein': round(weight_kg * 1.2 * 10) / 10,
            'Fat': round((bmr * 0.25) / 9 * 10) / 10,
            'Carbohydrate': round((bmr * 0.55) / 4 * 10) / 10
        }

    @staticmethod
    def get_nutrient_display_name(nutrient_code: str) -> str:
        """获取营养素的显示名称"""
        display_names = {
            'calories': '热量',
            'protein': '蛋白质',
            'fat': '脂肪',
            'carbohydrate': '碳水化合物',
            'calcium': '钙',
            'iron': '铁',
            'vitamin_c': '维生素C',
            'vitamin_a': '维生素A',
            'sodium': '钠',
            'dietary_fiber': '膳食纤维'
        }
        return display_names.get(nutrient_code, nutrient_code)