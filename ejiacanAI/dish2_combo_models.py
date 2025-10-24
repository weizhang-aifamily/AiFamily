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
    # 北方省份：面食为主，汤较少
    'BJ': {'staple': 1.2, 'soup': 0.8},  # 北京
    'SD': {'staple': 1.3, 'soup': 0.7},  # 山东
    'HE': {'staple': 1.2, 'soup': 0.8},  # 河北
    # 南方省份：米饭为主，汤较多
    'GD': {'staple': 1.0, 'soup': 1.5},  # 广东
    'FJ': {'staple': 1.0, 'soup': 1.4},  # 福建
    'ZJ': {'staple': 1.0, 'soup': 1.3},  # 浙江
    # 西南省份：辣味主菜较多
    'SC': {'main_dish': 1.3, 'side_dish': 1.2},  # 四川
    'CQ': {'main_dish': 1.4, 'side_dish': 1.1},  # 重庆
    'HN': {'main_dish': 1.2, 'side_dish': 1.1},  # 湖南
    """
    member_ids: List[int] = None
    keyword: str = None
    members: List[Dict] = None
    province_code: str = 'default'  # 省份代码
    meal_type: str = "all"          # breakfast / lunch / dinner / all
    refresh_key: int = 0            # 用于随机洗牌
    max_dishes_per_meal: int = 0    # 0 表示自动计算
    cook_time_limit: int = 30       # 分钟
    deficit_kcal: int = 0           # 热量缺口
    explicit_tags: List[str] = field(default_factory=list)  # 标签
    implicit_tags: List[str] = field(default_factory=list)  # 分类
    dish_series: Optional[str] = None  # 菜系ID
    dish_category: Optional[str] = None # 菜品类别
    want_eat: Optional[str] = None  # 逗号或空格隔开的食材/菜品名称

@dataclass
class ExactPortion:
    """
    精确份量：外壳 S/M/L + 内部克数
    """
    size: str           # S / M / L
    grams: int          # 实际克数

@dataclass
class Dish1:
    dish_id: int
    name: str
    cook_time: int
    ingredients: Dict[str, float]   # 食材 -> 克数（已累加重量）
    nutrients: Dict[str, float]     # 营养素 -> 克数
    exact_portion: ExactPortion
    allergens: List[str]
    # 选菜用的标签
    explicit_tags: List[str]        # tags 显性标签，补钙、低脂、儿童餐、中辣等
    implicit_tags: List[str]        # dish_category 隐性标签 家常菜、火锅等
    dish_series: int                # 菜系
    meal_type_code: Optional[str]   # breakfast lunch dinner

@dataclass
class ComboMeal:
    combo_id: int
    combo_name: str
    meal_type: str
    dishes: List[Dish]
    total_cook_time: int = 0  # 新增：总烹饪时间
    portion_plan: Dict[str, List[str]] = field(default_factory=dict)  # 新增：份量分配方案
    meal_structure : Dict[str, Dict[str, int]] = field(default_factory=dict)
    nutrients: Dict[str, float] = field(default_factory=dict)  # 新增：营养素汇总
    need_nutrients: Dict[str, float] = field(default_factory=dict)  # 新增：目标营养素需求
    food_category_distribution: Dict[str, int] = field(default_factory=dict)

@dataclass
class DishFoodNutrient1:
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
    series_id: Optional[int]
    series_name: Optional[str]
    tag_id: Optional[int]
    tag_name: Optional[str]
    category_match_score: Optional[float]
    food_id: int
    food_amount_in_dish_g: int
    food_description: str
    food_category1: Optional[str]
    food_category2: Optional[str]
    # food_data_type: Optional[str]
    # portion_id: Optional[int]
    # portion_seq: Optional[int]
    # portion_amount: Optional[float]
    # portion_unit_id: Optional[int]
    # portion_modifier: Optional[str]
    # portion_gram_weight: Optional[float]
    # nutrient_id: int
    nutrient_name: str
    nutrient_name_cn: str
    nutrient_unit: str
    nutrient_order: int
    nutrient_per_100g: float
    nutrient_in_dish: float          # 已乘 food_amount_in_dish_g
    allergen_list: Optional[str]     # GROUP_CONCAT 结果
    explicit_tags: str = ""
    implicit_tags: str = ""
    meal_type_code: Optional[str] = None


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


# v3_dish_food_complete_view 中需要调整 DishFoodNutrient 和 Dish 模型

@dataclass
class DishFoodNutrient:
    """
    对应 dish_food_complete_view 一行
    """
    dish_id: int
    dish_name: str
    dish_emoji: Optional[str]
    dish_description: Optional[str]
    dish_rating: Optional[float]
    dish_default_portion_g: int
    dish_cook_time: int
    need_tags: str

    # 食材信息
    food_id: int
    food_amount_grams: int
    foodCode: int
    foodName: str
    category1: str
    category2: Optional[str]
    is_main_food: str

    # 营养成分信息（保持横表结构）
    edible: Optional[int]
    water: Optional[float]
    energyKCal: Optional[int]
    energyKJ: Optional[int]
    protein: Optional[float]
    fat: Optional[float]
    CHO: Optional[float]
    dietaryFiber: Optional[float]
    cholesterol: Optional[float]
    ash: Optional[float]
    vitaminA: Optional[float]
    carotene: Optional[float]
    retinol: Optional[float]
    thiamin: Optional[float]
    riboflavin: Optional[float]
    niacin: Optional[float]
    vitaminC: Optional[float]
    vitaminETotal: Optional[float]
    vitaminE1: Optional[float]
    vitaminE2: Optional[float]
    vitaminE3: Optional[float]
    Ca: Optional[float]
    P: Optional[float]
    K: Optional[float]
    Na: Optional[float]
    Mg: Optional[float]
    Fe: Optional[float]
    Zn: Optional[float]
    Se: Optional[float]
    Cu: Optional[float]
    Mn: Optional[float]
    remark: Optional[str]

    # 过敏原信息
    allergen_code: Optional[str]
    allergen_name: Optional[str]

    tags_json: Optional[str]


@dataclass
class Dish:
    dish_id: int
    dish_emoji: str
    name: str
    cook_time: int
    ingredients: List[Dict[str, str]]   # 食材名称 -> 克数
    nutrients: Dict[str, float]  # 营养素编码 -> 含量
    default_portion: int
    exact_portion: ExactPortion
    allergens: List[str]
    dish_tags: Dict[str, List[Dict[str, str]]]
    foods: List[Food] = field(default_factory=list)  # 新增：食材详细信息
    food_categories: List[str] = field(default_factory=list)  # 如 ['protein', 'vege_fruit']
    # 以下全部给默认值
    explicit_tags: List[str] = field(default_factory=list)
    implicit_tags: List[str] = field(default_factory=list)
    meal_structure_type: Dict[str, str] = None  # main_dish, selected #main_dish, alternative
    is_selected: int = None  # 1 0
    rating: Optional[float] = None
    description: Optional[str] = None

@dataclass
class Food:
    """食材信息"""
    food_id: int
    food_amount_grams: int
    foodCode: int
    foodName: str
    category1: str
    category2: Optional[str]
    is_main_food: str
    # 营养成分信息
    edible: Optional[int] = None
    water: Optional[float] = None
    energyKCal: Optional[int] = None
    energyKJ: Optional[int] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    CHO: Optional[float] = None
    dietaryFiber: Optional[float] = None
    cholesterol: Optional[float] = None
    ash: Optional[float] = None
    vitaminA: Optional[float] = None
    carotene: Optional[float] = None
    retinol: Optional[float] = None
    thiamin: Optional[float] = None
    riboflavin: Optional[float] = None
    niacin: Optional[float] = None
    vitaminC: Optional[float] = None
    vitaminETotal: Optional[float] = None
    vitaminE1: Optional[float] = None
    vitaminE2: Optional[float] = None
    vitaminE3: Optional[float] = None
    Ca: Optional[float] = None
    P: Optional[float] = None
    K: Optional[float] = None
    Na: Optional[float] = None
    Mg: Optional[float] = None
    Fe: Optional[float] = None
    Zn: Optional[float] = None
    Se: Optional[float] = None
    Cu: Optional[float] = None
    Mn: Optional[float] = None
    remark: Optional[str] = None

