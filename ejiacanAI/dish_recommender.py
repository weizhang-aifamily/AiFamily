from typing import List
from models import UserSnapshot, Context, Dish
from dish_data_access import EnhancedDataAccess   # 取数接口
import random

class DishRecommender:
    def __init__(self, data_access: EnhancedDataAccess):
        self.da = data_access

    def recommend(self, member_id: int, ctx: Context, top_k: int = 3) -> List[Dish]:
        user = self.da.get_user_snapshot(member_id)
        pool = self.da.get_dish_pool(ctx.meal_type)

        # 1) 过滤：库存 / 时间  (库存为空时全放行)
        mask = [d for d in pool
                if d.cook_time <= ctx.max_cook_time
                and (ctx.stock is None or all(d.ingredients.get(i, 0) <= ctx.stock.get(i, 0) for i in d.ingredients))]

        # 2) 计算 last_seen_days
        for d in mask:
            d.last_seen_days = 0 if d.dish_id not in user.recent_7d_dish_ids else 1   # 简化示例

        # 3) 打分 & 多样性 TopK（直接复用之前的极简实现）
        def score(d: Dish) -> float:
            med = sum(user.daily_targets.get(k, 0) and d.nutrients.get(k, 0) / user.daily_targets[k] for k in user.daily_targets)
            novelty = 1 / (1 + d.last_seen_days)
            explore = ctx.surprise_level * (0.2 if random.random() < 0.2 else 0)
            return med * novelty + explore

        scored = sorted(mask, key=score, reverse=True)[:top_k]
        return scored