# meal_generator_v2.py
import json
import logging
import random
from typing import List, Dict, Optional
from collections import defaultdict

from ejiacanAI.MealStructureGenerator import MealStructureGenerator
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
    def generate_per_meal_default(cls, req: MealRequest) -> List[ComboMeal]:
        dish_list_wide = DishComboData.list_dish_food_nutrient([], req)  # 一次性拉全表
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
            # cls._scale_portions(dishes, meal_range)  # 按餐次独立缩放
            combo_meals.append(
                cls._build_combo_meal(meal_code, dishes)
            )
        return combo_meals
    @classmethod
    def generate_per_meal(cls, req: MealRequest) -> List[ComboMeal]:
        dish_list_wide = DishComboData.list_dish_food_nutrient([],req)  # 一次性拉全表
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
    def _select_dishes_for_meal_bak(
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
            if ("all" == meal_code or meal_code in cls.tag_pick(d, 'meal_time', 'code'))
               # and (not req.cook_time_limit or d.cook_time <= req.cook_time_limit)
               # and (not req.dish_series or any(series in cls.tag_pick(d, 'cuisine', 'code')
               #                                 for series in req.dish_series.split(',')))
               # and not allergens.intersection(set(d.allergens))
        ]

        # 3. 随机洗牌
        rng.shuffle(pool)

        # 4. 打分
        def score(d: Dish) -> int:
            base_score = len(d.explicit_tags)

            # 计算 req.explicit_tags 和 dish.explicit_tags 的匹配度
            if hasattr(req, 'explicit_tags') and req.explicit_tags:
                # 确保 req.explicit_tags 是列表形式
                req_tags = req.explicit_tags
                if isinstance(req_tags, str):
                    req_tags = req_tags.split(",")

                # 计算匹配的标签数量
                matched_tags = set(req_tags) & set(d.explicit_tags)
                match_score = len(matched_tags) * 2  # 给匹配的标签更高权重

                # 基础分 + 匹配分
                return base_score + match_score
            else:
                return base_score

        # 按分数排序（降序）
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

        # 2. 生成餐次结构配置
        target = req.max_dishes_per_meal or max(2, len(req.member_ids) + 2)
        meal_structure = MealStructureGenerator.generate_meal_structure(
            target, len(req.member_ids), req
        )

        # 3. 先过滤：①餐次匹配 ②烹饪时间 ③不过敏
        pool = [
            d for d in dish_list
            if ("all" == meal_code or meal_code in cls.tag_pick(d, 'meal_time', 'code'))
               # and (not req.cook_time_limit or d.cook_time <= req.cook_time_limit)
               # and (not req.dish_series or any(series in cls.tag_pick(d, 'cuisine', 'code')
               #                                 for series in req.dish_series.split(',')))
               # and not allergens.intersection(set(d.allergens))
        ]

        # 4. 按餐次结构分类菜品
        categorized_dishes = cls._categorize_dishes_by_structure(pool)

        # 5. 随机洗牌每个分类
        for category in categorized_dishes:
            rng.shuffle(categorized_dishes[category])

        # 6. 打分函数（保持不变）
        def score(d: Dish) -> int:
            base_score = len(d.explicit_tags)

            # 计算 req.explicit_tags 和 dish.explicit_tags 的匹配度
            if hasattr(req, 'explicit_tags') and req.explicit_tags:
                req_tags = req.explicit_tags
                if isinstance(req_tags, str):
                    req_tags = req_tags.split(",")

                matched_tags = set(req_tags) & set(d.explicit_tags)
                match_score = len(matched_tags) * 2
                return base_score + match_score
            else:
                return base_score

        # 7. 按餐次结构选择菜品
        dishes: List[Dish] = []
        remaining = meal_range.copy()

        # 按优先级选择：主菜 -> 配菜 -> 主食 -> 汤品
        selection_order = [
            ('main_dishes', meal_structure.main_dishes),
            ('side_dishes', meal_structure.side_dishes),
            ('staple_foods', meal_structure.staple_foods),
            ('soups', meal_structure.soups)
        ]

        for category, target_count in selection_order:
            if target_count == 0:
                continue

            category_pool = categorized_dishes.get(category, [])

            # 按分数排序（降序）
            category_pool.sort(key=score, reverse=True)

            selected_count = 0
            for dish in category_pool:
                if selected_count >= target_count:
                    break

                selected_dish = cls._dedup_increase_weight(dish, dishes)
                if selected_dish:
                    cls._update_remaining(selected_dish, remaining)
                    dishes.append(selected_dish)
                    selected_count += 1

        # 8. 如果按结构选择不够，用原有逻辑补充
        if len(dishes) < target:
            remaining_pool = [d for d in pool if d not in dishes]
            remaining_pool.sort(key=score, reverse=True)

            for dish in remaining_pool:
                if len(dishes) >= target:
                    break
                selected_dish = cls._dedup_increase_weight(dish, dishes)
                if selected_dish:
                    cls._update_remaining(selected_dish, remaining)
                    dishes.append(selected_dish)

        return dishes

    @classmethod
    def _categorize_dishes_by_structure(cls, dish_list: List[Dish]) -> Dict[str, List[Dish]]:
        """根据餐次结构对菜品进行分类"""
        categorized = {
            'main_dishes': [],
            'side_dishes': [],
            'staple_foods': [],
            'soups': []
        }

        for dish in dish_list:
            category = cls._classify_dish_category(dish)
            if category in categorized:
                categorized[category].append(dish)

        return categorized

    @classmethod
    def _classify_dish_category(cls, dish: Dish) -> str:
        """判断菜品属于哪个类别"""
        dish_tags = getattr(dish, 'dish_tags', {}) or {}

        # 1. 优先使用 dish_tags 中的明确分类
        # 主食判断
        staple_tags = dish_tags.get('staple', [])
        for tag in staple_tags:
            code = tag.get('code', '')
            if code == 'yes':  # 明确标记为主食
                return 'staple_foods'

        # 2. 使用 vege 标签进行荤素分类
        vege_tags = dish_tags.get('vege', [])
        for tag in vege_tags:
            code = tag.get('code', '')
            # 荤菜类别
            if code in ['meat','seafood']:
                return 'main_dishes'
            # 素菜类别
            elif code in ['vege', 'vegan', 'egg']:
                return 'side_dishes'

        # 3. 使用 category 判断汤品
        category_tags = dish_tags.get('category', [])
        for tag in category_tags:
            code = tag.get('code', '')
            if code in ['soups']:  # 汤品烹饪方法
                return 'soups'

        # 4. 根据营养素含量进行智能判断
        nutrients = getattr(dish, 'nutrients', {}) or {}
        protein = nutrients.get('Protein', 0)
        carbs = nutrients.get('Carbohydrate', 0)

        # 高碳水且低蛋白的可能是主食
        if carbs > 40 and protein < 10:
            return 'staple_foods'

        # 高蛋白的可能是主菜
        if protein > 20:
            return 'main_dishes'
        elif protein > 8:
            return 'side_dishes'

        # 5. 最终默认分类
        # 如果以上都无法判断，保守地分类为配菜
        return 'side_dishes'
    # -------------------------------------------------
    # 打包单餐
    # -------------------------------------------------
    @classmethod
    def _build_combo_meal(cls, meal_code: str, dishes: List[Dish]) -> ComboMeal:
        cook = sum(d.cook_time for d in dishes)
        shopping = defaultdict(float)
        nutrients = defaultdict(float)  # 新增：营养素汇总

        for d in dishes:
            # 汇总购物清单
            for ing, g in d.ingredients.items():
                shopping[ing] += g
            # 汇总营养素
            for nutrient, value in d.nutrients.items():
                nutrients[nutrient] += value

        name_map = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐"}
        return ComboMeal(
            combo_id=abs(hash(meal_code + str(random.randint(0, 9999)))) % 100000,
            combo_name=name_map.get(meal_code, meal_code),
            need_codes=[],
            meal_type=meal_code,
            dishes=dishes,
            total_cook_time=cook,
            portion_plan={},
            shopping_list=dict(shopping),
            nutrients=dict(nutrients)  # 新增：传入营养素汇总
        )

    from typing import Dict, List
    from ejiacanAI.dish2_combo_models import Dish, ExactPortion, DishFoodNutrient

    @classmethod
    def build_true_dishes(cls, wide_rows: List[DishFoodNutrient], req: MealRequest) -> List[Dish]:
        dish_map = cls._group_by_dish_and_food(wide_rows)
        dishes: List[Dish] = []

        for dish_id, food_map in dish_map.items():
            meta = cls._get_meta(food_map)
            ingredients, nutrients, allergens = cls._aggregate_foods(food_map)
            dish_tags = cls._build_dish_tags(meta.tags_json)  # 2. 新 tag 结构

            # 3. 一次性把 CSV 里“多余”字段也带上
            dishes.append(Dish(
                dish_id=dish_id,
                name=meta.dish_name,
                dish_emoji=meta.dish_emoji,  # 🔥
                cook_time=meta.dish_cook_time,
                default_portion=meta.dish_default_portion_g,
                rating=meta.dish_rating,
                description=meta.dish_description,
                explicit_tags=meta.need_tags.split(",") if meta.need_tags else [],

                ingredients=ingredients,
                nutrients=nutrients,
                exact_portion=ExactPortion(size="M", grams=meta.dish_default_portion_g),
                allergens=list(allergens),

                dish_tags=dish_tags,  # 新版 map
            ))
        return dishes

    # ------------------ 下面全是小工具 ------------------
    @staticmethod
    def _group_by_dish_and_food(wide_rows):
        d = defaultdict(lambda: defaultdict(list))
        for r in wide_rows:
            d[r.dish_id][r.food_id].append(r)
        return d

    @staticmethod
    def _get_meta(food_map):
        return next(iter(food_map.values()))[0]

    @classmethod
    def _aggregate_foods(cls, food_map):
        ingredients: Dict[str, float] = {}
        nutrients: Dict[str, float] = defaultdict(float)
        allergens: set[str] = set()
        NUTRIENT_MAPPING = {
            # 宏量
            'protein': 'Protein',
            'fat': 'Fat',
            'CHO': 'Carbohydrate',
            'dietaryFiber': 'DietaryFiber',
            'ash': 'Ash',
            # 能量
            'energyKCal': 'EnergyKCal',
            'energyKJ': 'EnergyKJ',
            # 矿物质
            'Ca': 'Calcium', 'P': 'Phosphorus', 'K': 'Potassium',
            'Na': 'Sodium', 'Mg': 'Magnesium', 'Fe': 'Iron',
            'Zn': 'Zinc', 'Se': 'Selenium', 'Cu': 'Copper',
            'Mn': 'Manganese',
            # 维生素
            'vitaminA': 'VitaminA',
            'carotene': 'Carotene',
            'retinol': 'Retinol',
            'thiamin': 'Thiamin',
            'riboflavin': 'Riboflavin',
            'niacin': 'Niacin',
            'vitaminC': 'VitaminC',
            'vitaminETotal': 'VitaminETotal',
            'vitaminE1': 'VitaminE1',
            'vitaminE2': 'VitaminE2',
            'vitaminE3': 'VitaminE3',
            # 其他
            'cholesterol': 'Cholesterol',
            'water': 'Water',
            'edible': 'EdibleRatio'
        }
        for food_id, rows in food_map.items():
            first = rows[0]
            ingredients[first.foodName] = float(first.food_amount_grams or 0)

            for field, key in NUTRIENT_MAPPING.items():
                val = getattr(first, field, None)
                if val is not None:
                    nutrients[key] += float(val) * float(first.food_amount_grams) / 100

            if first.allergen_code:
                allergens.add(first.allergen_code)
        return ingredients, dict(nutrients), allergens

    @staticmethod
    def _build_dish_tags(tags_json: Optional[str]) -> Dict[str, List[Dict[str, str]]]:
        """按 group 聚合成 map：group -> [{code: xx, name: yy}, ...]"""
        if not tags_json:
            return {}
        try:
            tags = json.loads(tags_json)
        except Exception as e:
            logging.warn("invalid tags_json: %s  error: %s", tags_json, e)
            return {}
        bucket: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        for tag in tags:
            group = tag.get('group')
            if group:
                bucket[group].append({'code': tag.get('code'), 'name': tag.get('name')})
        return dict(bucket)
    @classmethod
    def build_true_dishes_bak(cls, wide_rows: List[DishFoodNutrient], req: MealRequest) -> List[Dish]:
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

            # 5. 按食材聚合
            ingredients: Dict[str, float] = {}
            nutrients: Dict[str, float] = defaultdict(float)
            allergens: set[str] = set()
            explicit_tags: set[str] = set()
            implicit_tags: set[str] = set()
            dish_series: Optional[str] = None  # 菜系ID
            meal_type_code: Optional[str] = None

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
                if first.tags_json:
                    dish_series = cls.extract_group_items(first.tags_json,'cuisine')
                    meal_type_code = cls.extract_group_items(first.tags_json,'meal_time')
                    dish_series = dish_series[:dish_series.find(':')]
                    meal_type_code = meal_type_code[:meal_type_code.find(':')]
                    explicit_tags.add(cls.extract_group_items(first.tags_json,'cuisine'))
                    implicit_tags.add(cls.extract_group_items(first.tags_json,'meal_time'))

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
                dish_series=dish_series,
                meal_type_code=meal_type_code,
                rating=rating,
                description=description
            ))

        return dishes

    @classmethod
    def extract_group_items(cls, json_str, target_group):
        """
        从数据列表中提取指定分组的信息

        Args:
            data_list: 包含多个字典的列表
            target_group: 要提取的分组名称，如'meal_time', 'cuisine'等

        Returns:
            str: 指定分组的信息，格式如"code：name"或多个用逗号相隔
        """
        if not json_str or not target_group:
            return ""

        try:
            # 将JSON字符串解析为Python列表
            data_list = json.loads(json_str)

            group_items = []

            for item in data_list:
                if isinstance(item, dict) and item.get('group') == target_group:
                    code = item.get('code', '')
                    name = item.get('name', '')
                    if code and name:
                        group_items.append(f"{code}:{name}")

            return '，'.join(group_items)

        except json.JSONDecodeError:
            return "无效的JSON格式"
        except Exception as e:
            return f"处理出错: {str(e)}"
    @staticmethod
    def tag_pick(dish: Dish, group: str, pick='code'):
        """通用取标签工具：group=分组名，pick='code'|'name'"""
        return [t[pick] for t in dish.dish_tags.get(group, [])]
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
            dish_series = cls.tag_pick(dish, 'cuisine', 'code')
            raw = req.dish_series
            allowed = {s.strip() for s in raw.split(',')} if raw else set()

            # 检查两个集合是否有交集
            if allowed and not any(series in allowed for series in dish_series):
                continue

            # 如果通过所有过滤条件，添加到结果列表
            filtered_dishes.append(dish)

        return filtered_dishes