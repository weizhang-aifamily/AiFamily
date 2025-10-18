# common_nutrient_calculator.py
from typing import Dict, Any
from models.nutrition_data import NutritionData
from models.nutrient_config import MEAL_RATIO


class CommonNutrientCalculator:
    """共用营养计算器 - 确保套餐生成和营养分析使用相同逻辑"""

    @staticmethod
    def calculate_daily_nutrient_targets(member: Dict[str, Any]) -> Dict[str, float]:
        """
        计算成员每日营养目标（与营养分析器相同逻辑）

        Args:
            member: 成员信息字典，包含 age, gender, height_cm, weight_kg, ageGroup

        Returns:
            Dict[str, float]: 营养素代码到目标值的映射
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

            # 3. 计算BMR（与营养分析器完全相同）
            bmr = NutritionData.calculate_advanced_bmr(
                height_cm, weight_kg, age, gender, age_group
            )

            # 4. 按营养素类型分别计算
            targets = {}

            # 热量：直接使用BMR
            targets['calories'] = round(bmr)

            # 蛋白质：按体重计算
            protein_rdi = rdi_data.get('protein')
            if protein_rdi:
                protein_amount = weight_kg * protein_rdi['amount']
                targets['protein'] = round(protein_amount * 10) / 10  # 保留1位小数
            else:
                # 降级处理（与营养分析器相同）
                targets['protein'] = round(weight_kg * 1.2 * 10) / 10

            # 脂肪：基于BMR和能量比例
            fat_rdi = rdi_data.get('fat', {'amount': 0.25})
            fat_calories = bmr * fat_rdi['amount']
            targets['fat'] = round((fat_calories / 9) * 10) / 10  # 保留1位小数

            # 碳水：基于BMR和能量比例
            carbs_rdi = rdi_data.get('carbohydrate', {'amount': 0.55})
            carbs_calories = bmr * carbs_rdi['amount']
            targets['carbohydrate'] = round((carbs_calories / 4) * 10) / 10  # 保留1位小数

            # 其他营养素直接使用RDI值（如钙、铁、维生素等）
            for nutrient_name, nutrient_info in rdi_data.items():
                if nutrient_name not in ['protein', 'fat', 'carbohydrate']:
                    # 对于矿物质和维生素，直接使用RDI值
                    targets[nutrient_name] = round(nutrient_info['amount'])

            return targets

        except Exception as e:
            print(f"计算成员营养目标时出错: {str(e)}")
            # 降级处理：返回基础值
            return CommonNutrientCalculator._get_fallback_targets(member)

    @staticmethod
    def calculate_meal_nutrient_targets(daily_targets: Dict[str, float], meal_type: str) -> Dict[str, float]:
        """
        计算单餐营养目标

        Args:
            daily_targets: 每日营养目标
            meal_type: 餐次类型 'breakfast'|'lunch'|'dinner'|'all'

        Returns:
            Dict[str, float]: 单餐营养目标
        """
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
                meal_targets[nutrient] = daily_value * ratio

        return meal_targets

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
            'calories': round(bmr),
            'protein': round(weight_kg * 1.2 * 10) / 10,
            'fat': round((bmr * 0.25) / 9 * 10) / 10,
            'carbohydrate': round((bmr * 0.55) / 4 * 10) / 10
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