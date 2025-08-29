# dish_smart_recommender.py
import random
from typing import List
from dish_smart_models import Dish, FamilyMember, Algorithm
from dish_smart_data import DishSmartData

class DishSmartRecommender:

    # ---------- 打分 ----------
    @staticmethod
    def _score(dish: Dish, user: FamilyMember) -> float:
        # 1) 医学达标
        med = 1.0
        for k, v in dish.nutrients.items():
            target = user.daily_targets.get(k, 0)
            if target > 0:
                med *= min(v / target, 1.0) + 1e-3

        # 2) 基因/需求权重
        pers = 1.0
        for tag, w in user.gene_weights.items():
            if tag in (dish.name.lower() + str(dish.nutrients)):
                pers *= w

        # 3) 新鲜度
        novelty = 1 / (1 + (1 if dish.dish_id in user.recent_7d_dish_ids else 0)) ** user.cfg.novelty_power
        # 4) 随机扰动
        explore = user.cfg.surprise_scale * random.random()
        return med * pers * novelty + explore

    # ---------- 三种算法 ----------
    @staticmethod
    def recommend(user: FamilyMember, dishes: List[Dish], k: int = 3, algo: int = Algorithm.GREEDY) -> List[Dish]:
        pool = [d for d in dishes if d.dish_id not in user.recent_7d_dish_ids]
        if not pool:
            return []

        if algo == Algorithm.MMR:
            return sorted(pool, key=lambda d: DishSmartRecommender._score(d, user), reverse=True)[:k]

        if algo == Algorithm.GREEDY:
            chosen = []
            for _ in range(min(k, len(pool))):
                if random.random() < user.cfg.epsilon_greedy:
                    d = random.choice(pool)
                else:
                    d = max(pool, key=lambda x: DishSmartRecommender._score(x, user))
                chosen.append(d)
                pool.remove(d)
            return chosen

        if algo == Algorithm.BANDIT:
            # 简化：随机 beta 采样
            chosen = []
            for _ in range(min(k, len(pool))):
                d = max(pool, key=lambda x: random.betavariate(user.cfg.bandit_prior_alpha,
                                                               user.cfg.bandit_prior_beta))
                chosen.append(d)
                pool.remove(d)
            return chosen
        return []

# ---------------- 运行示例 ----------------
if __name__ == "__main__":
    from dish_smart_models import RecommendationConfig

    # 模拟配置
    #cfg = RecommendationConfig(epsilon_greedy=0.2, novelty_power=1.2)
    # 取数据库配置
    member_id = 3
    grade_code = DishSmartData.get_user_grade(member_id)
    cfg = DishSmartData.get_grade_config(grade_code)
    user = DishSmartData.get_user_snapshot(member_id=1, cfg=cfg)
    dishes = DishSmartData.get_dish_pool(meal_type='lunch')

    res = DishSmartRecommender.recommend(user, dishes, k=3, algo=2)
    print("推荐菜品：", [d.name for d in res])