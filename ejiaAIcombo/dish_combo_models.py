# dish_combo_models.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ComboConfig:
    # 菜品数量配置
    base_dish_count: int = 3
    dish_per_adult: int = 1
    dish_per_child: int = 1
    toddler_extra_dish: int = 1

    # 份量配置
    portion_adult: str = "L"
    portion_child: str = "M"
    portion_toddler: str = "S"
    portion_ratios: Dict[str, float] = field(default_factory=lambda: {"S": 0.5, "M": 1.0, "L": 1.5})

    # 烹饪时间配置（分钟）
    cook_time_breakfast: int = 15
    cook_time_lunch: int = 30
    cook_time_dinner: int = 45
    cook_time_all: int = 30

    # 营养配置
    nutrient_tolerance: float = 0.05
    include_allergens: bool = True

    # 各餐型营养分配比例
    nutrient_ratio_breakfast: float = 0.3  # 早餐30%
    nutrient_ratio_lunch: float = 0.4      # 午餐40%
    nutrient_ratio_dinner: float = 0.3     # 晚餐30%
    nutrient_ratio_single: float = 1.0     # 单餐100%

@dataclass
class MemberInfo:
    member_id: int
    age: float
    gender: str
    height_cm: int
    weight_kg: float


@dataclass
class Dish:
    dish_id: int
    name: str
    nutrients: Dict[str, float]
    ingredients: Dict[str, float]
    cook_time: int
    allergens: List[str] = field(default_factory=list)
    portion_ratio: float = 1.0
    matched_needs: List[str] = field(default_factory=list)
    match_score: float = 0.0
    portion_size: str = "M"  # 新增：份量规格


@dataclass
class ComboMeal:
    combo_id: int
    combo_name: str
    need_codes: List[str]
    meal_type: str
    dishes: List[Dish]
    total_cook_time: int = 0  # 新增：总烹饪时间
    portion_plan: Dict[str, List[str]] = field(default_factory=dict)  # 新增：份量分配方案
