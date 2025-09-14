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
    # 4. 去重增重：主料+做法相似
    # -------------------------------------------------
    @classmethod
    def _dedup_increase_weight(cls, new: Dish, existing: List[Dish]) -> Dish:
        """
        主料去重：如果主料（用量最大的食材）与已选菜品重复，则返回 None
        """
        if not new.ingredients:
            return new  # 无食材信息，直接保留

        # 提取主料（用量最大的食材）
        main_ingredient_new = max(new.ingredients.items(), key=lambda x: x[1])[0]

        # 检查是否与已选菜品主料重复
        for old in existing:
            if not old.ingredients:
                continue
            main_ingredient_old = max(old.ingredients.items(), key=lambda x: x[1])[0]
            if main_ingredient_new == main_ingredient_old:
                return None  # 主料重复，丢弃新菜

        return new  # 主料不重复，保留新菜

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
            ingredients={row.food_description: float(row.food_amount_in_dish_g or 0)},
            nutrients={row.nutrient_name: float(row.nutrient_in_dish or 0)},
            exact_portion=ExactPortion(size="M", grams=int(row.dish_default_portion_g)),
            allergens=row.allergen_list.split(",") if row.allergen_list else [],
            explicit_tags=row.explicit_tags.split(",") if row.explicit_tags else [],
            implicit_tags=row.implicit_tags.split(",") if row.implicit_tags else []
        )

    """
        按餐次独立选菜、独立微调、独立去重
        """
    MEAL_RATIO = {"breakfast": 0.30, "lunch": 0.40, "dinner": 0.30}
    @classmethod
    def generate_per_meal(cls, req: MealRequest) -> List[ComboMeal]:
        dish_list_wide = DishComboData.list_dish_food_nutrient([])  # 一次性拉全表
        # 过滤一部分不满足req的dish，如level_la，qingzhen，sushi等，除memberneed
        dish_list = cls.build_true_dishes(dish_list_wide, req)
        # 只保留符合要求的菜系、种类、时间、应季等
        filtered_dishes = cls.filter_dishes(dish_list, req)
        rng = random.Random(req.refresh_key)
        rng.shuffle(filtered_dishes)
        need_list = DishComboData.list_member_need_nutrient(req.member_ids)

        daily_range = cls._calc_daily_range(need_list, req.deficit_kcal)

        # 根据请求决定要生成几餐
        if req.meal_type == "all":
            meals_to_build = ["breakfast", "lunch", "dinner"]
        else:
            meals_to_build = [req.meal_type]

        # 逐餐处理
        combo_meals: List[ComboMeal] = []
        for meal_code in meals_to_build:
            meal_range = cls._build_single_meal_range(daily_range, meal_code)
            dishes = cls._select_dishes_for_meal(
                filtered_dishes, meal_range, meal_code, req
            )
            cls._scale_portions(dishes, meal_range)  # 按餐次独立缩放
            combo_meals.append(
                cls._build_combo_meal(meal_code, dishes)
            )
        return combo_meals

    # -------------------------------------------------
    # 为单餐构建需求区间
    # -------------------------------------------------
    @classmethod
    def _build_single_meal_range(
            cls, daily: Dict[str, Dict[str, float]], meal_code: str
    ) -> Dict[str, Dict[str, float]]:
        ratio = cls.MEAL_RATIO[meal_code]
        return {k: {"min": v["min"] * ratio, "max": v["max"] * ratio}
                for k, v in daily.items()}

    # -------------------------------------------------
    # 为单餐选菜
    # -------------------------------------------------
    @classmethod
    def _select_dishes_for_meal(
            cls,
            dish_list: List[Dish],
            meal_range: Dict[str, Dict[str, float]],
            meal_code: str,
            req: MealRequest
    ) -> List[Dish]:
        rng = random.Random(req.refresh_key)

        # 1. 过敏原过滤
        allergens = set(DishComboData.get_family_allergens(req.member_ids))

        # 2. 先过滤：①餐次匹配 ②烹饪时间 ③不过敏
        pool = [
            d for d in dish_list
            if (d.meal_type_code == meal_code or meal_code == "all")
               and (not req.cook_time_limit or d.cook_time <= req.cook_time_limit)
               and (not req.dish_series or d.dish_series in req.dish_series)
               and not allergens.intersection(set(d.allergens))
        ]

        # 3. 随机洗牌
        rng.shuffle(pool)

        # 4. 打分
        def score(d: Dish) -> int:
            return len(d.explicit_tags) + len(d.implicit_tags)

        pool.sort(key=score, reverse=True)

        # 5. 选够目标数
        target = req.max_dishes_per_meal or max(2, len(req.member_ids) + 2)
        dishes: List[Dish] = []
        remaining = meal_range.copy()

        for row in pool:
            if len(dishes) >= target:
                break
            # dish = cls._build_dish(row)
            dish = cls._dedup_increase_weight(row, dishes)
            if dish:
                cls._update_remaining(dish, remaining)
                dishes.append(dish)
        return dishes

    # -------------------------------------------------
    # 打包单餐
    # -------------------------------------------------
    @classmethod
    def _build_combo_meal(cls, meal_code: str, dishes: List[Dish]) -> ComboMeal:
        cook = sum(d.cook_time for d in dishes)
        shopping = defaultdict(float)
        for d in dishes:
            for ing, g in d.ingredients.items():
                shopping[ing] += g

        name_map = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐"}
        return ComboMeal(
            combo_id=abs(hash(meal_code + str(random.randint(0, 9999)))) % 100000,
            combo_name=name_map.get(meal_code, meal_code),
            need_codes=[],
            meal_type=meal_code,
            dishes=dishes,
            total_cook_time=cook,
            portion_plan={},
            shopping_list=dict(shopping)
        )

    from typing import Dict, List, Tuple
    from collections import defaultdict
    from ejiacanAI.dish2_combo_models import Dish, DishFoodNutrient, ExactPortion

    from typing import Dict, List
    from collections import defaultdict
    from ejiacanAI.dish2_combo_models import Dish, ExactPortion, DishFoodNutrient

    def build_true_dishesbak(wide_rows: List[DishFoodNutrient], req: MealRequest) -> List[Dish]:
        """
        把“菜品 × 食材 × 营养素”宽表聚合成真正的 Dish 对象列表
        """
        # dish_id -> food_id -> List[DishFoodNutrient]
        dish_map: Dict[int, Dict[int, List[DishFoodNutrient]]] = defaultdict(lambda: defaultdict(list))
        for r in wide_rows:
            dish_map[r.dish_id][r.food_id].append(r)

        dishes: List[Dish] = []
        for dish_id, food_map in dish_map.items():
            # 1. 取 dish 级元数据（所有行都一样，取第一行即可）
            meta = next(iter(food_map.values()))[0]  # 任意取一条

            dish_name = meta.dish_name
            dish_emoji = meta.dish_emoji or ""
            cook_time = meta.dish_cook_time
            default_portion = meta.dish_default_portion_g

            meal_type_code = ""
            series_id = None
            series_name = ""
            category_id = None
            category_name = ""
            tag_id = None
            tag_name = ""

            # 2. 遍历所有行，收集第一个出现的非空值
            for rows_all in food_map.values():
                for r in rows_all:
                    if r.dish_meal_type_code and not meal_type_code:
                        meal_type_code = r.dish_meal_type_code
                    if r.series_id is not None and series_id is None:
                        series_id = r.series_id
                        series_name = r.series_name or ""
                    if r.category_id is not None and category_id is None:
                        category_id = r.category_id
                        category_name = r.category_name or ""
                    if r.tag_id is not None and tag_id is None:
                        tag_id = r.tag_id
                        tag_name = r.tag_name or ""
                    # 一旦全部都有了，可以提前退出
                    if all([meal_type_code, series_id, category_id, tag_id]):
                        break

            # 2. 按食材聚合
            ingredients: Dict[str, float] = {}
            nutrients: Dict[str, float] = defaultdict(float)
            allergens: set[str] = set()
            explicit_tags: set[str] = set()
            implicit_tags: set[str] = set()
            series_id: int

            for food_id, rows in food_map.items():
                # 2-1 食材 & 用量
                first = rows[0]
                ingredients[first.food_description] = float(first.food_amount_in_dish_g or 0)

                # 2-2 营养素（已乘克数）
                for r in rows:
                    if r.nutrient_name and r.nutrient_in_dish is not None:
                        nutrients[r.nutrient_name] += float(r.nutrient_in_dish)

                # 2-3 标签 & 过敏原（每行都重复，但 set 去重）
                if first.allergen_list:
                    allergens.update(a.strip() for a in first.allergen_list.split(",") if a.strip())
                if first.explicit_tags: # tag_id
                    explicit_tags.update(t.strip() for t in first.explicit_tags.split(",") if t.strip())
                if first.implicit_tags: # category_id
                    implicit_tags.update(t.strip() for t in first.implicit_tags.split(",") if t.strip())
                if first.series_id: # series_id
                    series_id = first.series_id

            dishes.append(Dish(
                dish_id=dish_id,
                name=dish_name,
                cook_time=cook_time,
                ingredients=ingredients,
                nutrients=dict(nutrients),
                exact_portion=ExactPortion(size="M", grams=default_portion),
                allergens=list(allergens),
                explicit_tags=list(explicit_tags),
                implicit_tags=list(implicit_tags),
                dish_series=series_id,
                meal_type_code=meal_type_code
            ))
        return dishes


    def build_true_dishes(wide_rows: List[DishFoodNutrient], req: MealRequest) -> List[Dish]:
        """
        把 dish_food_complete_view 宽表聚合成真正的 Dish 对象列表
        并进行初步过滤（level_la, qingzhen, sushi等）
        """
        # dish_id -> food_id -> List[DishFoodNutrient]
        dish_map: Dict[int, Dict[int, List[DishFoodNutrient]]] = defaultdict(lambda: defaultdict(list))
        for r in wide_rows:
            dish_map[r.dish_id][r.food_id].append(r)

        dishes: List[Dish] = []

        # 营养成分字段映射到标准编码
        nutrient_mapping = {
            'protein': 'Protein',
            'fat': 'Fat',
            'Ca': 'Calcium',
            'ash': 'Ash'
        }

        for dish_id, food_map in dish_map.items():
            # 1. 取 dish 级元数据（所有行都一样，取第一行即可）
            meta = next(iter(food_map.values()))[0]

            # 3. 收集菜品基本信息
            dish_name = meta.dish_name
            dish_emoji = meta.dish_emoji
            cook_time = meta.dish_cook_time
            default_portion = meta.dish_default_portion_g
            rating = meta.dish_rating
            description = meta.dish_description

            # 4. 收集分类、菜系、标签信息
            meal_type_code = meta.meal_type
            series_id = meta.series_id
            series_name = meta.series_name
            category_id = meta.category_id
            category_name = meta.category_name
            tag_id = meta.tag_id
            tag_name = meta.tag_name

            # 2. 遍历所有行，收集第一个出现的非空值
            for rows_all in food_map.values():
                for r in rows_all:
                    if r.meal_type and not meal_type_code:
                        meal_type_code = r.meal_type
                    if r.series_id is not None and series_id is None:
                        series_id = r.series_id
                        series_name = r.series_name or ""
                    if r.category_id is not None and category_id is None:
                        category_id = r.category_id
                        category_name = r.category_name or ""
                    if r.tag_id is not None and tag_id is None:
                        tag_id = r.tag_id
                        tag_name = r.tag_name or ""
                    # 一旦全部都有了，可以提前退出
                    if all([meal_type_code, series_id, category_id, tag_id]):
                        break

            # 5. 按食材聚合
            ingredients: Dict[str, float] = {}
            nutrients: Dict[str, float] = defaultdict(float)
            allergens: set[str] = set()
            explicit_tags: set[str] = set()
            implicit_tags: set[str] = set()

            for food_id, rows in food_map.items():
                # 5-1 食材 & 用量
                first = rows[0]
                ingredients[first.foodName] = float(first.food_amount_grams or 0)

                # 5-2 营养成分（转换为纵表并累加）
                for r in rows:
                    for field, code in nutrient_mapping.items():
                        value = getattr(r, field, None)
                        if value is not None:
                            # 计算该食材在菜品中的营养成分含量
                            nutrient_amount = float(value * first.food_amount_grams) / 100
                            nutrients[code] += nutrient_amount

                # 5-3 过敏原
                if first.allergen_code:
                    allergens.add(first.allergen_code)

            # 6. 收集标签信息
            if tag_name:
                explicit_tags.add(f"{tag_id}:{tag_name},")
            if category_name:
                implicit_tags.add(f"{category_id}:{category_name},")
            if series_name:
                implicit_tags.add(f"{series_id}:{series_name},")

            # 7. 创建 Dish 对象
            dishes.append(Dish(
                dish_id=dish_id,
                name=dish_name,
                cook_time=cook_time,
                ingredients=ingredients,
                nutrients=dict(nutrients),
                exact_portion=ExactPortion(size="M", grams=default_portion),
                allergens=list(allergens),
                explicit_tags=list(explicit_tags),
                implicit_tags=list(implicit_tags),
                dish_series=series_id,
                meal_type_code=meal_type_code,
                rating=rating,
                description=description
            ))

        return dishes


    @classmethod
    def filter_dishes(cls, dish_list: List[Dish], req: MealRequest) -> List[Dish]:
        # 创建结果列表而不是在原列表上修改
        filtered_dishes = []

        for dish in dish_list:
            # 假设 dish 是 Dish 对象，而不是 (dish_id, meta) 元组
            # 如果需要获取 dish_id 和 meta，需要根据 Dish 类的实际结构调整

            # 检查烹饪时间限制
            if (hasattr(dish, 'cook_time') and dish.cook_time is not None and
                    req.cook_time_limit is not None and
                    dish.cook_time > req.cook_time_limit):
                continue

            # 检查菜品系列
            if (hasattr(dish, 'dish_series') and dish.dish_series is not None and
                    req.dish_series and
                    dish.dish_series not in req.dish_series):
                continue

            # 如果通过所有过滤条件，添加到结果列表
            filtered_dishes.append(dish)

        return filtered_dishes