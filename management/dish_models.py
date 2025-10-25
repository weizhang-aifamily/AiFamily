from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
@dataclass
class DishListItem:
    """页面1列表行模型，仅含展示字段。"""
    dish_id: int
    name: str
    rating: Optional[float]
    dish_cook_time: int
    tags: Optional[str]
    need_tags: Optional[str]

@dataclass
class DishPage2SaveCmd:
    """页面2保存入参"""
    dish_id: int
    category_id: Optional[int]
    category_match_score: Optional[float]
    series_id: Optional[int]
    tag_id: Optional[int]
    meal_type: Optional[str]

@dataclass
class NutrientRule:
    """一条需求标签判定规则"""
    id: int
    need_code: str
    nutrient: str          # 英文列名，用于映射
    comparison_operator: str    # ">=", "<=" 等
    threshold_value: float
    unit: str


@dataclass
class DishNutrientTotal:
    """菜品维度各营养素合计（每 100 g 可食部）"""
    dish_id: int
    nutrient_map: Dict[str, float]  # key 为 nutrient_name，value 为合计值