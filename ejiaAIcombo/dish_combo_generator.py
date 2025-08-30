# dish_combo_generator.py
import hashlib
from typing import List, Dict, Optional, Set
from dish_combo_models import Dish, ComboMeal, ComboConfig, MemberInfo
from dish_combo_data import DishComboData


class DishComboGenerator:
    CONFIG = ComboConfig()

    @staticmethod
    def generate_family_combo(member_ids: List[int],
                              max_per_meal: Optional[int] = None,
                              filter_allergens: bool = True,
                              meal_type: str = "all",
                              cook_time_config: Optional[Dict[str, int]] = None,
                              portion_config: Optional[Dict[str, str]] = None) -> List[ComboMeal]:
        """
        生成家庭套餐
        - meal_type="all": 生成早中晚三个套餐，营养合计满足全日需求
        - meal_type="breakfast/lunch/dinner": 生成单个套餐，营养按比例分配
        """
        data_handler = DishComboData()

        # 获取基础信息
        member_info = data_handler.get_member_info(member_ids)
        family_allergens = data_handler.get_family_allergens(member_ids)
        nutrient_ranges = DishComboGenerator._get_family_nutrient_ranges(member_ids)

        if meal_type == "all":
            # 生成三个套餐，营养合计满足全日需求
            return DishComboGenerator._generate_all_day_meals(
                member_ids, member_info, nutrient_ranges, family_allergens,
                filter_allergens, max_per_meal, cook_time_config, portion_config
            )
        else:
            # 生成单个套餐，营养按比例分配
            return DishComboGenerator._generate_single_meal(
                member_ids, member_info, nutrient_ranges, family_allergens,
                filter_allergens, meal_type, max_per_meal, cook_time_config, portion_config
            )

    @staticmethod
    def _generate_all_day_meals(member_ids, member_info, full_nutrient_ranges,
                                family_allergens, filter_allergens, max_per_meal,
                                cook_time_config, portion_config):
        """生成全天三个套餐"""
        meals = []

        # 为每个餐型生成套餐
        for meal_type in ["breakfast", "lunch", "dinner"]:
            # 计算该餐型的营养需求比例
            ratio = getattr(DishComboGenerator.CONFIG, f"nutrient_ratio_{meal_type}")
            meal_nutrient_ranges = DishComboGenerator._scale_nutrient_ranges(full_nutrient_ranges, ratio)

            # 获取该餐型的烹饪时间限制
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
            meal = DishComboGenerator._create_single_meal(
                selected_dishes, dish_tags, member_ids, meal_type,
                portion_plan, cook_time_limit
            )
            meals.append(meal)

        return meals

    @staticmethod
    def _generate_single_meal(member_ids, member_info, full_nutrient_ranges,
                              family_allergens, filter_allergens, meal_type,
                              max_per_meal, cook_time_config, portion_config):
        """生成单个套餐"""
        # 计算该餐型的营养需求比例
        ratio = getattr(DishComboGenerator.CONFIG, f"nutrient_ratio_{meal_type}",
                        DishComboGenerator.CONFIG.nutrient_ratio_single)
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
            dishes=dishes,
            total_cook_time=total_cook_time,
            portion_plan=portion_plan
        )
    @staticmethod
    def _calculate_dish_count(member_info: List[MemberInfo], custom_count: Optional[int]) -> int:
        """计算菜品数量"""
        if custom_count is not None:
            return max(2, custom_count)  # 至少2道菜

        # 统计成员结构
        adult_count = sum(1 for m in member_info if m.age > 12)
        child_count = sum(1 for m in member_info if 3 <= m.age <= 12)
        has_toddler = any(m.age < 3 for m in member_info)

        # 自动计算
        total_dishes = (
                DishComboGenerator.CONFIG.base_dish_count +
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

        # 先选择满足特定需求的菜品
        for member_id in member_ids:
            member_needs = data_handler.get_member_specific_needs(member_id)
            for need_code in member_needs:
                matched_dishes = data_handler.get_dishes_by_need(need_code, 5)
                for dish_id, score in matched_dishes:
                    if len(selected_dishes) >= dish_count:
                        break

                    dish = data_handler.get_dish_by_id(dish_id)
                    if not dish:
                        continue

                    # 检查烹饪时间
                    if dish.cook_time > cook_time_limit:
                        continue

                    # 检查过敏原
                    dish_allergens = data_handler.get_dish_allergens(dish_id, family_allergens)
                    if filter_allergens and dish_allergens:
                        continue

                    # 检查主料重复（避免相同主料的菜品）
                    main_ingredient = next(iter(dish.ingredients.keys()), "")
                    if any(main_ingredient in selected_dish.ingredients for selected_dish in selected_dishes):
                        continue

                    # 检查营养贡献
                    if DishComboGenerator._dish_fits_nutrient_range(dish, remaining_nutrients):
                        selected_dishes.append(dish)

                        # 记录需求标签
                        if dish_id not in dish_tags:
                            dish_tags[dish_id] = {"needs": set(), "members": {}}
                        dish_tags[dish_id]["needs"].add(need_code)
                        if member_id not in dish_tags[dish_id]["members"]:
                            dish_tags[dish_id]["members"][member_id] = set()
                        dish_tags[dish_id]["members"][member_id].add(need_code)

                        # 更新剩余营养需求
                        DishComboGenerator._update_nutrient_range(dish, remaining_nutrients)

        # 补充基础营养菜品（使用带烹饪时间限制的菜品池）
        all_dishes = data_handler.get_dish_pool(cook_time_limit)
        for dish in all_dishes:
            if len(selected_dishes) >= dish_count:
                break

            if dish.dish_id in [d.dish_id for d in selected_dishes]:
                continue

            # 检查过敏原
            dish_allergens = data_handler.get_dish_allergens(dish.dish_id, family_allergens)
            if filter_allergens and dish_allergens:
                continue

            # 检查主料重复
            main_ingredient = next(iter(dish.ingredients.keys()), "")
            if any(main_ingredient in selected_dish.ingredients for selected_dish in selected_dishes):
                continue

            if DishComboGenerator._dish_fits_nutrient_range(dish, remaining_nutrients):
                selected_dishes.append(dish)
                DishComboGenerator._update_nutrient_range(dish, remaining_nutrients)

        return selected_dishes, dish_tags

    @staticmethod
    def _assign_portion_sizes(dishes: List[Dish], member_info: List[MemberInfo],
                              custom_config: Optional[Dict[str, str]]) -> Dict[str, List[str]]:
        """分配份量规格"""
        portion_plan = {}

        if custom_config:
            # 使用自定义份量配置
            for dish in dishes:
                dish.portion_size = custom_config.get("default", "M")
            portion_plan["custom"] = [f"{dish.name}: {dish.portion_size}" for dish in dishes]
        else:
            # 智能份量分配
            has_toddler = any(m.age < 3 for m in member_info)
            has_child = any(3 <= m.age <= 12 for m in member_info)

            if has_toddler:
                # 幼儿特殊处理
                toddler_dishes = dishes[:1]
                family_dishes = dishes[1:]

                for dish in toddler_dishes:
                    dish.portion_size = DishComboGenerator.CONFIG.portion_toddler
                for dish in family_dishes:
                    dish.portion_size = DishComboGenerator.CONFIG.portion_adult

                portion_plan["toddler"] = [f"{d.name}: {d.portion_size}" for d in toddler_dishes]
                portion_plan["family"] = [f"{d.name}: {d.portion_size}" for d in family_dishes]

            elif has_child:
                # 儿童和成人区分
                child_count = sum(1 for m in member_info if 3 <= m.age <= 12)
                child_dishes = dishes[:min(child_count, len(dishes))]
                adult_dishes = dishes[len(child_dishes):]

                for dish in child_dishes:
                    dish.portion_size = DishComboGenerator.CONFIG.portion_child
                for dish in adult_dishes:
                    dish.portion_size = DishComboGenerator.CONFIG.portion_adult

                portion_plan["child"] = [f"{d.name}: {d.portion_size}" for d in child_dishes]
                portion_plan["adult"] = [f"{d.name}: {d.portion_size}" for d in adult_dishes]

            else:
                # 全是成人
                for dish in dishes:
                    dish.portion_size = DishComboGenerator.CONFIG.portion_adult
                portion_plan["adult"] = [f"{d.name}: {d.portion_size}" for d in dishes]

        return portion_plan

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