# meal_generator_v2.py
import random
from typing import List, Dict
from collections import defaultdict
from ejiacanAI.dish2_combo_models import MealRequest, ComboMeal, Dish, ExactPortion, DishFoodNutrient
from ejiacanAI.dish2_combo_data import DishComboData   # 统一数据入口

class MealGeneratorV2:
    """
    一次性读取两张视图 → 内存对象列表 → 选菜 → 份量微调 → 打包三餐
    全程无 pandas、无硬编码常量。
    """

    # -------------------------------------------------
    # 1. 主入口
    # -------------------------------------------------
    @classmethod
    def generate(cls, req: MealRequest) -> List[ComboMeal]:
        # 1. 一次性拉表
        dish_list = DishComboData.list_dish_food_nutrient([])          # 全部菜品
        need_list = DishComboData.list_member_need_nutrient(req.member_ids)

        # 2. 计算每日 & 每餐需求
        daily_range = cls._calc_daily_range(need_list, req.deficit_kcal)
        meal_ranges = cls._split_ranges(daily_range, req.meal_type)

        # 3. 选菜（含过敏/标签/去重增重）
        dishes = cls._select_dishes(dish_list, meal_ranges, req)

        # 4. 全局份量微调
        cls._scale_portions(dishes, daily_range)

        # 5. 按餐次打包
        return cls._pack_meals(dishes, req)

    # -------------------------------------------------
    # 2. 计算每日需求（基于 MemberNeedNutrient）
    # -------------------------------------------------
    @classmethod
    def _calc_daily_range(cls, need_list: List, deficit: int) -> Dict[str, Dict[str, float]]:
        ranges = defaultdict(lambda: {"min": 0.0, "max": 0.0})
        for n in need_list:
            ranges[n.nutrient_code]["min"] += float(n.min_need_qty or 0)
            ranges[n.nutrient_code]["max"] += float(n.max_need_qty or 0)

        if deficit:
            factor = (2000 - deficit) / 2000
            for k in ranges:
                ranges[k]["min"] *= factor
                ranges[k]["max"] *= factor
        return dict(ranges)

    @classmethod
    def _split_ranges(cls, daily: Dict[str, Dict[str, float]], meal_type: str) -> Dict[str, Dict[str, float]]:
        ratio_map = {"all": 1.0, "breakfast": 0.3, "lunch": 0.4, "dinner": 0.3}
        ratio = ratio_map[meal_type]
        return {k: {"min": v["min"] * ratio, "max": v["max"] * ratio} for k, v in daily.items()}

    # -------------------------------------------------
    # 3. 选菜（显性+隐性标签 + 去重增重）
    # -------------------------------------------------
    @classmethod
    def _select_dishes(cls, dish_list: List, ranges: Dict[str, Dict[str, float]], req: MealRequest) -> List[Dish]:
        # 1. 过滤 & 洗牌
        rng = random.Random(req.refresh_key)
        pool = list(dish_list)        # 复制
        rng.shuffle(pool)

        # 2. 过敏原过滤
        allergens = set(DishComboData.get_family_allergens(req.member_ids))
        pool = [d for d in pool if not allergens.intersection(set(d.allergen_list.split(",")))]

        # 3. 目标菜数
        target = req.max_dishes_per_meal or max(2, len(req.member_ids) + 2)

        # 4. 打分函数（显性+隐性标签数量）
        def score(d: DishFoodNutrient):
            explicit = d.explicit_tags.split(",") if d.explicit_tags else []
            implicit = d.implicit_tags.split(",") if d.implicit_tags else []
            return len(explicit) + len(implicit)

        pool.sort(key=score, reverse=True)

        dishes = []
        remaining = ranges.copy()

        for row in pool:
            if len(dishes) >= target:
                break
            dish = cls._build_dish(row)
            dish = cls._dedup_increase_weight(dish, dishes)
            if dish:
                cls._update_remaining(dish, remaining)
                dishes.append(dish)
        return dishes

    # -------------------------------------------------
    # 4. 去重增重：主料+做法相似
    # -------------------------------------------------
    @classmethod
    def _dedup_increase_weight(cls, new: Dish, existing: List[Dish]) -> Dish:
        """
        主料+做法相似则合并食材克数，返回 None 表示已合并
        """
        key = lambda d: (tuple(sorted(d.ingredients.keys())), d.cook_time // 5)
        new_key = key(new)
        for old in existing:
            if key(old) == new_key:
                # 累加克数 & 营养素
                for ing, g in new.ingredients.items():
                    old.ingredients[ing] = old.ingredients.get(ing, 0) + g
                for n, v in new.nutrients.items():
                    old.nutrients[n] = old.nutrients.get(n, 0) + v
                return None              # 已合并
        return new

    # -------------------------------------------------
    # 5. 份量微调（S/M/L + 精确克数）
    # -------------------------------------------------
    @classmethod
    def _scale_portions(cls, dishes: List[Dish], daily_range: Dict[str, Dict[str, float]]):
        total = defaultdict(float)
        for d in dishes:
            for n, v in d.nutrients.items():
                total[n] += v

        scale = min(daily_range[n]["max"] / max(total[n], 1e-6) for n in daily_range)
        scale = max(0.8, min(1.2, scale))

        for d in dishes:
            raw = int(d.exact_portion.grams * scale)
            raw = max(1, raw)
            # 重新映射外壳
            if raw <= 100:
                size = "S"
            elif raw <= 200:
                size = "M"
            else:
                size = "L"
            d.exact_portion = ExactPortion(size=size, grams=raw)

    # -------------------------------------------------
    # 6. 打包三餐
    # ---------------------------------------------
    @classmethod
    def _pack_meals(cls, dishes: List[Dish], req: MealRequest) -> List[ComboMeal]:
        meal_cnt = 3 if req.meal_type == "all" else 1
        per = max(1, len(dishes) // meal_cnt)
        splits = [dishes[i * per: (i + 1) * per] for i in range(meal_cnt)]

        meals = []
        names = ["早餐", "午餐", "晚餐"] if meal_cnt == 3 else [req.meal_type]
        for name, ds in zip(names, splits):
            cook = sum(d.cook_time for d in ds)
            shopping = defaultdict(float)
            for d in ds:
                for ing, g in d.ingredients.items():
                    shopping[ing] += g
            meals.append(ComboMeal(
                combo_id=abs(hash(name + str(req.refresh_key))) % 100000,
                combo_name=name,
                need_codes=[],
                meal_type=name[:2].lower(),
                dishes=ds,
                total_cook_time=cook,
                portion_plan={},  # 前端用 exact_portion
                shopping_list=dict(shopping)
            ))
        return meals

    # ---------------------------------------------
    # 7. 小工具
    # ---------------------------------------------
    @classmethod
    def _update_remaining(cls, dish: Dish, remaining: Dict[str, Dict[str, float]]):
        for n, v in dish.nutrients.items():
            if n in remaining:
                remaining[n]["min"] = max(0, remaining[n]["min"] - v)
                remaining[n]["max"] = max(0, remaining[n]["max"] - v)

    @classmethod
    def _build_dish(cls, row: DishFoodNutrient) -> Dish:
        return Dish(
            dish_id=row.dish_id,
            name=row.dish_name,
            cook_time=row.dish_cook_time,
            ingredients={row.food_description: float(row.food_amount_in_dish_g)},
            nutrients={row.nutrient_name: float(row.nutrient_in_dish)},
            exact_portion=ExactPortion(size="M", grams=int(row.dish_default_portion_g)),
            allergens=row.allergen_list.split(",") if row.allergen_list else [],
            explicit_tags=row.explicit_tags.split(",") if row.explicit_tags else [],
            implicit_tags=row.implicit_tags.split(",") if row.implicit_tags else []
        )