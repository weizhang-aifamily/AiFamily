from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any

@dataclass
class NutritionAnalysisInput:
    """营养分析输入数据"""
    id: str
    name: str
    gender: str
    age: int
    ageGroup: str
    height_cm: float
    weight_kg: float
    calories_intake: float
    protein_g: float
    fat_g: float
    carbs_g: float
    exerciseFrequency: str
    exerciseDuration: str
    exerciseIntensity: str

@dataclass
class NutritionBaseline:
    """营养基准数据"""
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float
    bmr: float
    tdee: float

@dataclass
class NutritionDifferences:
    """营养差异数据"""
    absolute: Dict[str, float]
    ratios: Dict[str, float]
    actual_ratios: Dict[str, float]
    baseline_ratios: Dict[str, float]

@dataclass
class WeightPrediction:
    """体重预测结果"""
    weight_shift_kg: float
    new_weight_kg: float
    fat_shift_kg: float
    muscle_shift_kg: float
    muscle_ratio: float
    optimization_score: float
    synergy_score: float
    metabolic_adaptation: float
    advanced_bmr: float
    exercise_energy: float
    total_tdee: float
    timeframe_days: int

@dataclass
class BodyImagePrediction:
    """身材图片预测"""
    current: Dict[str, Any]
    future: Dict[str, Any]
    weight_change: float

@dataclass
class NutritionAnalysisResult:
    """营养分析完整结果"""
    user_input: NutritionAnalysisInput
    baseline: NutritionBaseline
    differences: NutritionDifferences
    prediction: WeightPrediction
    body_image: BodyImagePrediction
    patent_algorithm_version: str = "1.0"

@dataclass
class NutrientRDI:
    """营养素推荐摄入量"""
    age_min: int
    age_max: int
    gender: str
    nutrient: str
    amount: float
    unit: str
    reference: str