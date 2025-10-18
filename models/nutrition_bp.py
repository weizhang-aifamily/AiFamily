from typing import List, Dict, Optional, Any
from flask import Blueprint, request, jsonify
from models.nutrition_data import NutritionData
from models.nutrition_models import (
    NutritionAnalysisInput, NutritionBaseline, NutritionDifferences,
    WeightPrediction, BodyImagePrediction, NutritionAnalysisResult
)
from models.common_nutrient_calculator import CommonNutrientCalculator

nutrition_bp = Blueprint('nutrition', __name__, url_prefix='/nutrition')


class NutritionAnalyzer:
    """营养分析器主类"""

    def __init__(self):
        self.nutrition_data = NutritionData()

    """营养分析器 - 可以使用共用方法确保一致性"""

    def calculate_baseline(self, user_input: NutritionAnalysisInput, meal_type: str = 'all') -> NutritionBaseline:
        """计算营养基准 - 可以使用共用方法"""
        try:
            # 转换为成员字典格式
            member_data = {
                'age': user_input.age,
                'gender': user_input.gender,
                'height_cm': user_input.height_cm,
                'weight_kg': user_input.weight_kg,
                'ageGroup': user_input.ageGroup
            }

            # 使用共用计算器获取每日目标
            daily_targets = CommonNutrientCalculator.calculate_daily_nutrient_targets(member_data)

            # 如果需要单餐目标，进一步计算
            if meal_type != 'all':
                meal_targets = CommonNutrientCalculator.calculate_meal_nutrient_targets(daily_targets, meal_type)
            else:
                meal_targets = daily_targets

            # 转换为NutritionBaseline对象
            return NutritionBaseline(
                calories=meal_targets.get('calories', 0),
                protein_g=meal_targets.get('protein', 0),
                fat_g=meal_targets.get('fat', 0),
                carbs_g=meal_targets.get('carbohydrate', 0),
                bmr=daily_targets.get('calories', 0),  # 每日热量就是BMR
                tdee=daily_targets.get('calories', 0)  # 基础情况下TDEE=BMR
            )

        except Exception as e:
            print(f"使用共用计算器失败，使用原有逻辑: {str(e)}")

    def _calculate_nutrient_from_rdi(self, rdi_data: Dict, nutrient: str, weight_kg: float) -> float:
        """根据RDI计算营养素基准"""
        rdi = rdi_data.get(nutrient)
        if not rdi:
            # 默认计算
            return round(weight_kg * 1.2 * 10) / 10

        amount = weight_kg * rdi['amount']  # 蛋白质按体重计算
        return round(amount * 10) / 10

    def _calculate_fat_from_rdi(self, rdi_data: Dict, bmr: float) -> float:
        """计算脂肪基准"""
        fat_rdi = rdi_data.get('fat', {'amount': 0.25})
        fat_calories = bmr * fat_rdi['amount']
        return round((fat_calories / 9) * 10) / 10

    def _calculate_carbs_from_rdi(self, rdi_data: Dict, bmr: float) -> float:
        """计算碳水基准"""
        carbs_rdi = rdi_data.get('carbohydrate', {'amount': 0.55})
        carbs_calories = bmr * carbs_rdi['amount']
        return round((carbs_calories / 4) * 10) / 10

    def calculate_differences(self, intake: NutritionAnalysisInput,
                              baseline: NutritionBaseline) -> NutritionDifferences:
        """计算营养差异"""
        absolute_diffs = {
            'calories': round(intake.calories_intake - baseline.calories, 1),
            'protein_g': round(intake.protein_g - baseline.protein_g, 1),
            'fat_g': round(intake.fat_g - baseline.fat_g, 1),
            'carbs_g': round(intake.carbs_g - baseline.carbs_g, 1)
        }

        def calculate_ratio(nutrient_g: float, calories: float, nutrient_type: str) -> float:
            kcal_per_g = 9 if nutrient_type == 'fat' else 4
            return (nutrient_g * kcal_per_g) / calories if calories > 0 else 0

        actual_ratios = {
            'protein': calculate_ratio(intake.protein_g, intake.calories_intake, 'protein'),
            'fat': calculate_ratio(intake.fat_g, intake.calories_intake, 'fat'),
            'carbs': calculate_ratio(intake.carbs_g, intake.calories_intake, 'carbs')
        }

        baseline_ratios = {
            'protein': calculate_ratio(baseline.protein_g, baseline.calories, 'protein'),
            'fat': calculate_ratio(baseline.fat_g, baseline.calories, 'fat'),
            'carbs': calculate_ratio(baseline.carbs_g, baseline.calories, 'carbs')
        }

        ratio_diffs = {}
        for nutrient in ['protein', 'fat', 'carbs']:
            ratio_diffs[nutrient] = actual_ratios[nutrient] - baseline_ratios[nutrient]

        return NutritionDifferences(
            absolute=absolute_diffs,
            ratios=ratio_diffs,
            actual_ratios=actual_ratios,
            baseline_ratios=baseline_ratios
        )

    def predict_weight_shift_advanced(self, differences: NutritionDifferences,
                                      user_input: NutritionAnalysisInput, days: int = 90) -> WeightPrediction:
        """预测体重变化"""
        # 计算高级BMR
        advanced_bmr = self.nutrition_data.calculate_advanced_bmr(
            user_input.height_cm, user_input.weight_kg, user_input.age,
            user_input.gender, user_input.ageGroup
        )

        # 计算运动消耗
        exercise_ee = self.nutrition_data.calculate_exercise_energy_expenditure(advanced_bmr, {
            'frequency': user_input.exerciseFrequency,
            'duration': user_input.exerciseDuration,
            'intensity': user_input.exerciseIntensity
        })

        # 计算总能量消耗
        tdee = advanced_bmr + exercise_ee

        # 热量差值计算
        daily_calorie_diff = differences.absolute['calories'] - tdee
        total_calorie_surplus = daily_calorie_diff * days

        # 基础体重变化
        base_weight_shift = total_calorie_surplus / NutritionData.PATENTED_CONFIG['kcal_per_kg_fat']

        # 营养协同效应调整
        synergy_score = self.nutrition_data.calculate_nutrient_synergy(
            differences.actual_ratios['protein'],
            differences.actual_ratios['fat'],
            differences.actual_ratios['carbs'],
            user_input.ageGroup
        )

        # 代谢适应性调整
        metabolic_adaptation = self.nutrition_data.predict_metabolic_adaptation(
            user_input.weight_kg, base_weight_shift, days, user_input.ageGroup
        )

        # 最终体重变化
        adjusted_weight_shift = (base_weight_shift * synergy_score *
                                 NutritionData.PATENTED_CONFIG['NUTRIENT_SYNERGY_MULTIPLIER'] *
                                 (1 - metabolic_adaptation))

        # 体成分预测
        body_comp = self.nutrition_data.predict_body_composition_advanced(
            differences.ratios, adjusted_weight_shift, user_input.weight_kg,
            user_input.gender, user_input.ageGroup, {
                'frequency': user_input.exerciseFrequency,
                'duration': user_input.exerciseDuration,
                'intensity': user_input.exerciseIntensity
            }
        )

        new_weight = user_input.weight_kg + adjusted_weight_shift

        return WeightPrediction(
            weight_shift_kg=round(adjusted_weight_shift, 2),
            new_weight_kg=round(new_weight, 1),
            fat_shift_kg=round(body_comp['fat_shift'], 2),
            muscle_shift_kg=round(body_comp['muscle_shift'], 2),
            muscle_ratio=round(body_comp['muscle_ratio'], 3),
            optimization_score=round(body_comp['optimization_score'] * 100),
            synergy_score=round(synergy_score * 100),
            metabolic_adaptation=round(metabolic_adaptation * 100),
            advanced_bmr=round(advanced_bmr),
            exercise_energy=round(exercise_ee),
            total_tdee=round(tdee),
            timeframe_days=days
        )

    def predict_future_body_image(self, user_input: NutritionAnalysisInput,
                                  predicted_weight_shift: float) -> BodyImagePrediction:
        """预测未来身材图片"""
        current_body = self.nutrition_data.get_body_image_type(
            user_input.height_cm, user_input.weight_kg, user_input.gender
        )
        future_body = self.nutrition_data.get_body_image_type(
            user_input.height_cm, user_input.weight_kg + predicted_weight_shift, user_input.gender
        )

        return BodyImagePrediction(
            current=current_body,
            future=future_body,
            weight_change=predicted_weight_shift
        )

    def analyze(self, users_input: List[Dict], days: int = None, meal_type: str = 'all') -> List[NutritionAnalysisResult]:
        """主营养分析方法"""
        if not days:
            days = 90  # 默认90天

        results = []

        for user_data in users_input:
            # 转换为输入模型
            user_input = NutritionAnalysisInput(**user_data)

            baseline = self.calculate_baseline(user_input, meal_type)
            differences = self.calculate_differences(user_input, baseline)
            prediction = self.predict_weight_shift_advanced(differences, user_input, days)
            body_image = self.predict_future_body_image(user_input, prediction.weight_shift_kg)

            results.append(NutritionAnalysisResult(
                user_input=user_input,
                baseline=baseline,
                differences=differences,
                prediction=prediction,
                body_image=body_image
            ))

        return results


