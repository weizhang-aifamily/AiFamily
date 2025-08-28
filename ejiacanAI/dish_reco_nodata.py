# menu_recommender.py
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple
from datetime import date, timedelta

# ---------------- 数据定义 ----------------
@dataclass
class UserSnapshot:
    uid: str
    daily_targets: Dict[str, float]          # 每日目标
    hard_caps: Dict[str, float]              # 硬性上限
    gene_weights: Dict[str, float]           # SNP 权重
    microbiome_weights: Dict[str, float]     # 菌属权重
    recent_7d_ids: List[str]                 # 最近 7 天吃过的 dish_id

@dataclass
class Context:
    date: date                               # 当天日期
    meal_type: str                           # breakfast / lunch / dinner / snack
    stock: Dict[str, float]                  # 库存食材(g)
    max_cook_time: int                       # 最大可接受烹饪时间(min)
    surprise_level: float                    # 0-1 前端滑块

@dataclass
class Dish:
    dish_id: str
    nutrients: Dict[str, float]              # 每道菜的营养素
    tags: List[str]                          # 标签
    ingredients: Dict[str, float]            # 所需食材(g)
    cook_time: int
    popularity: float
    last_seen_days: int                      # 距上次被该用户做的天数

# ---------------- 核心算法 ----------------
def medical_fit(dish: Dish, targets: Dict[str, float], caps: Dict[str, float]) -> float:
    """医学级约束打分：越接近目标越好，越靠近上限越差"""
    score = 1.0
    for k, v in dish.nutrients.items():
        if k in caps and v > caps[k]:
            return 0.0  # 直接淘汰
        if k in targets and targets[k] > 0:
            score *= min(v / targets[k], 1.0) + 1e-3
    return score

def personal_fit(dish: Dish, gene_w: Dict[str, float], micro_w: Dict[str, float]) -> float:
    """基因 & 肠菌加权"""
    score = 1.0
    for tag, w in gene_w.items():
        if tag in dish.tags:
            score *= w
    for tag, w in micro_w.items():
        if tag in dish.tags:
            score *= w
    return score

def diversity_pick(k: int, scored: List[Tuple[Dish, float]], recent: List[str]) -> List[Dish]:
    """简单多样性打散：主料哈希去重"""
    seen_main = set()
    picked = []
    for dish, _ in sorted(scored, key=lambda x: -x[1]):
        main = list(dish.ingredients.keys())[0]  # 拿第一个主料当代表
        if main not in seen_main and dish.dish_id not in recent:
            picked.append(dish)
            seen_main.add(main)
        if len(picked) == k:
            break
    return picked

def TopMenu(user: UserSnapshot, ctx: Context, pool: List[Dish], top_k: int = 3) -> List[Dish]:
    # 1. 过滤库存 & 时间
    mask = [d for d in pool
            if d.cook_time <= ctx.max_cook_time
            and all(d.ingredients.get(i, 0) <= ctx.stock.get(i, 0) for i in d.ingredients)]

    # 2. 打分
    scored = []
    for d in mask:
        med = medical_fit(d, user.daily_targets, user.hard_caps)
        if med == 0.0:
            continue
        pers = personal_fit(d, user.gene_weights, user.microbiome_weights)
        novelty = 1 / (1 + d.last_seen_days)
        explore = ctx.surprise_level * random.random()
        score = med * pers * novelty + explore
        scored.append((d, score))

    # 3. 多样性 TopK
    return diversity_pick(top_k, scored, user.recent_7d_ids)

# ---------------- Demo 模拟 ----------------
def demo():
    # 构造假数据
    user = UserSnapshot(
        uid="u123",
        daily_targets={"calcium": 800, "carbs": 130},
        hard_caps={"sodium": 2000},
        gene_weights={"high_calcium": 1.2},
        microbiome_weights={"low_gi": 1.1},
        recent_7d_ids=["d001"]
    )

    ctx = Context(
        date=date.today(),
        meal_type="dinner",
        stock={"chicken": 300, "broccoli": 200, "cheese": 100},
        max_cook_time=25,
        surprise_level=0.3
    )

    pool = [
        Dish("d001", {"calcium": 300, "carbs": 40, "sodium": 800}, ["high_calcium"],
             {"chicken": 200, "cheese": 50}, 20, 4.5, 2),
        Dish("d002", {"calcium": 600, "carbs": 20, "sodium": 400}, ["high_calcium", "low_gi"],
             {"broccoli": 150, "cheese": 80}, 22, 4.7, 10),
        Dish("d003", {"calcium": 100, "carbs": 60, "sodium": 1500}, [],
             {"chicken": 250}, 15, 4.1, 5)
    ]

    result = TopMenu(user, ctx, pool, top_k=2)
    for d in result:
        print(f"推荐: {d.dish_id} —— 主料: {list(d.ingredients.keys())[0]} "
              f"钙: {d.nutrients['calcium']}mg 烹饪: {d.cook_time}min")

if __name__ == "__main__":
    demo()