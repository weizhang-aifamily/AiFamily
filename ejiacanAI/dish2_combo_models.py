# dish_combo_models.py
from __future__ import annotations

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
@dataclass
class MealRequest:
    """
    唯一入口参数，所有外部信息由此传入。
    字段保持最小化，后续可扩展。
    """
    member_ids: List[int]
    meal_type: str = "all"          # breakfast / lunch / dinner / all
    refresh_key: int = 0            # 用于随机洗牌
    max_dishes_per_meal: int = 0    # 0 表示自动计算
    cook_time_limit: int = 30       # 分钟
    deficit_kcal: int = 0           # 热量缺口

@dataclass
class ExactPortion:
    """
    精确份量：外壳 S/M/L + 内部克数
    """
    size: str           # S / M / L
    grams: int          # 实际克数

@dataclass
class Dish:
    dish_id: int
    name: str
    cook_time: int
    ingredients: Dict[str, float]   # 食材 -> 克数（已累加重量）
    nutrients: Dict[str, float]     # 营养素 -> 克数
    exact_portion: ExactPortion
    allergens: List[str]
    # 选菜用的标签
    explicit_tags: List[str]        # need-dish 显性标签
    implicit_tags: List[str]        # dish_category 隐性标签

@dataclass
class ComboMeal:
    combo_id: int
    combo_name: str
    need_codes: List[str]
    meal_type: str
    dishes: List[Dish]
    total_cook_time: int = 0  # 新增：总烹饪时间
    portion_plan: Dict[str, List[str]] = field(default_factory=dict)  # 新增：份量分配方案
    shopping_list: Dict[str, float] = field(default_factory=dict)

@dataclass
class DishFoodNutrient:
    """
    对应 v2_dish_food_nutrient 一行
    """
    dish_id: int
    dish_name: str
    dish_emoji: Optional[str]
    dish_description: Optional[str]
    dish_rating: Optional[float]
    dish_default_portion_g: int
    dish_cook_time: int
    dish_meal_type_code: Optional[str]
    dish_meal_type_name: Optional[str]
    category_id: Optional[int]
    category_name: Optional[str]
    category_match_score: Optional[float]
    food_id: int
    food_amount_in_dish_g: int
    food_description: str
    food_data_type: Optional[str]
    food_publication_date: Optional[str]
    portion_id: Optional[int]
    portion_seq: Optional[int]
    portion_amount: Optional[float]
    portion_unit_id: Optional[int]
    portion_modifier: Optional[str]
    portion_gram_weight: Optional[float]
    nutrient_id: int
    nutrient_name: str
    nutrient_name_cn: str
    nutrient_unit: str
    nutrient_order: int
    nutrient_per_100g: float
    nutrient_in_dish: float          # 已乘 food_amount_in_dish_g
    allergen_list: Optional[str]     # GROUP_CONCAT 结果
    explicit_tags: str = ""
    implicit_tags: str = ""


@dataclass
class MemberNeedNutrient:
    """
    对应 v2_member_need_nutrient 一行
    """
    member_id: int
    member_need_id: int
    need_type: Optional[str]
    need_code: str
    offset_val: Optional[float]
    need_name: Optional[str]
    icon: Optional[str]
    desc_text: Optional[str]
    checkup_id: Optional[int]
    goal_id: Optional[int]
    is_external: int
    nutrient_name: str
    name_cn: str
    unit_name: str
    nutrient_nbr: Optional[str]
    order_rank: int
    actual_id: Optional[int]
    nutrient_code: Optional[str]
    need_qty: Optional[float]
    min_need_qty: Optional[float]
    max_need_qty: Optional[float]
    updated_at: Optional[str]