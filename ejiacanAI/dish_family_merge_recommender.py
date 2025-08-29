# family_merge_recommender.py
from typing import Dict, List, Tuple
from dish_smart_recommender import DishSmartRecommender
from dish_smart_models import RecommendationConfig, FamilyMember, Dish, Algorithm
from dish_smart_data import DishSmartData

class FamilyMergeRecommender:
    """
    只做合并：把单人推荐列表 → 家庭合并列表
    """
    # ---------- 计算缺口 ----------
    @staticmethod
    def _gaps(members: str,
              per_member_dishes: Dict[int, List[Dish]]) -> Dict[int, Dict[str, float]]:
        """每人剩余缺口"""
        member_ids = [int(mid) for mid in members.split(',') if mid.strip()]
        gaps = {}
        for mid in member_ids:
            gap = DishSmartData.get_user_snapshot(mid,
                                                  RecommendationConfig()).daily_targets.copy()
            for d in per_member_dishes[mid]:
                for n, v in d.nutrients.items():
                    gap[n] = gap.get(n, 0) - v
            gaps[mid] = {k: max(v, 0) for k, v in gap.items()}
        return gaps

    # ---------- 合并算法 ----------
    @staticmethod
    def merge(members: str,
              meal_type: str,
              max_dishes: int = 5) -> List[Dish]:
        # 1) 先做单成员推荐（每人 k=10，不过滤过敏）
        member_ids = [int(mid) for mid in members.split(',') if mid.strip()]
        single = {}
        family_members = {}
        for mid in member_ids:
            dishes = DishSmartData.get_dish_pool(meal_type)
            family_member = DishSmartData.get_user_snapshot(mid, RecommendationConfig())
            family_members[mid] = family_member
            single[mid] = DishSmartRecommender.recommend(
                family_member,
                dishes,
                k=10,
                algo=Algorithm.GREEDY
            )

        # 2) 所有菜品去重
        all_dishes = {d.dish_id: d for dishes in single.values() for d in dishes}.values()

        # 3) 计算家庭总缺口
        gaps = FamilyMergeRecommender._gaps(members, single)
        total_gap = {}
        for g in gaps.values():
            for n, v in g.items():
                total_gap[n] = total_gap.get(n, 0) + v

        # 4) 贪心：按“闭合总缺口效率”排序
        scored = []
        for d in all_dishes:
            cover = sum(min(d.nutrients.get(n, 0), total_gap.get(n, 0)) for n in total_gap)
            scored.append((d, cover))
        scored.sort(key=lambda x: -x[1])

        # 5) 主料去重选前 max_dishes 道
        chosen, seen_main = [], set()
        for d, _ in scored:
            main = next(iter(d.ingredients.keys()), "")
            if main in seen_main:
                continue
            chosen.append(d)
            seen_main.add(main)
            if len(chosen) >= max_dishes:
                break
        # 6) 给菜品打标签（家庭级）
        family_allergens = {a for m in family_members.values() for a in m.allergens}
        #family_taboos = {t for m in family_members.values() for t in m.taboos}

        for d in chosen:
            # 通过 dish ↔ 食材 ↔ 过敏原 / 忌口 的映射查询
            dish_allergens = DishSmartData.get_dish_allergens(d.dish_id)
            #dish_taboos = DishSmartData.get_dish_taboos(d.dish_id)

            d.allergens = list(set(dish_allergens) & family_allergens)
            #d.taboos = list(set(dish_taboos) & family_taboos)
        return chosen