# meal_generator_v2.py
import json
import logging
import random
from typing import List, Dict, Optional
from collections import defaultdict

from ejiacanAI.MealStructureGenerator import MealStructureGenerator
from ejiacanAI.dish2_combo_models import MealRequest, ComboMeal, Dish, ExactPortion, DishFoodNutrient
from ejiacanAI.dish2_combo_data import DishComboData   # 统一数据入口
from models.nutrient_config import MEAL_RATIO, nutrient_priority, structure_def
from models.common_nutrient_calculator import CommonNutrientCalculator

class MealGeneratorV2:
    """
    一次性读取两张视图 → 内存对象列表 → 选菜 → 份量微调 → 打包三餐
    全程无 pandas、无硬编码常量。
    """

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

        # 修改：提取主料（用量最大的食材）- 现在需要从列表结构中提取
        try:
            # 找到用量最大的食材
            main_ingredient_new = max(new.ingredients,
                                      key=lambda x: float(x['grams']))
            main_ingredient_name = main_ingredient_new['name']
        except (ValueError, KeyError):
            # 如果无法确定主料，直接保留
            return new

        # 检查是否与已选菜品主料重复
        for old in existing:
            if not old.ingredients:
                continue
            try:
                # 同样找到已选菜品的主料
                main_ingredient_old = max(old.ingredients,
                                          key=lambda x: float(x['grams']))
                main_ingredient_old_name = main_ingredient_old['name']

                if main_ingredient_name == main_ingredient_old_name:
                    return None  # 主料重复，丢弃新菜
            except (ValueError, KeyError):
                continue

        return new  # 主料不重复，保留新菜

    @classmethod
    def generate_per_meal_default(cls, req: MealRequest) -> List[ComboMeal]:
        dish_list_wide = DishComboData.list_dish_food_nutrient([], req)  # 一次性拉全表
        # 过滤一部分不满足req的dish，如level_la，qingzhen，sushi等，除memberneed
        dish_list = cls.build_true_dishes(dish_list_wide, req)
        # 只保留符合要求的菜系、种类、时间、应季等
        filtered_dishes = cls.filter_dishes(dish_list, req)
        rng = random.Random(req.refresh_key)
        rng.shuffle(filtered_dishes)
        # need_list = DishComboData.list_member_need_nutrient(req.member_ids)
        daily_range = CommonNutrientCalculator.get_daily_range(req.members)

        # 根据请求决定要生成几餐
        if req.meal_type == "all":
            meals_to_build = ["breakfast", "lunch", "dinner"]
        else:
            meals_to_build = [req.meal_type]

        # 逐餐处理
        msg = MealStructureGenerator()
        combo_meals: List[ComboMeal] = []
        for meal_code in meals_to_build:
            meal_range = cls._build_single_meal_range(daily_range, meal_code)
            meal_structure = msg.calculate_meal_config(
                req.members, meal_code, req.province_code
            )
            dishes = cls._select_dishes_for_meal(
                filtered_dishes, meal_range, meal_code, req, meal_structure
            )
            # cls._scale_portions(dishes, meal_range)  # 按餐次独立缩放

            combo_meal = cls._build_combo_meal(meal_code, dishes)
            need_nutrients = cls._build_need_nutrients(meal_range)
            combo_meal.need_nutrients = need_nutrients
            combo_meal.meal_structure = meal_structure
            combo_meals.append(combo_meal)
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
        # need_list = DishComboData.list_member_need_nutrient(req.member_ids)

        daily_range = CommonNutrientCalculator.get_daily_range(req.members)

        # 根据请求决定要生成几餐
        if req.meal_type == "all":
            meals_to_build = ["breakfast", "lunch", "dinner"]
        else:
            meals_to_build = [req.meal_type]

        # 逐餐处理
        msg = MealStructureGenerator()
        combo_meals: List[ComboMeal] = []
        for meal_code in meals_to_build:
            meal_range = cls._build_single_meal_range(daily_range, meal_code)
            meal_structure = msg.calculate_meal_config(
                req.members, meal_code, req.province_code
            )
            dishes = cls._select_dishes_for_meal(
                filtered_dishes, meal_range, meal_code, req, meal_structure
            )
            cls._scale_portions(dishes, meal_range)  # 按餐次独立缩放

            combo_meal = cls._build_combo_meal(meal_code, dishes)
            need_nutrients = cls._build_need_nutrients(meal_range)
            combo_meal.need_nutrients = need_nutrients
            combo_meal.meal_structure = meal_structure
            combo_meals.append(combo_meal)
        return combo_meals

    @classmethod
    def _build_need_nutrients(cls, meal_range: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        从 meal_range 构建 actual_nutrients 格式
        格式与 nutrients 一致：{营养素代码: 目标值}
        """
        actual_nutrients = {}
        for nutrient_code, values in meal_range.items():
            # 使用 need 值作为目标值，如果没有 need 则使用 min 和 max 的平均值
            target_value = values.get("need", 0)
            if target_value == 0:
                target_value = (values.get("min", 0) + values.get("max", 0)) / 2
            actual_nutrients[nutrient_code] = round(target_value, 2)

        return actual_nutrients

    # -------------------------------------------------
    # 为单餐构建需求区间 MEAL_RATIO {"breakfast": 0.30, "lunch": 0.40, "dinner": 0.30}
    # -------------------------------------------------
    @classmethod
    def _build_single_meal_range(
            cls, daily: Dict[str, Dict[str, float]], meal_code: str
    ) -> Dict[str, Dict[str, float]]:
        ratio = MEAL_RATIO[meal_code]
        return {k: {"min": v["min"] * ratio, "max": v["max"] * ratio, "need": v["need"] * ratio}
                for k, v in daily.items()}

    @classmethod
    def _select_dishes_for_meal(
            cls,
            dish_list: List[Dish],
            meal_range: Dict[str, Dict[str, float]],
            meal_code: str,
            req: MealRequest,
            meal_structure: Dict[str, int]
    ) -> List[Dish]:
        """为单餐选择菜品（主要菜品 + 备选菜品）"""

        # 配置参数
        config = cls._get_selection_config()

        # 1. 准备菜品池
        filtered_pool = cls._prepare_dish_pool(dish_list, meal_code, req)
        meal_structure_dished = cls._structure_and_rank_dishes(filtered_pool, req, meal_range)

        # 2. 选择主要菜品
        selected_dishes = cls._select_recommend_dishes(
            meal_structure_dished, meal_structure, req, config
        )

        # 3. 选择备选菜品
        alternative_dishes = cls._select_alternative_dishes(
            meal_structure_dished, selected_dishes, meal_structure, config
        )

        # 4. 补充不足的菜品
        final_dishes = cls._supplement_dishes(
            selected_dishes, alternative_dishes, filtered_pool,
            meal_structure, req, meal_range
        )

        return final_dishes + alternative_dishes

    @classmethod
    def _get_selection_config(cls) -> Dict:
        """获取选择配置"""
        return {
            'alternative_ratio': 0.3,  # 备选菜比例
            'min_alternatives': 1,  # 最少备选菜数量
            'max_alternatives': 3,  # 最多备选菜数量
            'min_nutrition_ratio': 0.8,  # 最低营养满足比例
        }

    @classmethod
    def _prepare_dish_pool(cls, dish_list: List[Dish], meal_code: str, req: MealRequest) -> List[Dish]:
        """准备过滤后的菜品池"""
        # 过敏原过滤
        allergens = set(DishComboData.get_family_allergens(req.member_ids))

        return [
            d for d in dish_list
            if ("all" == meal_code or meal_code in cls.tag_pick(d, 'meal_time', 'code'))
            # and (not req.cook_time_limit or d.cook_time <= req.cook_time_limit)
            # and not allergens.intersection(set(d.allergens))
        ]

    @classmethod
    def _structure_and_rank_dishes(cls, dish_pool: List[Dish], req: MealRequest,
                                    nutrient_range: Dict) -> Dict[str, List[Dish]]:
        """对菜品进行分类和排名"""
        meal_structure_dished = cls._group_dishes_by_structure(dish_pool)
        ranked_dishes = {}

        for category, dishes in meal_structure_dished.items():
            ranked_dishes[category] = cls._rank_dishes_by_score(dishes, req, nutrient_range)

        return ranked_dishes

    @classmethod
    def _rank_dishes_by_score(cls, dishes: List[Dish], req: MealRequest,
                              nutrient_range: Dict) -> List[Dish]:
        """按分数对菜品进行排名（考虑随机性）"""
        if not dishes:
            return []

        # 使用类别相关的随机种子确保刷新变化
        category_rng = random.Random(req.refresh_key + hash(dishes[0].name if dishes else 0))

        # 计算每个菜品的分数
        scored_dishes = []
        for dish in dishes:
            score = cls._calculate_dish_score(dish, req, nutrient_range)
            scored_dishes.append((dish, score))

        # 按分数降序排序
        scored_dishes.sort(key=lambda x: x[1], reverse=True)

        # 对同分数组进行随机打乱
        return cls._shuffle_same_score_groups(scored_dishes, category_rng)

    @classmethod
    def _shuffle_same_score_groups(cls, scored_dishes: List[tuple], rng: random.Random) -> List[Dish]:
        """对相同分数的菜品组进行随机打乱"""
        ranked_dishes = []
        current_score = None
        current_group = []

        for dish, score in scored_dishes:
            if score != current_score:
                if current_group:
                    rng.shuffle(current_group)
                    ranked_dishes.extend(current_group)
                    current_group = []
                current_score = score
            current_group.append(dish)

        if current_group:
            rng.shuffle(current_group)
            ranked_dishes.extend(current_group)

        return ranked_dishes

    @classmethod
    def _select_recommend_dishes(cls, meal_structure_dished: Dict[str, List[Dish]],
                            meal_structure: Dict[str, int], req: MealRequest,
                            config: Dict) -> List[Dish]:
        """选择主要菜品"""
        selected_dishes = []
        total_target = sum(meal_structure.values())

        selection_order = [
            ('staple', meal_structure.get('staple', 1)),
            ('main_dish', meal_structure.get('main_dish', 1)),
            ('baby_food', meal_structure.get('baby_food', 0)),
            ('side_dish', meal_structure.get('side_dish', 0)),
            ('soup', meal_structure.get('soup', 0))
        ]

        for structure_type, target_count in selection_order:
            if target_count == 0:
                continue

            structure_type_dishes = meal_structure_dished.get(structure_type, [])
            selected_from_structure = cls._select_from_structure(
                structure_type_dishes, selected_dishes, target_count, structure_type
            )
            selected_dishes.extend(selected_from_structure)

            # 如果已达到目标数量，提前退出
            if len(selected_dishes) >= total_target:
                break

        return selected_dishes

    @classmethod
    def _select_from_structure(cls, structure_type_dishes: List[Dish], existing_dishes: List[Dish],
                              target_count: int, structure_type: str) -> List[Dish]:
        """从指定类别中选择菜品"""
        selected = []
        existing_dish_ids = set(d.dish_id for d in existing_dishes)

        for dish in structure_type_dishes:
            if len(selected) >= target_count:
                break

            # 检查是否已存在（通过 dish_id）
            if dish.dish_id in existing_dish_ids:
                continue

            # 只进行去重检查，不检查营养范围
            selected_dish = cls._dedup_increase_weight(dish, existing_dishes + selected)
            if selected_dish:
                selected_dish.meal_structure = {structure_type: "selected"}
                selected_dish.is_selected = 1
                selected.append(selected_dish)

        return selected

    @classmethod
    def _select_alternative_dishes(cls, meal_structure_dished: Dict[str, List[Dish]],
                                   selected_dishes: List[Dish], meal_structure: Dict[str, int],
                                   config: Dict) -> List[Dish]:
        """选择备选菜品"""
        alternative_dishes = []

        # 获取已选菜品的ID集合
        selected_dish_ids = set(d.dish_id for d in selected_dishes)

        for structure_type, target_count in meal_structure.items():
            if target_count == 0:
                continue

            structure_type_dishes = meal_structure_dished.get(structure_type, [])
            # 使用 dish_id 来过滤
            available_dishes = [d for d in structure_type_dishes if d.dish_id not in selected_dish_ids]

            if available_dishes:
                alt_count = cls._calculate_alternative_count(
                    target_count, len(available_dishes), config
                )

                # 选择前 alt_count 个菜品作为备选
                for i in range(min(alt_count, len(available_dishes))):
                    alt_dish = available_dishes[i]
                    alt_dish.meal_structure = {structure_type: "alternative"}
                    alt_dish.is_selected = 0
                    alternative_dishes.append(alt_dish)

        return alternative_dishes

    @classmethod
    def _calculate_alternative_count(cls, target_count: int, available_count: int,
                                     config: Dict) -> int:
        """计算应该选择的备选菜数量"""
        # 按目标数量的比例计算
        alt_by_ratio = max(config['min_alternatives'],
                           min(config['max_alternatives'],
                               int(target_count * config['alternative_ratio'])))

        # 按可用菜品数量的比例计算
        alt_by_pool = max(config['min_alternatives'],
                          min(config['max_alternatives'],
                              int(available_count * config['alternative_ratio'])))

        # 取两者中较小的值
        return min(alt_by_ratio, alt_by_pool, available_count)

    @classmethod
    def _supplement_dishes(cls, selected_dishes: List[Dish], alternative_dishes: List[Dish],
                           dish_pool: List[Dish], meal_structure: Dict[str, int],
                           req: MealRequest, nutrient_range: Dict) -> List[Dish]:
        """补充不足的菜品"""
        total_target = sum(meal_structure.values())

        if len(selected_dishes) >= total_target:
            return selected_dishes

        # 准备补充池（排除已选和备选菜品）
        used_dish_ids = set()
        for dish in selected_dishes + alternative_dishes:
            used_dish_ids.add(dish.dish_id)

        supplement_pool = [d for d in dish_pool if d.dish_id not in used_dish_ids]

        # 按分数排序
        supplement_pool.sort(key=lambda d: cls._calculate_dish_score(d, req, nutrient_range),
                             reverse=True)

        # 补充菜品
        supplemented_dishes = selected_dishes.copy()
        for dish in supplement_pool:
            if len(supplemented_dishes) >= total_target:
                break

            selected_dish = cls._dedup_increase_weight(dish, supplemented_dishes)
            if selected_dish:
                selected_dish.meal_structure = {"supplement": "selected"}
                supplemented_dishes.append(selected_dish)

        return supplemented_dishes

    @classmethod
    def _calculate_dish_score(cls, dish: Dish, req: MealRequest, nutrient_range: Dict) -> int:
        """计算菜品分数（考虑标签匹配和营养补充）"""
        base_score = len(dish.explicit_tags)

        # 计算标签匹配度
        if hasattr(req, 'explicit_tags') and req.explicit_tags:
            req_tags = req.explicit_tags
            if isinstance(req_tags, str):
                req_tags = req_tags.split(",")

            matched_tags = set(req_tags) & set(dish.explicit_tags)
            match_score = len(matched_tags) * 2
            base_score += match_score

        # 营养补充加分
        nutrient_bonus = cls._calculate_nutrient_bonus(dish, nutrient_range)
        return base_score + nutrient_bonus

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
        """智能调整份量 - 考虑营养优先级"""
        if not dishes:
            return

        # 1. 计算当前总营养
        total_nutrients = defaultdict(float)
        for d in dishes:
            for nutrient, value in d.nutrients.items():
                total_nutrients[nutrient] += value

        # 3. 分析营养状况
        nutrition_status = {}
        for nutrient, values in meal_range.items():
            current = total_nutrients.get(nutrient, 0)
            min_need = values.get("min", 0)
            max_need = values.get("max", 0)
            need = values.get("need", 0)

            priority = nutrient_priority.get(nutrient, 1)

            nutrition_status[nutrient] = {
                'current': current,
                'min_need': min_need,
                'max_need': max_need,
                'need': need,
                'priority': priority,
                'deficit_ratio': (min_need - current) / min_need if min_need > 0 else 0,
                'excess_ratio': (current - max_need) / max_need if max_need > 0 else 0
            }

        # 4. 分层调整策略
        final_scale = cls._calculate_optimal_scale(nutrition_status, dishes)

        # 5. 应用调整
        if final_scale != 1.0:
            cls._apply_portion_scale(dishes, final_scale)

    @classmethod
    def _calculate_optimal_scale(cls, nutrition_status: Dict, dishes: List[Dish]) -> float:
        """计算最优缩放比例 - 考虑营养优先级"""

        # 策略1：检查关键营养素严重不足
        critical_nutrients = ['protein', 'calories']
        for nutrient in critical_nutrients:
            if nutrient in nutrition_status:
                status = nutrition_status[nutrient]
                if status['current'] < status['min_need'] * 0.8:  # 严重不足
                    # 需要放大，但限制最大倍数
                    required_scale = min(1.5, status['min_need'] / max(status['current'], 1e-6))
                    print(f"⚠️ {nutrient}严重不足，需要放大: {required_scale:.2f}倍")
                    return required_scale

        # 策略2：处理超标营养素（考虑优先级）
        shrink_factors = []
        for nutrient, status in nutrition_status.items():
            if status['current'] > status['max_need']:
                # 高优先级营养素超标 - 轻微缩小
                if status['priority'] >= 8:
                    shrink_factor = 0.9  # 轻微调整
                # 低优先级营养素超标 - 正常缩小
                else:
                    shrink_factor = status['max_need'] / status['current']
                shrink_factors.append(shrink_factor)
                print(f"📉 {nutrient}超标，建议缩小: {shrink_factor:.2f}倍")

        # 策略3：处理不足营养素（考虑优先级）
        expand_factors = []
        for nutrient, status in nutrition_status.items():
            if status['current'] < status['min_need']:
                # 高优先级营养素不足 - 优先满足
                if status['priority'] >= 8:
                    expand_factor = min(1.3, status['min_need'] / max(status['current'], 1e-6))
                    expand_factors.append(expand_factor)
                    print(f"📈 {nutrient}不足，建议放大: {expand_factor:.2f}倍")

        # 策略4：平衡决策
        if shrink_factors:
            # 有超标情况，优先处理（取最严重的）
            final_scale = min(shrink_factors)

            # 但如果有关键营养素严重不足，需要权衡
            critical_deficit = any(
                status['priority'] >= 8 and status['current'] < status['min_need'] * 0.9
                for nutrient, status in nutrition_status.items()
            )

            if critical_deficit and final_scale < 0.8:
                # 不能缩太小，否则关键营养素更不足
                final_scale = max(0.8, final_scale)
                print(f"⚖️ 权衡：关键营养素不足，限制最小缩放为: {final_scale:.2f}")

        elif expand_factors:
            # 只有不足情况，适度放大
            final_scale = min(expand_factors)  # 取最保守的放大
        else:
            # 营养均衡，不需要调整
            final_scale = 1.0

        # 限制调整范围
        final_scale = max(0.5, min(2.0, final_scale))

        if final_scale != 1.0:
            print(f"🎯 最终调整比例: {final_scale:.2f}倍")
        else:
            print("✅ 营养均衡，无需调整")

        return final_scale

    @classmethod
    def _apply_portion_scale(cls, dishes: List[Dish], scale: float):
        """应用份量调整"""
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

            # 调整营养成分数据
            d.nutrients = {k: v * scale for k, v in d.nutrients.items()}

            # 调整食材克数
            for ingredient in d.ingredients:
                try:
                    original_grams = float(ingredient['grams'])
                    adjusted_grams = original_grams * scale
                    ingredient['grams'] = f"{adjusted_grams:.1f}"
                except (ValueError, KeyError):
                    continue

    @classmethod
    def _group_dishes_by_structure(cls, dish_list: List[Dish]) -> Dict[str, List[Dish]]:
        """根据餐次结构对菜品进行分类"""

        for dish in dish_list:
            structure_type = cls._classify_dish_structure_type(dish)
            if structure_type in structure_def:
                structure_def[structure_type].append(dish)

        return structure_def

    @classmethod
    def _classify_dish_structure_type(cls, dish: Dish) -> str:
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
        nutrients = defaultdict(float)  # 新增：营养素汇总

        for d in dishes:
            # 汇总营养素
            for nutrient, value in d.nutrients.items():
                nutrients[nutrient] += value

        name_map = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐"}
        return ComboMeal(
            combo_id=abs(hash(meal_code + str(random.randint(0, 9999)))) % 100000,
            combo_name=name_map.get(meal_code, meal_code),
            meal_type=meal_code,
            dishes=dishes,
            total_cook_time=cook,
            portion_plan={},
            nutrients=dict(nutrients),  # 新增：传入营养素汇总
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
        ingredients: List[Dict[str, str]] = []
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
            ingredients.append({
                'name': first.foodName,
                'grams': f"{float(first.food_amount_grams or 0):.1f}"
            })

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