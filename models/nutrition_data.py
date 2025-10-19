from typing import List, Dict, Optional, Any
from dbconnect.dbconn import db
from models.nutrition_models import NutrientRDI, NutritionAnalysisInput


class NutritionData:
    """营养数据分析类"""

    # 专利核心参数
    PATENTED_CONFIG = {
        'METABOLIC_ADAPTATION_FACTOR': 0.15,
        'NUTRIENT_SYNERGY_MULTIPLIER': 1.25,
        'AGE_RELATED_DECLINE_CURVE': 0.002,
        'EXERCISE_EFFICIENCY_INDEX': 0.85,
        'BODY_COMPOSITION_OPTIMIZER': 0.72,
        'kcal_per_kg_fat': 7700
    }

    # BMI标准定义
    BMI_STANDARDS = {
        'male': {
            1: {  # 偏偏瘦
                'name': '偏偏瘦',
                'bmi_range': [0, 18.4],
                'description': '体重过轻，需要增加营养',
                'image_path': 'images/mbody/very_thin.png'
            },
            2: {  # 偏瘦
                'name': '偏瘦',
                'bmi_range': [18.5, 19.9],
                'description': '体重偏轻，建议适当增重',
                'image_path': 'images/mbody/thin.png'
            },
            3: {  # 标准
                'name': '标准',
                'bmi_range': [20.0, 23.9],
                'description': '健康体重，继续保持',
                'image_path': 'images/mbody/normal.png'
            },
            4: {  # 偏胖
                'name': '偏胖',
                'bmi_range': [24.0, 27.9],
                'description': '体重偏重，建议适当减重',
                'image_path': 'images/mbody/overweight.png'
            },
            5: {  # 偏偏胖
                'name': '偏偏胖',
                'bmi_range': [28.0, 100.0],
                'description': '体重过重，需要减重',
                'image_path': 'images/mbody/very_overweight.png'
            }
        },
        'female': {
            1: {  # 偏偏瘦
                'name': '偏偏瘦',
                'bmi_range': [0, 17.4],
                'description': '体重过轻，需要增加营养',
                'image_path': 'images/fbody/very_thin.png'
            },
            2: {  # 偏瘦
                'name': '偏瘦',
                'bmi_range': [17.5, 18.9],
                'description': '体重偏轻，建议适当增重',
                'image_path': 'images/fbody/thin.png'
            },
            3: {  # 标准
                'name': '标准',
                'bmi_range': [19.0, 23.9],
                'description': '健康体重，继续保持',
                'image_path': 'images/fbody/normal.png'
            },
            4: {  # 偏胖
                'name': '偏胖',
                'bmi_range': [24.0, 27.9],
                'description': '体重偏重，建议适当减重',
                'image_path': 'images/fbody/overweight.png'
            },
            5: {  # 偏偏胖
                'name': '偏偏胖',
                'bmi_range': [28.0, 100.0],
                'description': '体重过重，需要减重',
                'image_path': 'images/fbody/very_overweight.png'
            }
        }
    }

    @staticmethod
    def get_user_rdi(age: int, gender: str) -> Dict[str, Dict[str, Any]]:
        """获取用户RDI数据"""
        sql = """
            SELECT nutrient, amount, unit 
            FROM nutrient_rdi 
            WHERE age_min <= %s AND age_max >= %s 
            AND gender IN (%s, 'B')
            ORDER BY nutrient
        """

        # 转换性别格式
        db_gender = 'M' if gender == 'male' else 'F'
        results = db.query(sql, [age, age, db_gender])

        # 转换为对象格式便于使用
        rdi_map = {}
        for row in results:
            rdi_map[row['nutrient']] = {
                'amount': float(row['amount']),
                'unit': row['unit']
            }

        return rdi_map

    @staticmethod
    def get_daily_nutrient_targets_actual(member: Dict[str, Any]) -> Dict[str, float]:
        """从 ejia_member_daily_nutrient_actual 表获取成员实际营养素需求"""
        try:
            member_id = member.get('member_id')
            if not member_id:
                raise ValueError("member_id 不能为空")

            sql = """
                SELECT nutrient_code, need_qty 
                FROM ejia_member_daily_nutrient_actual 
                WHERE member_id = %s 
                ORDER BY nutrient_code
            """

            results = db.query(sql, [member_id])

            # 转换为与 calculate_daily_nutrient_targets 一致的格式
            nutrient_targets = {}
            for row in results:
                nutrient_code = row['nutrient_code']
                need_qty = float(row['need_qty']) if row['need_qty'] is not None else 0.0
                nutrient_targets[nutrient_code] = need_qty

            # 如果数据库中没有数据，返回空字典，让调用方使用计算值
            if not nutrient_targets:
                print(f"成员 {member_id} 今日无实际营养素需求数据，将使用计算值")
                return {}

            return nutrient_targets

        except Exception as e:
            print(f"获取成员实际营养素需求时出错: {str(e)}")
            # 出错时返回空字典，让调用方使用计算值
            return {}

    @staticmethod
    def calculate_bmi(height: float, weight: float) -> float:
        """计算BMI"""
        height_m = height / 100
        return weight / (height_m * height_m)

    @staticmethod
    def get_body_image_type(height: float, weight: float, gender: str) -> Dict[str, Any]:
        """获取身材图片类型"""
        bmi = NutritionData.calculate_bmi(height, weight)
        body_image_mapping = NutritionData.BMI_STANDARDS[gender]

        for type_code, config in body_image_mapping.items():
            min_bmi, max_bmi = config['bmi_range']
            if min_bmi <= bmi < max_bmi:
                return {
                    'type_code': int(type_code),
                    'type_name': config['name'],
                    'bmi': round(bmi, 1),
                    'image_path': config['image_path'],
                    'description': config['description']
                }

        # 默认返回标准体型
        return body_image_mapping[3]

    @staticmethod
    def calculate_advanced_bmr(height: float, weight: float, age: int, gender: str, age_group: str) -> float:
        """计算高级基础代谢率"""
        # 基础BMR计算
        if gender == 'male':
            base_bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            base_bmr = 10 * weight + 6.25 * height - 5 * age - 161

        # 年龄段修正因子
        age_group_factors = {
            'child': 1.15,  # 儿童新陈代谢旺盛
            'teen': 1.25,  # 青少年生长激素影响
            'young': 1.10,  # 青年代谢活跃
            'middle': 1.00,  # 中年基准
            'senior': 0.85  # 老年代谢减缓
        }

        # 性别特异性修正
        gender_specific_factors = {
            'male': 1.05,
            'female': 0.95
        }

        return base_bmr * age_group_factors.get(age_group, 1.0) * gender_specific_factors.get(gender, 1.0)

    @staticmethod
    def calculate_exercise_energy_expenditure(bmr: float, exercise_params: Dict[str, str]) -> float:
        """计算运动能量消耗"""
        frequency = exercise_params.get('frequency', 'moderate')
        duration = exercise_params.get('duration', 'medium')
        intensity = exercise_params.get('intensity', 'medium')

        # 运动频率系数
        frequency_factors = {
            'sedentary': 1.0,
            'light': 1.1,
            'moderate': 1.25,
            'active': 1.45,
            'athlete': 1.7
        }

        # 运动时长系数
        duration_factors = {
            'short': 0.8,
            'medium': 1.0,
            'long': 1.25,
            'extended': 1.5
        }

        # 运动强度系数
        intensity_factors = {
            'low': 1.2,  # MET 3-4
            'medium': 1.5,  # MET 5-6
            'high': 2.0,  # MET 7-8
            'veryHigh': 2.8  # MET 9+
        }

        return (bmr *
                frequency_factors.get(frequency, 1.25) *
                duration_factors.get(duration, 1.0) *
                intensity_factors.get(intensity, 1.5) *
                NutritionData.PATENTED_CONFIG['EXERCISE_EFFICIENCY_INDEX'])

    @staticmethod
    def calculate_nutrient_synergy(protein_ratio: float, fat_ratio: float, carbs_ratio: float, age_group: str) -> float:
        """计算营养协同效应"""
        # 不同年龄段的理想营养比例
        optimal_ratios = {
            'child': {'protein': 0.15, 'fat': 0.30, 'carbs': 0.55},
            'teen': {'protein': 0.20, 'fat': 0.25, 'carbs': 0.55},
            'young': {'protein': 0.25, 'fat': 0.25, 'carbs': 0.50},
            'middle': {'protein': 0.25, 'fat': 0.25, 'carbs': 0.50},
            'senior': {'protein': 0.30, 'fat': 0.25, 'carbs': 0.45}
        }

        optimal = optimal_ratios.get(age_group, optimal_ratios['middle'])

        # 营养偏离度计算
        protein_deviation = abs(protein_ratio - optimal['protein'])
        fat_deviation = abs(fat_ratio - optimal['fat'])
        carbs_deviation = abs(carbs_ratio - optimal['carbs'])

        # 协同效应得分
        synergy_score = 1 - (protein_deviation + fat_deviation + carbs_deviation) * 2
        return max(0.1, min(1.0, synergy_score))

    @staticmethod
    def predict_metabolic_adaptation(current_weight: float, predicted_shift: float, timeframe: int,
                                     age_group: str) -> float:
        """预测代谢适应性"""
        adaptation_factors = {
            'child': 0.6,  # 儿童代谢适应性强
            'teen': 0.7,  # 青少年适应性强
            'young': 0.8,  # 青年基准
            'middle': 0.9,  # 中年代谢适应性下降
            'senior': 1.0  # 老年代谢适应性显著下降
        }

        base_adaptation = NutritionData.PATENTED_CONFIG['METABOLIC_ADAPTATION_FACTOR']
        age_adaptation = adaptation_factors.get(age_group, 0.9)

        # 长期代谢适应公式
        time_factor = (timeframe / 30) ** 0.5  # 以30天为基准
        weight_change_factor = min(1.0, abs(predicted_shift) / current_weight * 10)

        return base_adaptation * age_adaptation * time_factor * weight_change_factor

    @staticmethod
    def predict_body_composition_advanced(ratio_diffs: Dict[str, float], total_shift: float, weight: float,
                                          gender: str, age_group: str, exercise_params: Dict[str, str]) -> Dict[
        str, float]:
        """预测体成分变化"""
        # 基于年龄和性别的基准肌肉比例
        base_ratios = {
            'male': {
                'child': 0.25, 'teen': 0.35, 'young': 0.40, 'middle': 0.35, 'senior': 0.25
            },
            'female': {
                'child': 0.20, 'teen': 0.25, 'young': 0.30, 'middle': 0.25, 'senior': 0.20
            }
        }

        base_muscle_ratio = base_ratios[gender][age_group]

        if total_shift > 0:
            # 增重模式
            if ratio_diffs.get('protein', 0) > 0.03:
                base_muscle_ratio += 0.20
            elif ratio_diffs.get('protein', 0) < -0.03:
                base_muscle_ratio -= 0.15

            # 运动强度对肌肉增长的促进
            intensity_bonus = {
                'low': 0.05, 'medium': 0.10, 'high': 0.15, 'veryHigh': 0.20
            }
            base_muscle_ratio += intensity_bonus.get(exercise_params.get('intensity', 'medium'), 0.10)
        else:
            # 减重模式
            base_muscle_ratio = base_ratios[gender][age_group] * 0.7

            # 高蛋白保护肌肉
            if ratio_diffs.get('protein', 0) > 0.03:
                base_muscle_ratio += 0.15
            elif ratio_diffs.get('protein', 0) < -0.03:
                base_muscle_ratio -= 0.10

            # 力量训练保护肌肉
            if exercise_params.get('intensity') in ['high', 'veryHigh']:
                base_muscle_ratio += 0.10

        # 专利优化器调整
        optimized_ratio = base_muscle_ratio * NutritionData.PATENTED_CONFIG['BODY_COMPOSITION_OPTIMIZER']
        muscle_ratio = max(0.1, min(0.8, optimized_ratio))

        muscle_shift = total_shift * muscle_ratio
        fat_shift = total_shift * (1 - muscle_ratio)

        return {
            'fat_shift': fat_shift,
            'muscle_shift': muscle_shift,
            'muscle_ratio': muscle_ratio,
            'optimization_score': NutritionData._calculate_optimization_score(muscle_ratio, age_group, gender)
        }

    @staticmethod
    def _calculate_optimization_score(muscle_ratio: float, age_group: str, gender: str) -> float:
        """计算体成分优化得分"""
        optimal_ratios = {
            'male': {'child': 0.3, 'teen': 0.4, 'young': 0.45, 'middle': 0.4, 'senior': 0.35},
            'female': {'child': 0.25, 'teen': 0.3, 'young': 0.35, 'middle': 0.3, 'senior': 0.25}
        }

        optimal = optimal_ratios[gender][age_group]
        return max(0.0, 1 - abs(muscle_ratio - optimal) / optimal)