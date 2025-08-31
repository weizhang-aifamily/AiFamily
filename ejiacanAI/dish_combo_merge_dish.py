# dish_combo_merge_dish.py
from __future__ import annotations
import copy
from typing import List, Dict, Optional, Tuple, Set
from ejiacanAI.dish_combo_models import Dish, MemberInfo, MergeConfig


class DishMergeProcessor:
    """智能菜品合并处理器"""

    def __init__(self, merge_config: Optional[MergeConfig] = None):
        self.merge_config = merge_config or MergeConfig()
        self._processed_pairs: Set[Tuple[int, int]] = set()  # 记录已处理的菜品对

    def smart_merge(self, dishes: List[Dish], member_info: List[MemberInfo],
                    nutrient_ranges: Dict[str, Dict[str, float]]) -> List[Dish]:
        """
        智能合并菜品主入口
        逻辑：1.计算目标数量 → 2.渐进式合并 → 3.返回优化后的菜品列表
        """
        member_count = len(member_info)
        target_count = self._get_target_dish_count(member_count, len(dishes))

        # 如果已经在目标范围内或菜品太少，直接返回
        if len(dishes) <= target_count or len(dishes) <= 3:
            return dishes

        # 深度拷贝避免修改原数据
        current_dishes = copy.deepcopy(dishes)
        merge_attempts = 0

        # 渐进式合并：每次合并一对，直到达到目标数量
        while (len(current_dishes) > target_count and
               merge_attempts < self.merge_config.max_merge_per_meal):

            # 找出最适合合并的菜品对
            best_pair = self._find_best_merge_pair(current_dishes)
            if not best_pair:
                break  # 没有可合并的菜品对

            dish1, dish2 = best_pair

            # 创建合并后的菜品
            merged_dish = self._merge_two_dishes(dish1, dish2)

            # 验证合并后的营养是否充足
            temp_dishes = [d for d in current_dishes if d not in [dish1, dish2]]
            temp_dishes.append(merged_dish)

            if self._validate_merge_result(temp_dishes, nutrient_ranges):
                # 合并成功，替换原菜品
                current_dishes = temp_dishes
                merge_attempts += 1
                print(f"✅ 成功合并: {dish1.name} + {dish2.name} → {merged_dish.name}")
            else:
                # 合并失败，标记这对菜品不再尝试
                self._mark_processed_pair(dish1.dish_id, dish2.dish_id)
                print(f"❌ 合并失败: {dish1.name} + {dish2.name} (营养不达标)")

        print(f"📊 合并结果: {len(dishes)}道 → {len(current_dishes)}道菜")
        return current_dishes

    def _find_best_merge_pair(self, dishes: List[Dish]) -> Optional[Tuple[Dish, Dish]]:
        """
        找出最适合合并的菜品对
        逻辑：遍历所有组合，选择得分最高的可合并菜品对
        """
        best_pair = None
        best_score = -1.0

        for i in range(len(dishes)):
            for j in range(i + 1, len(dishes)):
                dish1, dish2 = dishes[i], dishes[j]

                # 检查是否允许合并
                if not self._can_merge_dishes(dish1, dish2):
                    continue

                # 计算合并得分
                score = self._calculate_merge_score(dish1, dish2)

                # 选择得分最高的菜品对
                if score > best_score and score >= self.merge_config.min_similarity_for_merge:
                    best_score = score
                    best_pair = (dish1, dish2)

        return best_pair

    def _can_merge_dishes(self, dish1: Dish, dish2: Dish) -> bool:
        """
        检查两道菜是否允许合并
        逻辑：排除特定类型和已处理过的菜品对
        """
        # 检查是否已处理过
        pair_key = self._get_pair_key(dish1.dish_id, dish2.dish_id)
        if pair_key in self._processed_pairs:
            return False

        # 检查是否为不可合并类型（主食、汤品等）
        for category in self.merge_config.non_mergeable_categories:
            if category in dish1.name or category in dish2.name:
                return False

        # 检查是否有特殊标记不允许合并
        if hasattr(dish1, 'allow_merge') and not dish1.allow_merge:
            return False
        if hasattr(dish2, 'allow_merge') and not dish2.allow_merge:
            return False

        return True

    def _calculate_merge_score(self, dish1: Dish, dish2: Dish) -> float:
        """
        计算两道菜的合并得分（0-1）
        逻辑：营养重叠度(60%) + 需求冗余度(30%) + 优先级适配度(10%)
        """
        nutrient_score = self._calculate_nutrient_overlap(dish1, dish2)
        need_score = self._calculate_need_redundancy(dish1, dish2)
        priority_score = self._calculate_priority_score(dish1, dish2)

        # 加权总分
        total_score = (nutrient_score * 0.6 + need_score * 0.3 + priority_score * 0.1)

        return round(total_score, 2)

    def _calculate_nutrient_overlap(self, dish1: Dish, dish2: Dish) -> float:
        """
        计算营养重叠度：两道菜营养成分的相似程度
        """
        common_nutrients = set(dish1.nutrients.keys()) & set(dish2.nutrients.keys())
        if not common_nutrients:
            return 0.0

        overlap_score = 0.0
        for nutrient in common_nutrients:
            amount1 = dish1.nutrients[nutrient]
            amount2 = dish2.nutrients[nutrient]
            # 使用Jaccard相似度计算
            ratio = min(amount1, amount2) / max(amount1, amount2) if max(amount1, amount2) > 0 else 0
            overlap_score += ratio

        return overlap_score / len(common_nutrients)

    def _calculate_need_redundancy(self, dish1: Dish, dish2: Dish) -> float:
        """
        计算需求冗余度：两道菜满足的需求重叠程度
        """
        if not hasattr(dish1, 'matched_needs') or not hasattr(dish2, 'matched_needs'):
            return 0.0

        common_needs = set(dish1.matched_needs) & set(dish2.matched_needs)
        if not common_needs:
            return 0.0

        # 计算需求重叠比例
        min_needs_count = min(len(dish1.matched_needs), len(dish2.matched_needs))
        return len(common_needs) / min_needs_count

    def _calculate_priority_score(self, dish1: Dish, dish2: Dish) -> float:
        """
        计算优先级适配度：基于配置的优先级规则
        """
        priority1 = self._get_merge_priority(dish1)
        priority2 = self._get_merge_priority(dish2)

        # 优先级越接近，得分越高（鼓励相似优先级的菜品合并）
        priority_diff = abs(priority1 - priority2)
        return 1.0 - (priority_diff / 10.0)  # 标准化到0-1

    def _get_merge_priority(self, dish: Dish) -> int:
        """
        获取菜品合并优先级（数值越小越优先合并）
        """
        # 检查无特定需求
        if not hasattr(dish, 'matched_needs') or not dish.matched_needs:
            return next(priority for rule, priority in self.merge_config.merge_priority_rules
                        if rule == "NO_SPECIFIC_NEEDS")

        # 检查单一需求
        if len(dish.matched_needs) == 1:
            return next(priority for rule, priority in self.merge_config.merge_priority_rules
                        if rule == "SINGLE_NEED")

        # 检查均衡营养
        if 'BALANCED' in dish.matched_needs:
            return next(priority for rule, priority in self.merge_config.merge_priority_rules
                        if rule == "BALANCED_NEED")

        # 默认优先级（核心需求）
        return next(priority for rule, priority in self.merge_config.merge_priority_rules
                    if rule == "CORE_NEED")

    def _merge_two_dishes(self, dish1: Dish, dish2: Dish) -> Dish:
        """
        合并两道菜为一道新菜
        逻辑：智能组合营养成分、食材和需求
        """
        # 创建新菜品
        merged_dish = Dish(
            dish_id=f"merged_{dish1.dish_id}_{dish2.dish_id}",
            name=self._generate_merged_name(dish1.name, dish2.name),
            nutrients={},
            ingredients={},
            cook_time=max(dish1.cook_time, dish2.cook_time),
            portion_size="L"  # 合并后默认大份
        )

        # 合并营养成分（加权平均，避免过量）
        all_nutrients = set(dish1.nutrients.keys()) | set(dish2.nutrients.keys())
        for nutrient in all_nutrients:
            val1 = dish1.nutrients.get(nutrient, 0)
            val2 = dish2.nutrients.get(nutrient, 0)
            # 取90%的平均值，避免营养过量
            merged_dish.nutrients[nutrient] = (val1 + val2) * 0.45

        # 合并食材（保留所有食材）
        merged_dish.ingredients = {**dish1.ingredients, **dish2.ingredients}

        # 合并需求标签
        if hasattr(dish1, 'matched_needs') and hasattr(dish2, 'matched_needs'):
            merged_dish.matched_needs = list(set(dish1.matched_needs) | set(dish2.matched_needs))
        elif hasattr(dish1, 'matched_needs'):
            merged_dish.matched_needs = dish1.matched_needs.copy()
        elif hasattr(dish2, 'matched_needs'):
            merged_dish.matched_needs = dish2.matched_needs.copy()

        # 继承过敏原信息
        if hasattr(dish1, 'allergens') and hasattr(dish2, 'allergens'):
            merged_dish.allergens = list(set(dish1.allergens) | set(dish2.allergens))

        return merged_dish

    def _generate_merged_name(self, name1: str, name2: str) -> str:
        """
        智能生成合并后的菜品名称
        """
        # 根据菜品类型智能命名
        if any(keyword in name1 and keyword in name2 for keyword in ['炒', '煸', '爆']):
            base1 = name1.replace('炒', '').replace('煸', '').replace('爆', '')
            base2 = name2.replace('炒', '').replace('煸', '').replace('爆', '')
            return f"双拼{base1}{base2}"
        elif any(keyword in name1 and keyword in name2 for keyword in ['汤', '羹', '粥']):
            base1 = name1.replace('汤', '').replace('羹', '').replace('粥', '')
            base2 = name2.replace('汤', '').replace('羹', '').replace('粥', '')
            return f"双味{base1}{base2}"
        elif any(keyword in name1 and keyword in name2 for keyword in ['烧', '炖', '焖']):
            return f"合烧{name1[0]}{name2[0]}"
        else:
            return f"{name1}+{name2}组合"

    def _validate_merge_result(self, dishes: List[Dish], nutrient_ranges: Dict[str, Dict[str, float]]) -> bool:
        """
        验证合并后的营养是否满足需求
        """
        # 计算总营养
        total_nutrients = {}
        for dish in dishes:
            for nutrient, amount in dish.nutrients.items():
                total_nutrients[nutrient] = total_nutrients.get(nutrient, 0) + amount

        # 检查每种营养素是否在合理范围内
        for nutrient, range_info in nutrient_ranges.items():
            actual = total_nutrients.get(nutrient, 0)
            min_req = range_info["min"]
            max_req = range_info["max"]

            # 允许20%的误差范围
            if actual < min_req * 0.8:
                return False  # 营养不足
            if actual > max_req * 1.2:
                return False  # 营养过量

        return True

    def _mark_processed_pair(self, dish_id1: int, dish_id2: int):
        """标记一对菜品为已处理（避免重复尝试）"""
        pair_key = self._get_pair_key(dish_id1, dish_id2)
        self._processed_pairs.add(pair_key)

    def _get_pair_key(self, id1: int, id2: int) -> Tuple[int, int]:
        """生成菜品对的唯一键（有序元组）"""
        return (min(id1, id2), max(id1, id2))

    def _get_target_dish_count(self, member_count: int, current_count: int) -> int:
        """获取目标菜品数量"""
        target = self.merge_config.target_dish_counts.get(member_count, member_count + 2)
        return min(current_count, max(3, target))  # 至少3道菜

    def reset_processed_pairs(self):
        """重置已处理的菜品对记录"""
        self._processed_pairs.clear()


# 全局单例实例
_global_merge_processor = DishMergeProcessor()


def smart_merge_dishes(dishes: List[Dish], member_info: List[MemberInfo],
                       nutrient_ranges: Dict[str, Dict[str, float]],
                       merge_config: Optional[MergeConfig] = None) -> List[Dish]:
    """
    全局智能合并函数（方便直接调用）
    """
    if merge_config:
        processor = DishMergeProcessor(merge_config)
    else:
        processor = _global_merge_processor
        processor.reset_processed_pairs()

    return processor.smart_merge(dishes, member_info, nutrient_ranges)