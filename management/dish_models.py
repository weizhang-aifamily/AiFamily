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

@dataclass
class DishPage2SaveCmd:
    """页面2保存入参"""
    dish_id: int
    category_id: Optional[int]
    category_match_score: Optional[float]
    series_id: Optional[int]
    tag_id: Optional[int]
    meal_type: Optional[str]