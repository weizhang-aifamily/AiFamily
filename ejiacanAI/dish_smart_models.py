# dish_smart_models.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class RecommendationConfig:
    medical_strict: float = 1.0
    gene_weight_scale: float = 1.0
    micro_weight_scale: float = 1.0
    novelty_power: float = 1.0
    surprise_scale: float = 0.0
    diversity_threshold: float = 0.8
    max_cook_time_scale: float = 1.0
    stock_tolerance: float = 0.0
    history_window_days: int = 7
    mmr_lambda: float = 0.5
    epsilon_greedy: float = 0.1
    bandit_prior_alpha: int = 1
    bandit_prior_beta: int = 1

@dataclass
class FamilyMember:
    member_id: int
    daily_targets: Dict[str, float]
    hard_caps: Dict[str, float]
    gene_weights: Dict[str, float]
    micro_weights: Dict[str, float]
    recent_7d_dish_ids: List[int]
    cfg: RecommendationConfig
    allergens: List[str]  # 成员过敏原
    #taboos: List[str]  # 成员忌口

@dataclass
class Dish:
    dish_id: int
    name: str
    nutrients: Dict[str, float]
    ingredients: Dict[str, float]
    cook_time: int
    popularity: float
    allergens: List[str]

class Algorithm:
    MMR = 1
    GREEDY = 2
    BANDIT = 3
