# smart_demo.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
import random
from datetime import date, timedelta

# ---------------- 数据定义 ----------------
@dataclass
class RecommendationConfig:
    medical_strict: float = 1.0          # 1=严格，0=宽松
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
class UserSnapshot:
    uid: str
    level: str                               # 等级
    daily_targets: Dict[str, float]
    hard_caps: Dict[str, float]
    gene_weights: Dict[str, float]
    micro_weights: Dict[str, float]
    recent_ids: List[str]                    # 最近 N 天已吃
    cfg: RecommendationConfig

@dataclass
class Context:
    date: date
    stock: Dict[str, float]
    max_cook_time: int

@dataclass
class Dish:
    dish_id: str
    name: str
    nutrients: Dict[str, float]
    tags: List[str]
    ingredients: Dict[str, float]
    cook_time: int
    popularity: float          # 0-5

# ---------------- 模拟数据 ----------------
DISH_POOL = [
    Dish("d001", "奶酪焗鸡胸", {"calcium": 300, "sodium": 800}, ["high_calcium"], {"chicken": 200, "cheese": 50}, 20, 4.5),
    Dish("d002", "清炒西兰花", {"calcium": 150, "sodium": 100}, ["low_sodium"], {"broccoli": 150}, 10, 4.2),
    Dish("d003", "麻辣香锅", {"calcium": 50, "sodium": 2000}, ["spicy"], {"mixed": 300}, 25, 4.0),
    Dish("d004", "芝士焗土豆", {"calcium": 400, "sodium": 300}, ["high_calcium"], {"potato": 200, "cheese": 80}, 18, 4.6),
    Dish("d005", "蒸南瓜", {"calcium": 30, "sodium": 50}, ["low_sodium"], {"pumpkin": 200}, 12, 3.9),
    Dish("d006", "豆腐海带汤", {"calcium": 200, "sodium": 400}, ["high_calcium", "low_gi"], {"tofu": 100, "seaweed": 30}, 15, 4.3)
]

# ---------------- 等级默认配置 ----------------
LEVEL_CFG = {
    "bronze": RecommendationConfig(
        medical_strict=0.5,
        gene_weight_scale=0.8,
        novelty_power=0.5,
        surprise_scale=0.6,
        epsilon_greedy=0.3
    ),
    "silver": RecommendationConfig(
        medical_strict=0.8,
        gene_weight_scale=1.2,
        novelty_power=1.0,
        surprise_scale=0.3,
        epsilon_greedy=0.15
    ),
    "gold": RecommendationConfig(
        medical_strict=1.0,
        gene_weight_scale=1.8,
        novelty_power=1.5,
        surprise_scale=0.1,
        epsilon_greedy=0.05
    )
}

# ---------------- 推荐引擎 ----------------
class ConfigRecommender:
    @staticmethod
    def _medical_score(dish: Dish, targets: Dict[str, float], caps: Dict[str, float], cfg: RecommendationConfig) -> float:
        score = 1.0
        for k, v in dish.nutrients.items():
            if k in caps and v > caps[k]:
                return 0.0 if cfg.medical_strict >= 1.0 else 0.5
            if k in targets and targets[k] > 0:
                score *= min(v / targets[k], 1.0) + 1e-3
        return score

    @staticmethod
    def _personal_score(dish: Dish, gene_w: Dict[str, float], micro_w: Dict[str, float], cfg: RecommendationConfig) -> float:
        g = sum(cfg.gene_weight_scale * gene_w.get(t, 1.0) for t in dish.tags)
        m = sum(cfg.micro_weight_scale * micro_w.get(t, 1.0) for t in dish.tags)
        return (g + m) / max(len(dish.tags), 1)

    @staticmethod
    def recommend(user: UserSnapshot, dishes: List[Dish], k: int = 3) -> List[Dish]:
        recent = set(user.recent_ids)
        scored = []
        for d in dishes:
            if d.dish_id in recent:
                continue
            med = ConfigRecommender._medical_score(d, user.daily_targets, user.hard_caps, user.cfg)
            pers = ConfigRecommender._personal_score(d, user.gene_weights, user.micro_weights, user.cfg)
            novelty = 1 / (1 + random.randint(1, 15)) ** user.cfg.novelty_power
            explore = user.cfg.surprise_scale * random.random()
            score = med * pers * novelty + explore
            scored.append((d, score))

        # ε-Greedy 选择
        chosen = []
        scored.sort(key=lambda x: -x[1])
        pool = [d for d, _ in scored]
        for _ in range(min(k, len(pool))):
            if random.random() < user.cfg.epsilon_greedy:
                d = random.choice(pool)
            else:
                d = max(pool, key=lambda d: next(s for dish, s in scored if dish == d))
            chosen.append(d)
            pool.remove(d)
        return chosen

# ---------------- Demo 运行 ----------------
def demo():
    targets = {"calcium": 800}
    caps = {"sodium": 1500}
    gene = {"high_calcium": 1.2}
    micro = {"low_gi": 1.1}

    for level in ["bronze", "silver", "gold"]:
        user = UserSnapshot(
            uid=f"u_{level}",
            level=level,
            daily_targets=targets,
            hard_caps=caps,
            gene_weights=gene,
            micro_weights=micro,
            recent_ids=["d003"],  # 假设刚吃过麻辣香锅
            cfg=LEVEL_CFG[level]
        )
        result = ConfigRecommender.recommend(user, DISH_POOL, k=3)
        names = [d.name for d in result]
        print(f"{level.upper():>5} 用户推荐: {names}")

if __name__ == "__main__":
    demo()