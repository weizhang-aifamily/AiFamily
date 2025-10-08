from typing import List, Dict, Tuple
import random
from dataclasses import dataclass

from ejiacanAI.dish2_combo_models import MealRequest


@dataclass
class MealStructure:
    """简版餐次结构配置"""
    main_dishes: int  # 主菜/荤菜数量
    side_dishes: int  # 配菜/素菜数量
    staple_foods: int  # 主食数量
    soups: int  # 汤品数量


class MealStructureGenerator:
    """简版餐次结构生成器"""

    @classmethod
    def generate_meal_structure(
            cls,
            max_dishes: int,
            member_count: int,
            req: MealRequest
    ) -> MealStructure:
        """生成餐次结构配置"""
        rng = random.Random(req.refresh_key)

        # 基础配置规则
        if max_dishes <= 3:
            return cls._generate_small_meal(max_dishes, member_count, rng)
        elif max_dishes <= 6:
            return cls._generate_medium_meal(max_dishes, member_count, rng)
        else:
            return cls._generate_large_meal(max_dishes, member_count, rng)

    @classmethod
    def _generate_small_meal(
            cls,
            max_dishes: int,
            member_count: int,
            rng: random.Random
    ) -> MealStructure:
        """生成小型餐次结构（1-3道菜）"""

        if max_dishes == 1:
            # 1道菜：主菜或主食
            return MealStructure(
                main_dishes=rng.choice([0, 1]),
                side_dishes=0,
                staple_foods=rng.choice([0, 1]),
                soups=0
            )
        elif max_dishes == 2:
            # 2道菜：1主菜1配菜 或 1主菜1主食
            return MealStructure(
                main_dishes=1,
                side_dishes=rng.choice([0, 1]),
                staple_foods=rng.choice([0, 1]),
                soups=0
            )
        else:  # 3道菜
            # 3道菜：1主菜1配菜1主食 或 2主菜1配菜
            main_count = rng.choice([1, 2])
            return MealStructure(
                main_dishes=main_count,
                side_dishes=3 - main_count - rng.choice([0, 1]),
                staple_foods=rng.choice([0, 1]),
                soups=0
            )

    @classmethod
    def _generate_medium_meal(
            cls,
            max_dishes: int,
            member_count: int,
            rng: random.Random
    ) -> MealStructure:
        """生成中型餐次结构（4-6道菜）"""

        base_main = min(3, max_dishes // 2 + 1)
        base_side = min(2, max_dishes - base_main - 1)
        has_soup = rng.random() < 0.6  # 60%概率有汤
        has_staple = rng.random() < 0.8  # 80%概率有主食

        return MealStructure(
            main_dishes=base_main,
            side_dishes=base_side,
            staple_foods=1 if has_staple else 0,
            soups=1 if has_soup else 0
        )

    @classmethod
    def _generate_large_meal(
            cls,
            max_dishes: int,
            member_count: int,
            rng: random.Random
    ) -> MealStructure:
        """生成大型餐次结构（7+道菜）"""

        main_ratio = 0.4 + rng.random() * 0.2  # 40%-60%主菜
        side_ratio = 0.3 + rng.random() * 0.2  # 30%-50%配菜

        main_count = max(3, int(max_dishes * main_ratio))
        side_count = max(2, int(max_dishes * side_ratio))
        soup_count = 1 if max_dishes >= 8 else 0
        staple_count = 1

        # 调整总数
        total = main_count + side_count + soup_count + staple_count
        if total > max_dishes:
            # 优先减少配菜
            side_count = max(2, side_count - (total - max_dishes))

        return MealStructure(
            main_dishes=main_count,
            side_dishes=side_count,
            staple_foods=staple_count,
            soups=soup_count
        )