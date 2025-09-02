# dish_combo_generator.py
import random
from datetime import datetime
import hashlib
from typing import List, Dict, Optional, Set
from ejiacanAI.dish_combo_models import Dish, ComboMeal, ComboConfig, MemberInfo
from ejiacanAI.dish_combo_data import DishComboData
from ejiacanAI.dish_combo_merge_dish import smart_merge_dishes

class DishComboGenerator:
    CONFIG = ComboConfig()

    @staticmethod
    def generate_family_combo(member_ids: List[int],
                              max_per_meal: Optional[int] = None,
                              filter_allergens: bool = True,
                              meal_type: str = "all",
                              cook_time_config: Optional[Dict[str, int]] = None,
                              portion_config: Optional[Dict[str, str]] = None,
                              refresh_key: int = 0
                              ) -> List[ComboMeal]:
        """
        生成家庭套餐
        - meal_type="all": 生成早中晚三个套餐，营养合计满足全日需求
        - meal_type="breakfast/lunch/dinner": 生成单个套餐，营养按比例分配
        """
        seed_str = f"{sorted(member_ids)}-{datetime.now().strftime('%Y%m%d')}-{refresh_key}"
        random.seed(hash(seed_str) % (2 ** 32))

        data_handler = DishComboData()
        # 获取基础信息
        member_info = data_handler.get_member_info(member_ids)
        family_allergens = data_handler.get_family_allergens(member_ids)
        nutrient_ranges = DishComboGenerator._get_family_nutrient_ranges(member_ids)

        if meal_type == "all":
            # 生成三个套餐，营养合计满足全日需求
            meals = []
            for meal_type in ["breakfast", "lunch", "dinner"]:
                meal = DishComboGenerator._generate_meal_for_type(
                    member_ids, member_info, nutrient_ranges, family_allergens,
                    filter_allergens, meal_type, max_per_meal, cook_time_config, portion_config
                )
                meals.append(meal)
            return meals
        else:
            # 生成单个套餐，营养按比例分配
            return DishComboGenerator._generate_meal_for_type(
                member_ids, member_info, nutrient_ranges, family_allergens,
                filter_allergens, meal_type, max_per_meal, cook_time_config, portion_config
            )

    @staticmethod
    def _generate_meal_for_type(member_ids, member_info, full_nutrient_ranges,
                                family_allergens, filter_allergens, meal_type,
                                max_per_meal, cook_time_config, portion_config):
        """生成指定类型的套餐"""
        # 计算该餐型的营养需求比例
        ratio_attr = f"nutrient_ratio_{meal_type}" if meal_type != "all" else "nutrient_ratio_single"
        ratio = getattr(DishComboGenerator.CONFIG, ratio_attr)
        meal_nutrient_ranges = DishComboGenerator._scale_nutrient_ranges(full_nutrient_ranges, ratio)

        # 获取烹饪时间限制
        cook_time_limit = DishComboGenerator._get_cooking_time_limit(meal_type, cook_time_config)

        # 计算菜品数量
        dish_count = DishComboGenerator._calculate_dish_count(member_info, max_per_meal)

        # 选择菜品
        selected_dishes, dish_tags = DishComboGenerator._select_dishes(
            member_ids, dish_count, meal_nutrient_ranges, family_allergens,
            filter_allergens, cook_time_limit
        )

        # 分配份量
        portion_plan = DishComboGenerator._assign_portion_sizes(
            selected_dishes, member_info, portion_config
        )

        # 创建套餐
        return DishComboGenerator._create_single_meal(
            selected_dishes, dish_tags, member_ids, meal_type,
            portion_plan, cook_time_limit
        )

    @staticmethod
    def _scale_nutrient_ranges(nutrient_ranges: Dict[str, Dict[str, float]], ratio: float) -> Dict[
        str, Dict[str, float]]:
        """按比例缩放营养需求区间"""
        scaled_ranges = {}
        for nutrient, range_info in nutrient_ranges.items():
            scaled_ranges[nutrient] = {
                "min": range_info["min"] * ratio,
                "max": range_info["max"] * ratio
            }
        return scaled_ranges

    @staticmethod
    def _create_single_meal(dishes, dish_tags, member_ids, meal_type, portion_plan, cook_time_limit):
        """创建单个套餐"""
        # 获取成员信息和营养需求
        member_info = DishComboData.get_member_info(member_ids)
        nutrient_ranges = DishComboGenerator._get_family_nutrient_ranges(member_ids)

        print(f"🍽️ 合并前: {len(dishes)}道菜")

        # 调用智能合并（关键修改）
        merged_dishes = smart_merge_dishes(
            dishes,
            member_info,
            nutrient_ranges,
            DishComboGenerator.CONFIG.merge_config
        )
        # 将需求信息从 dish_tags 设置到每个菜品的 matched_needs 中
        for dish in merged_dishes:
            if dish.dish_id in dish_tags:
                dish.matched_needs = list(dish_tags[dish.dish_id]["needs"])
            else:
                dish.matched_needs = ["BALANCED"]  # 默认基础需求

        print(f"🍽️ 合并后: {len(merged_dishes)}道菜")
        combo_id = int(
            hashlib.md5(
                f"{'-'.join(map(str, member_ids))}-{meal_type}".encode()
            ).hexdigest(),
            16
        ) % 100000
        # 收集所有需求标签
        all_needs = set()
        for tags in dish_tags.values():
            all_needs.update(tags["needs"])

        # 计算总烹饪时间
        total_cook_time = sum(dish.cook_time for dish in dishes)

        return ComboMeal(
            combo_id=combo_id,
            combo_name=DishComboGenerator._generate_meal_name(meal_type, list(all_needs)),
            need_codes=list(all_needs),
            meal_type=meal_type,
            dishes=merged_dishes,
            total_cook_time=total_cook_time,
            portion_plan=portion_plan
        )
    @staticmethod
    def _calculate_dish_count(member_info: List[MemberInfo], custom_count: Optional[int]) -> int:
        """计算菜品数量"""
        if custom_count is not None:
            return max(2, custom_count)  # 至少2道菜

        # 统计成员结构
        elder_count = sum(1 for m in member_info if m.age >= 70)
        adult_count = sum(1 for m in member_info if 10 < m.age < 70)
        child_count = sum(1 for m in member_info if 3 <= m.age <= 10)
        has_toddler = any(m.age < 3 for m in member_info)

        # 自动计算
        total_dishes = (
                DishComboGenerator.CONFIG.base_dish_count +
                elder_count * DishComboGenerator.CONFIG.dish_per_elder +
                adult_count * DishComboGenerator.CONFIG.dish_per_adult +
                child_count * DishComboGenerator.CONFIG.dish_per_child +
                (DishComboGenerator.CONFIG.toddler_extra_dish if has_toddler else 0)
        )

        return max(2, total_dishes)

    @staticmethod
    def _get_cooking_time_limit(meal_type: str, custom_times: Optional[Dict[str, int]]) -> int:
        """获取烹饪时间限制"""
        default_times = {
            'breakfast': DishComboGenerator.CONFIG.cook_time_breakfast,
            'lunch': DishComboGenerator.CONFIG.cook_time_lunch,
            'dinner': DishComboGenerator.CONFIG.cook_time_dinner,
            'all': DishComboGenerator.CONFIG.cook_time_all
        }

        if custom_times:
            merged_times = {**default_times, **custom_times}
            return merged_times.get(meal_type, DishComboGenerator.CONFIG.cook_time_all)
        else:
            return default_times.get(meal_type, DishComboGenerator.CONFIG.cook_time_all)

    @staticmethod
    def _get_family_nutrient_ranges(member_ids: List[int]) -> Dict[str, Dict[str, float]]:
        """获取家庭营养需求区间"""
        data_handler = DishComboData()
        nutrient_ranges = {}

        for member_id in member_ids:
            member_ranges = data_handler.get_member_nutrient_range(member_id)
            for nutrient, range_info in member_ranges.items():
                if nutrient not in nutrient_ranges:
                    nutrient_ranges[nutrient] = {"min": 0, "max": 0}
                nutrient_ranges[nutrient]["min"] += range_info["min"]
                nutrient_ranges[nutrient]["max"] += range_info["max"]

        return nutrient_ranges

    @staticmethod
    def _select_dishes(member_ids, dish_count, nutrient_ranges, family_allergens, filter_allergens, cook_time_limit):
        """选择菜品并匹配需求"""
        data_handler = DishComboData()
        selected_dishes = []
        dish_tags = {}
        remaining_nutrients = nutrient_ranges.copy()

        # 获取成员需求映射
        member_needs_map = data_handler.get_need_pool(member_ids)

        # 先选择满足特定需求的菜品
        all_need_codes = list({code for needs in member_needs_map.values() for code in needs})
        candidate_dishes = data_handler.get_dishes_by_any_needs(all_need_codes, 30)
        random.shuffle(candidate_dishes)
        # 1) 把 3 个因子归一化到 0~1
        m_ratio = min(1.0, len(member_ids) / 6.0)  # 最多算 6 人
        n_ratio = min(1.0, len(all_need_codes) / 8.0)  # 最多算 8 种需求
        base = max(2, dish_count * 0.5)  # 至少留 50% 给补充菜

        # 2) 加权求候选数
        candidate_size = int(
            base
            + m_ratio * dish_count * 0.25  # 成员权重
            + n_ratio * dish_count * 0.20  # 需求权重
        )

        # 3) 软上限：保证最后至少有 2 道补充菜
        candidate_size = min(candidate_size, dish_count - 2)
        candidate_size = max(candidate_size, 2)  # 下限 2
        candidate_dishes = candidate_dishes[:max(0, candidate_size)]

        for dish in candidate_dishes:
            if len(selected_dishes) >= dish_count:
                break
            processed = DishComboGenerator._process_dish_for_selection(
                dish.dish_id, data_handler, cook_time_limit,
                family_allergens, filter_allergens,
                selected_dishes, remaining_nutrients
            )
            if processed:
                selected_dishes.append(processed)
                # 记录需求标签
                if dish.dish_id not in dish_tags:
                    dish_tags[dish.dish_id] = {"needs": set(), "members": {}}
                dish_tags[dish.dish_id]["needs"].update(dish.matched_needs)
                for mid in member_needs_map:
                    if mid not in dish_tags[dish.dish_id]["members"]:
                        dish_tags[dish.dish_id]["members"][mid] = set()
                    dish_tags[dish.dish_id]["members"][mid].update(dish.matched_needs)
                DishComboGenerator._update_nutrient_range(processed, remaining_nutrients)
        # ✅ 新增：给每道菜增加随机扰动分（0.8~1.2倍）
        for dish in selected_dishes:
            dish.random_boost = random.uniform(0.8, 1.2)
        selected_dishes.sort(
            key=lambda d: (d.match_score or 0) * d.random_boost,
            reverse=True
        )
        # 补充基础营养菜品
        all_dishes = data_handler.get_dish_pool(cook_time_limit)
        # ✅ 新增：给每道菜增加随机扰动分（0.8~1.2倍）
        for dish in all_dishes:
            dish.random_boost = random.uniform(0.8, 1.2)
        all_dishes.sort(
            key=lambda d: (d.match_score or 0) * d.random_boost,
            reverse=True
        )

        for dish in all_dishes:
            if len(selected_dishes) >= dish_count:
                break

            if dish.dish_id in [d.dish_id for d in selected_dishes]:
                continue

            processed_dish = DishComboGenerator._process_dish_for_selection(
                dish.dish_id, data_handler, cook_time_limit, family_allergens,
                filter_allergens, selected_dishes, remaining_nutrients
            )

            if processed_dish:
                selected_dishes.append(processed_dish)
                DishComboGenerator._update_nutrient_range(processed_dish, remaining_nutrients)

        return selected_dishes, dish_tags

    @staticmethod
    def _process_dish_for_selection(dish_id, data_handler, cook_time_limit, family_allergens,
                                    filter_allergens, selected_dishes, remaining_nutrients):
        """处理菜品选择的各种检查逻辑"""
        dish = data_handler.get_dish_by_id(dish_id)
        if not dish:
            return None

        # 检查烹饪时间
        if dish.cook_time > cook_time_limit:
            return None

        # 检查过敏原
        dish_allergens = data_handler.get_dish_allergens(dish_id, family_allergens)
        dish.allergens = dish_allergens
        if filter_allergens and dish_allergens:
            return None

        # 检查主料重复
        main_ingredient = next(iter(dish.ingredients.keys()), "")
        if any(main_ingredient in selected_dish.ingredients for selected_dish in selected_dishes):
            return None

        # 检查营养贡献
        if not DishComboGenerator._dish_fits_nutrient_range(dish, remaining_nutrients):
            return None

        return dish

    @staticmethod
    def _assign_portion_sizes(dishes: List[Dish], member_info: List[MemberInfo],
                              custom_config: Optional[Dict[str, str]]) -> Dict[str, List[str]]:
        """
        分配份量规格（带营养优化合并）
        返回每道菜最终的份量规格，前端直接使用
        """
        # 如果有自定义配置，直接使用
        if custom_config:
            for dish in dishes:
                dish.portion_size = custom_config.get("default", "M")
            return {"dishes": [f"{dish.name}:{dish.portion_size}" for dish in dishes]}

        # 智能营养合并逻辑
        return DishComboGenerator._assign_portions_intelligent(dishes, member_info)

    @staticmethod
    def _assign_portions_intelligent(dishes: List[Dish], member_info: List[MemberInfo]) -> Dict[str, List[str]]:
        """智能份量分配：真正实现营养合并"""
        # 1. 计算总营养需求
        total_nutrient_needs = DishComboGenerator._calculate_total_nutrient_needs(member_info)

        # 2. 计算当前菜品的总营养供给
        current_nutrients = DishComboGenerator._calculate_dish_nutrients(dishes, "M")  # 按中份计算基准

        # 3. 找出需要调整的营养素
        adjustments = DishComboGenerator._calculate_nutrient_adjustments(current_nutrients, total_nutrient_needs)

        # 4. 智能调整份量
        DishComboGenerator._adjust_dish_portions(dishes, adjustments)

        # 5. 返回最终结果（前端直接使用）
        portion_list = [f"{dish.name}:{dish.portion_size}" for dish in dishes]
        return {"dishes": portion_list}

    @staticmethod
    def _calculate_total_nutrient_needs(member_info: List[MemberInfo]) -> Dict[str, float]:
        """估算总营养需求（简化版）"""
        total_needs = {}
        for member in member_info:
            # 简化的营养需求估算，可根据实际业务调整
            base = 1000  # 基础需求
            if member.age < 3:
                multiplier = 0.5  # 幼儿
            elif member.age <= 12:
                multiplier = 0.8  # 儿童
            else:
                multiplier = 1.0  # 成人

            # 累加各营养素的估算需求
            for nutrient in ["calcium", "protein", "iron"]:  # 示例营养素
                total_needs[nutrient] = total_needs.get(nutrient, 0) + base * multiplier

        return total_needs

    @staticmethod
    def _calculate_dish_nutrients(dishes: List[Dish], base_size: str) -> Dict[str, float]:
        """计算当前菜品的总营养供给"""
        total_nutrients = {}
        ratio = DishComboGenerator.CONFIG.portion_ratios.get(base_size, 1.0)

        for dish in dishes:
            for nutrient, amount in dish.nutrients.items():
                total_nutrients[nutrient] = total_nutrients.get(nutrient, 0) + amount * ratio

        return total_nutrients

    @staticmethod
    def _calculate_nutrient_adjustments(current_nutrients: Dict[str, float],
                                        total_needs: Dict[str, float]) -> Dict[str, float]:
        """计算需要调整的营养素比例"""
        adjustments = {}
        for nutrient, current_amount in current_nutrients.items():
            if nutrient in total_needs and total_needs[nutrient] > 0:
                ratio = current_amount / total_needs[nutrient]
                adjustments[nutrient] = ratio
        return adjustments

    @staticmethod
    def _adjust_dish_portions(dishes: List[Dish], adjustments: Dict[str, float]):
        """根据营养调整需求智能分配份量"""
        # 按营养密度排序（高营养密度的菜优先调整）
        dishes_sorted = sorted(dishes,
                               key=lambda d: sum(d.nutrients.values()) / max(d.cook_time, 1),
                               reverse=True)

        for dish in dishes_sorted:
            # 计算这道菜的营养调整得分
            adjust_score = 0
            for nutrient, ratio in adjustments.items():
                if nutrient in dish.nutrients:
                    # 如果这种营养素不足，且这道菜富含该营养素，则应该加大份量
                    if ratio < 0.8:  # 不足
                        adjust_score += dish.nutrients[nutrient] * (1 - ratio)
                    elif ratio > 1.2:  # 过剩
                        adjust_score -= dish.nutrients[nutrient] * (ratio - 1)

            # 根据调整得分决定份量
            if adjust_score > 50:  # 富含不足的营养素
                dish.portion_size = "L"
            elif adjust_score < -30:  # 富含过剩的营养素
                dish.portion_size = "S"
            else:
                dish.portion_size = "M"
    @staticmethod
    def _create_meal_combos(dishes, dish_tags, member_ids, meal_type, portion_plan, cook_time_limit):
        """创建最终套餐"""
        combo_id = int(
            hashlib.md5("-".join(map(str, member_ids)).encode()).hexdigest(), 16
        ) % 100000

        # 收集所有需求标签
        all_needs = set()
        for tags in dish_tags.values():
            all_needs.update(tags["needs"])

        # 计算总烹饪时间
        total_cook_time = sum(dish.cook_time for dish in dishes)

        combo = ComboMeal(
            combo_id=combo_id,
            combo_name=DishComboGenerator._generate_meal_name(meal_type, list(all_needs)),
            need_codes=list(all_needs),
            meal_type=meal_type,
            dishes=dishes,
            total_cook_time=total_cook_time,
            portion_plan=portion_plan,
        )

        return [combo]


    # 辅助方法...
    @staticmethod
    def _dish_fits_nutrient_range(dish, remaining_nutrients):
        """检查菜品是否适合当前营养区间"""
        for nutrient, amount in dish.nutrients.items():
            if nutrient in remaining_nutrients:
                remaining_min = remaining_nutrients[nutrient]["min"]
                if amount > remaining_min * 1.5:  # 避免单菜品营养过量
                    return False
        return True


    @staticmethod
    def _update_nutrient_range(dish, remaining_nutrients):
        """更新剩余营养需求"""
        for nutrient, amount in dish.nutrients.items():
            if nutrient in remaining_nutrients:
                remaining_nutrients[nutrient]["min"] = max(0, remaining_nutrients[nutrient]["min"] - amount)
                remaining_nutrients[nutrient]["max"] = max(0, remaining_nutrients[nutrient]["max"] - amount)


    @staticmethod
    def _generate_meal_name(meal_type: str, need_codes: List[str]) -> str:
        """生成套餐名称"""
        meal_names = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐", "all": "全日餐"}
        base_name = meal_names.get(meal_type, "套餐")

        if not need_codes:
            return f"营养{base_name}"

        need_mapping = {
            "HIGH_CALCIUM": "高钙", "HIGH_PROTEIN": "高蛋白", "LOW_FAT": "低脂",
            "HIGH_FIBER": "高纤", "LOW_SODIUM": "低钠", "LOW_SUGAR": "低糖",
            "RICH_IRON": "富铁", "RICH_VITAMIN": "富维", "BALANCED": "均衡"
        }

        main_needs = []
        for code in need_codes:
            if code in need_mapping:
                main_needs.append(need_mapping[code])
            if len(main_needs) >= 2:
                break

        return f"{'·'.join(main_needs)}{base_name}" if main_needs else f"营养{base_name}"