# ------------- API路由 -------------

@nutrition_bp.route("/analyze", methods=["POST"])
def analyze_nutrition():
    """营养分析接口"""
    try:
        data = request.get_json()
        users_input = data.get('users', [])
        days = data.get('days', 90)
        meal_type = data.get('mealType','all')

        analyzer = NutritionAnalyzer()
        results = analyzer.analyze(users_input, days, meal_type)

        # 转换为字典返回
        return jsonify({
            'success': True,
            'results': [result.__dict__ for result in results]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@nutrition_bp.route("/calculate-ratios", methods=["POST"])
def calculate_nutrition_ratios():
    """批量计算用户营养分配比例"""
    try:
        data = request.get_json()
        active_members = data.get('active_members', [])
        all_users = data.get('all_users', [])

        if not active_members:
            return jsonify({'success': False, 'error': '活跃用户数据缺失'}), 400

        # 计算每个活跃用户的比例
        ratios = {}
        for user in active_members:
            ratio = _calculate_user_nutrition_ratio(user, all_users)
            ratios[user.get('member_id')] = ratio

        return jsonify({
            'success': True,
            'ratios': ratios
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _calculate_user_nutrition_ratio(user: Dict, all_users: List[Dict]) -> float:
    """计算用户营养分配比例 - 基于 TDEE + 年龄修正"""
    # 基础信息
    weight = float(user.get('weight_kg', 65))
    height = float(user.get('height_cm', 170))
    age = int(float(user.get('age', 30)))
    gender = user.get('gender', 'male')
    age_group = user.get('ageGroup', 'middle')

    # 计算 BMR
    nutrition_data = NutritionData()
    bmr = nutrition_data.calculate_advanced_bmr(height, weight, age, gender, age_group)

    # PAL（活动系数）映射
    pal_map = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'athlete': 1.9
    }
    pal = pal_map.get(user.get('exerciseFrequency', 'moderate'), 1.55)

    # 运动额外消耗
    duration_map = {'short': 15, 'medium': 30, 'long': 45, 'extended': 60}
    intensity_map = {'low': 3, 'medium': 5, 'high': 7, 'veryHigh': 9}

    mins = duration_map.get(user.get('exerciseDuration', 'medium'), 30)
    mets = intensity_map.get(user.get('exerciseIntensity', 'medium'), 5)
    exercise_kcal = (mets * weight * (mins / 60)) if mets and weight else 0

    # TDEE
    tdee = bmr * pal + exercise_kcal

    # 年龄修正
    if age < 6:
        tdee *= 1.2  # 生长高峰
    if age >= 65:
        tdee *= 0.9  # 食欲下降

    # 全家总 TDEE
    total_tdee = 0
    for u in all_users:
        u_weight = float(u.get('weight_kg', 65))
        u_height = float(u.get('height_cm', 170))
        u_age = int(float(u.get('age', 30)))
        u_gender = u.get('gender', 'male')
        u_age_group = u.get('ageGroup', 'middle')

        u_bmr = nutrition_data.calculate_advanced_bmr(u_height, u_weight, u_age, u_gender, u_age_group)
        u_pal = pal_map.get(u.get('exerciseFrequency', 'moderate'), 1.55)

        u_mins = duration_map.get(u.get('exerciseDuration', 'medium'), 30)
        u_mets = intensity_map.get(u.get('exerciseIntensity', 'medium'), 5)
        u_exercise = (u_mets * u_weight * (u_mins / 60)) if u_mets and u_weight else 0

        u_tdee = u_bmr * u_pal + u_exercise

        if u_age < 6:
            u_tdee *= 1.2
        if u_age >= 65:
            u_tdee *= 0.9

        total_tdee += u_tdee

    # 比例
    return tdee / total_tdee if total_tdee > 0 else 1 / len(all_users)