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
        ranges = defaultdict(lambda: {"min": 0.0, "max": 0.0, "need": 0.0})
        for n in need_list:
            ranges[n.nutrient_code]["min"] += float(n.min_need_qty or 0)
            ranges[n.nutrient_code]["max"] += float(n.max_need_qty or 0)
            ranges[n.nutrient_code]["need"] += float(n.need_qty or 0)

        if deficit:
            factor = (2000 - deficit) / 2000
            for k in ranges:
                ranges[k]["min"] *= factor
                ranges[k]["max"] *= factor
                ranges[k]["need"] *= factor
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
    def _scale_portions_bak(cls, dishes: List[Dish], daily_range: Dict[str, Dict[str, float]]):
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
    def _update_remaining_bak(cls, dish: Dish, remaining: Dict[str, Dict[str, float]]):
        for n, v in dish.nutrients.items():
            if n in remaining:
                remaining[n]["min"] = max(0, remaining[n]["min"] - v)
                remaining[n]["max"] = max(0, remaining[n]["max"] - v)
                remaining[n]["need"] = max(0, remaining[n]["need"] - v)

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
        return {k: {"min": v["min"] * ratio, "max": v["max"] * ratio, "need": v["need"] * ratio}
                for k, v in daily.items()}


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
        msg = MealStructureGenerator()
        meal_structure = msg.calculate_meal_config(
            req.members, meal_code, req.province_code
        )
        target = sum(meal_structure.values())

        # 3. 先过滤：①餐次匹配 ②烹饪时间 ③不过敏
        pool = [
            d for d in dish_list
            if ("all" == meal_code or meal_code in cls.tag_pick(d, 'meal_time', 'code'))
               # and (not req.cook_time_limit or d.cook_time <= req.cook_time_limit)
               # and not allergens.intersection(set(d.allergens))
        ]

        # 4. 按餐次结构分类菜品
        categorized_dishes = cls._categorize_dishes_by_structure(pool)

        # 5. 随机洗牌每个分类
        for category in categorized_dishes:
            rng.shuffle(categorized_dishes[category])

        # 6. 打分函数（考虑营养补充）
        def score(d: Dish) -> int:
            base_score = len(d.explicit_tags)

            # 计算 req.explicit_tags 和 dish.explicit_tags 的匹配度
            if hasattr(req, 'explicit_tags') and req.explicit_tags:
                req_tags = req.explicit_tags
                if isinstance(req_tags, str):
                    req_tags = req_tags.split(",")

                matched_tags = set(req_tags) & set(d.explicit_tags)
                match_score = len(matched_tags) * 2
                base_score += match_score

            # 新增：营养补充加分（基于当前剩余营养需求）
            nutrient_bonus = cls._calculate_nutrient_bonus(d, meal_range)
            return base_score + nutrient_bonus

        # 7. 按餐次结构选择菜品（不检查营养超标，因为后续会调整份量）
        dishes: List[Dish] = []
        remaining = {k: v.copy() for k, v in meal_range.items()}  # 深拷贝剩余营养需求

        # 按优先级选择：主菜 -> 配菜 -> 主食 -> 汤品
        selection_order = [
            ('main_dish', meal_structure.get('main_dish',1)),
            ('baby_food', meal_structure.get('baby_food',0)),
            ('side_dish', meal_structure.get('side_dish',0)),
            ('staple', meal_structure.get('staple',1)),
            ('soup', meal_structure.get('soup',0))
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

                # 移除了营养超标检查，因为后续会通过份量调整来解决
                selected_dish = cls._dedup_increase_weight(dish, dishes)
                if selected_dish:
                    cls._update_remaining(selected_dish, remaining)
                    dishes.append(selected_dish)
                    selected_count += 1

        # 8. 如果按结构选择不够，补充菜品（优先补充能改善营养平衡的）
        if len(dishes) < target:
            remaining_pool = [d for d in pool if d not in dishes]

            # 重新计算分数（考虑当前剩余营养需求）
            remaining_pool.sort(key=lambda d: score(d), reverse=True)

            for dish in remaining_pool:
                if len(dishes) >= target:
                    break

                selected_dish = cls._dedup_increase_weight(dish, dishes)
                if selected_dish:
                    cls._update_remaining(selected_dish, remaining)
                    dishes.append(selected_dish)

        return dishes

    @classmethod
    def _calculate_nutrient_bonus(cls, dish: Dish, meal_range: Dict[str, Dict[str, float]]) -> int:
        """
        计算菜品对当前营养需求的补充加分
        重点补充那些当前还比较缺乏的营养素
        """
        bonus = 0

        for nutrient, values in meal_range.items():
            if nutrient in dish.nutrients:
                current_need = values.get("need", 0)  # 当前还需要的量
                dish_provides = dish.nutrients[nutrient]  # 菜品提供的量

                # 如果这个营养素还有较大需求，且菜品能提供，就加分
                if current_need > 0 and dish_provides > 0:
                    # 补充比例越高，加分越多
                    supplement_ratio = min(dish_provides / current_need, 2.0)  # 限制最大加分
                    bonus += int(supplement_ratio * 3)  # 乘以权重系数

        return min(bonus, 10)  # 限制最大加分，避免过度影响

    @classmethod
    def _update_remaining(cls, dish: Dish, remaining: Dict[str, Dict[str, float]]):
        """更新剩余营养需求（用于动态调整后续选菜）"""
        for nutrient, value in dish.nutrients.items():
            if nutrient in remaining:
                # 更新需求值（用于动态评分）
                if "need" in remaining[nutrient]:
                    remaining[nutrient]["need"] = max(0, remaining[nutrient]["need"] - value)

    # 修改  方法，使其更智能
    @classmethod
    def _scale_portions(cls, dishes: List[Dish], meal_range: Dict[str, Dict[str, float]]):
        """
        智能调整份量，确保营养在合理范围内
        """
        if not dishes:
            return

        # 计算当前总营养
        total_nutrients = defaultdict(float)
        for d in dishes:
            for nutrient, value in d.nutrients.items():
                total_nutrients[nutrient] += value

        # 计算每个营养素的缩放比例
        scale_factors = []
        for nutrient, values in meal_range.items():
            current_total = total_nutrients.get(nutrient, 0)
            max_limit = values.get("max", 0)
            min_limit = values.get("min", 0)

            if current_total <= 0 or max_limit <= 0:
                continue

            # 逻辑1：如果超过最大值，需要缩小
            if current_total > max_limit:
                scale = max_limit / current_total
                scale_factors.append(scale)
                print(f"营养超标: {nutrient} 当前{current_total:.1f} > 最大{max_limit:.1f}, 缩放比例: {scale:.2f}")

            # 逻辑2：如果低于最小值，需要放大
            elif current_total < min_limit:
                # 计算需要放大到至少达到最小需求的比例
                # 但不能无限放大，限制最大放大倍数
                scale = min(2.0, min_limit / max(current_total, 1e-6))  # 最多放大2倍
                scale_factors.append(scale)
                print(f"营养不足: {nutrient} 当前{current_total:.1f} < 最小{min_limit:.1f}, 缩放比例: {scale:.2f}")

        # 确定最终缩放比例
        if scale_factors:
            # 如果有需要缩小的比例，优先使用最小的（最严格的限制）
            # 这样可以确保不会超标
            shrink_factors = [s for s in scale_factors if s < 1.0]
            if shrink_factors:
                final_scale = min(shrink_factors)  # 取最小的缩放比例（最严格）
            else:
                # 只有需要放大的情况，取最小的放大比例（最保守）
                final_scale = min(scale_factors)

            # 限制缩放范围在合理区间
            final_scale = max(0.5, min(2.0, final_scale))
            print(f"最终缩放比例: {final_scale:.2f}")
        else:
            final_scale = 1.0  # 不需要调整
            print("营养在合理范围内，无需调整")

        # 应用缩放
        for d in dishes:
            raw = int(d.exact_portion.grams * final_scale)
            raw = max(1, raw)

            # 重新映射外壳
            if raw <= 100:
                size = "S"
            elif raw <= 200:
                size = "M"
            else:
                size = "L"
            d.exact_portion = ExactPortion(size=size, grams=raw)

            # 同时调整营养成分数据（重要！）
            d.nutrients = {k: v * final_scale for k, v in d.nutrients.items()}

    @classmethod
    def _categorize_dishes_by_structure(cls, dish_list: List[Dish]) -> Dict[str, List[Dish]]:
        """根据餐次结构对菜品进行分类"""
        categorized = {
            'main_dish': [],
            'side_dish': [],
            'staple': [],
            'soup': [],
            'baby_food': []
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
                return 'staple'

        # 2. 使用 vege 标签进行荤素分类
        vege_tags = dish_tags.get('vege', [])
        for tag in vege_tags:
            code = tag.get('code', '')
            # 荤菜类别
            if code in ['meat','seafood']:
                return 'main_dish'
            # 素菜类别
            elif code in ['vege', 'vegan', 'egg']:
                return 'side_dish'

        # 3. 使用 category 判断汤品
        category_tags = dish_tags.get('category', [])
        for tag in category_tags:
            code = tag.get('code', '')
            if code in ['soup']:  # 汤品烹饪方法
                return 'soup'
        # 3. 使用 people 判断baby_food
        category_tags = dish_tags.get('people', [])
        for tag in category_tags:
            code = tag.get('code', '')
            if code in ['baby']:
                return 'baby_food'

        # 4. 根据营养素含量进行智能判断
        nutrients = getattr(dish, 'nutrients', {}) or {}
        protein = nutrients.get('Protein', 0)
        carbs = nutrients.get('Carbohydrate', 0)

        # 高碳水且低蛋白的可能是主食
        if carbs > 40 and protein < 10:
            return 'staple'

        # 高蛋白的可能是主菜
        if protein > 20:
            return 'main_dish'
        elif protein > 8:
            return 'side_dish'

        # 5. 最终默认分类
        # 如果以上都无法判断，保守地分类为配菜
        return 'side_dish'
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