if __name__ == "__main__":
    # 基本使用
    combos = DishComboGenerator.generate_family_combo([1, 2, 3])
    for c in combos:
        print("=== 默认配置生成的套餐 ===")
        print(f"套餐ID: {c.combo_id}")
        print(f"套餐名: {c.combo_name}")
        print(f"餐次: {c.meal_type}")
        print(f"总烹饪时间: {c.total_cook_time} 分钟")
        print("包含菜品:")
        for d in c.dishes:
            print(f"  - {d.name}（{d.portion_size}）")
        print("份量计划:")
        for k, v in c.portion_plan.items():
            print(f"  {k}: {v}")
        print()

    # 自定义配置使用
    combos_custom = DishComboGenerator.generate_family_combo(
        member_ids=[1, 2, 3],
        max_per_meal=4,
        meal_type="lunch",
        cook_time_config={"lunch": 40},
        portion_config={"default": "L"}
    )
    combos_custom = [combos_custom]
    for c in combos_custom:
        print("=== 自定义配置生成的套餐 ===")
        print(f"套餐ID: {c.combo_id}")
        print(f"套餐名: {c.combo_name}")
        print(f"餐次: {c.meal_type}")
        print(f"总烹饪时间: {c.total_cook_time} 分钟")
        print("包含菜品:")
        for d in c.dishes:
            print(f"  - {d.name}（{d.portion_size}）")
        print("份量计划:")
        for k, v in c.portion_plan.items():
            print(f"  {k}: {v}")