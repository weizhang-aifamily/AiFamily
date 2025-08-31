# dish_combo_models.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass
class MergeConfig:
    """智能合并配置"""
    # 合并优先级配置
    merge_priority_rules: List[Tuple[str, int]] = field(default_factory=lambda: [
        ("NO_SPECIFIC_NEEDS", 1),  # 无特定需求的菜品
        ("SINGLE_NEED", 2),  # 只满足一个需求
        ("BALANCED_NEED", 3),  # 均衡营养类
        ("CORE_NEED", 4),  # 核心需求菜品
    ])

    # 合并阈值配置
    nutrient_overlap_threshold: float = 0.7  # 营养重叠度阈值
    min_similarity_for_merge: float = 0.6  # 最小相似度才合并
    max_merge_per_meal: int = 2  # 每餐最多合并次数

    # 菜品类型配置
    non_mergeable_categories: List[str] = field(default_factory=lambda: [
        "主食", "汤品", "特色菜"
    ])

    # 目标菜品数量配置（基于家庭成员数）
    target_dish_counts: Dict[int, int] = field(default_factory=lambda: {
        1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 8
    })

@dataclass
class ComboConfig:

    # 份量配置
    base_dish_count: int = 3
    dish_per_adult: int = 1
    dish_per_child: int = 1
    toddler_extra_dish: int = 1
    portion_ratios: Dict[str, float] = field(default_factory=lambda: {"S": 0.5, "M": 1.0, "L": 1.5})

    # 烹饪时间配置（分钟）
    cook_time_breakfast: int = 15
    cook_time_lunch: int = 30
    cook_time_dinner: int = 45
    cook_time_all: int = 30

    # 各餐型营养分配比例
    nutrient_ratio_breakfast: float = 0.3  # 早餐30%
    nutrient_ratio_lunch: float = 0.4      # 午餐40%
    nutrient_ratio_dinner: float = 0.3     # 晚餐30%
    nutrient_ratio_single: float = 1.0     # 单餐100%
    merge_config: MergeConfig = field(default_factory=MergeConfig)

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
