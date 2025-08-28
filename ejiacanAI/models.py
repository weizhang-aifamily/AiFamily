from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class Dish:
    id: int
    name: str
    emoji: str
    default_portion_g: float
    max_servings: int
    calcium: float
    iron: float
    sodium: float
    purine: float
    kcal: float
    fat: float = 0.0
    protein: float = 0.0
    fiber: float = 0.0
    tags: List[str] = field(default_factory=list)

@dataclass
class FamilyNeed:
    calcium_target: float
    iron_target: float
    sodium_limit: float
    purine_limit: float
    kcal_limit: float
    protein_target: float = 0.0
    fiber_target: float = 0.0

@dataclass
class RecommendationConfig:
    min_match_score: float = 0.6
    max_recommendations: int = 20
    diversity_weight: float = 0.3
    popularity_weight: float = 0.2
    rating_weight: float = 0.2
    need_match_weight: float = 0.3

@dataclass
class MemberConstraints:
    allergy_member_ids: List[int] = field(default_factory=list)
    diet_taboos: List[str] = field(default_factory=list)
    taste_preferences: List[str] = field(default_factory=list)
    cooking_ability: int = 2  # 1-简单, 2-中等, 3-复杂

@dataclass
class NeedInfo:
    member_needs: Dict[int, List[Dict]]
    all_need_codes: List[str]
    need_weights: Dict[str, float] = field(default_factory=dict)

################dish_recommender########
@dataclass
class UserSnapshot:
    member_id: int
    daily_targets: Dict[str, float]          # 营养素 -> 目标量
    hard_caps: Dict[str, float]              # 营养素 -> 上限
    gene_weights: Dict[str, float]           # 需求代码 -> 权重
    recent_7d_dish_ids: List[int]            # 最近 7 天已吃 dish_id

@dataclass
class Context:
    meal_type: str                           # breakfast/lunch/dinner/snack
    max_cook_time: int                       # 分钟
    surprise_level: float                    # 0-1 滑块
    stock: Dict[str, float] | None = None    # 可选库存，None=全放行

@dataclass
class Dish:
    dish_id: int
    name: str
    nutrients: Dict[str, float]              # 每 100 g 含量
    ingredients: Dict[str, float]            # 食材 -> 克
    cook_time: int
    last_seen_days: int                      # 距用户上次吃这道菜的天数