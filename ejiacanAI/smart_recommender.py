from typing import List, Dict, Optional
from dataclasses import dataclass
import random
from ejiacanAI.models import RecommendationConfig, NeedInfo, MemberConstraints, FamilyNeed
from ejiacanAI.data_access import EnhancedDataAccess
import logging

logger = logging.getLogger(__name__)


class SmartRecommender:
    def __init__(self, data_access: EnhancedDataAccess, config: Optional[RecommendationConfig] = None):
        self.data_access = data_access
        self.config = config or RecommendationConfig()
        logger.info("SmartRecommender initialized with config: %s", self.config)

    def recommend(self, member_ids: List[int], meal_type: str = None,
                  max_results: int = 10) -> List[Dict]:
        """
        智能推荐主入口
        """
        try:
            # 1. 获取成员需求信息
            needs_info = self.data_access.get_member_needs(member_ids)

            # 2. 获取成员约束条件
            constraints = self.data_access.get_member_constraints(member_ids)

            # 3. 根据需求场景选择推荐策略
            if not needs_info.all_need_codes:
                recommendations = self.data_access.get_popular_dishes(constraints, max_results * 2)
            elif len(needs_info.all_need_codes) == 1:
                recommendations = self.data_access.get_dishes_for_need(
                    needs_info.all_need_codes[0], constraints, self.config.min_match_score, max_results * 3
                )
            else:
                recommendations = self.data_access.get_dishes_for_multiple_needs(
                    needs_info.all_need_codes, constraints, needs_info.need_weights, max_results * 4
                )


            # 增加多样性 TODO
            # processed_recommendations = self._add_more_recommendations(
            #     recommendations, meal_type, needs_info, max_results
            # )

            return recommendations

        except Exception as e:
            logger.error("Error in recommendation: %s", str(e))
            return self._get_fallback_recommendations(member_ids, max_results)

    # 从成员需求拼出 FamilyNeed
    def _build_family_need(self, member_ids: List[int]) -> FamilyNeed:
        # ejia_member_daily_nutrient_actual
        calcium_total = 0
        iron_total = 0
        sodium_total = 2000  # 每人 2000mg，示例
        purine_total = 300
        kcal_total = 600  # 单餐示例
        for mid in member_ids:
            # TODO: 按年龄性别查 nutrient_rni_template 求和
            calcium_total += 800
            iron_total += 12
        return FamilyNeed(
            calcium_target=calcium_total,
            iron_target=iron_total,
            sodium_limit=sodium_total,
            purine_limit=purine_total,
            kcal_limit=kcal_total
        )

    def _add_more_recommendations(self, recommendations: List[Dict],
                                      meal_type: str, needs_info: NeedInfo,
                                      max_results: int) -> List[Dict]:
        """后处理推荐结果"""
        if not recommendations:
            return []

        # 去重
        unique_recommendations = {}
        for rec in recommendations:
            if rec['dish_id'] not in unique_recommendations:
                unique_recommendations[rec['dish_id']] = rec

        recommendations = list(unique_recommendations.values())

        # 确保多样性
        if len(needs_info.all_need_codes) > 1:
            recommendations = self._ensure_diversity(recommendations, needs_info.all_need_codes)

        # 排序并限制数量
        recommendations.sort(key=lambda x: x['final_score'], reverse=True)
        return recommendations[:max_results]

    def _ensure_diversity(self, recommendations: List[Dict], need_codes: List[str]) -> List[Dict]:
        """确保推荐结果的多样性"""
        if len(recommendations) <= 10:  # 数量少时不需要多样性处理
            return recommendations

        # 按主要需求分组
        dish_groups = {code: [] for code in need_codes}

        for rec in recommendations:
            # 找到匹配度最高的需求
            best_match = max(need_codes, key=lambda code: self._get_need_match_score(rec, code))
            dish_groups[best_match].append(rec)

        # 从每个组中选取代表性菜品
        diverse_recommendations = []
        for code, dishes in dish_groups.items():
            if dishes:
                # 取每个组的前2名
                diverse_recommendations.extend(
                    sorted(dishes, key=lambda x: x.get('weighted_score', 0), reverse=True)[:2])

        # 如果多样性处理后的结果太少，补充一些高分菜品
        if len(diverse_recommendations) < 8:
            top_dishes = sorted(recommendations, key=lambda x: x.get('weighted_score', 0), reverse=True)[:10]
            diverse_recommendations.extend(top_dishes)

        # 去重
        unique_dishes = {dish['id']: dish for dish in diverse_recommendations}
        return list(unique_dishes.values())

    def _calculate_final_score(self, dish: Dict) -> float:
        """计算最终评分（健壮版本）"""
        # 获取基础匹配分数
        base_score = 0.0
        if 'weighted_score' in dish and dish['weighted_score'] is not None:
            base_score = float(dish['weighted_score'])
        elif 'match_score' in dish and dish['match_score'] is not None:
            base_score = float(dish['match_score'])

        # 安全处理评分
        rating_score = 0.6  # 默认值
        try:
            rating_value = dish.get('rating')
            if rating_value is not None:
                if isinstance(rating_value, str):
                    rating_value = float(rating_value.strip())
                elif isinstance(rating_value, (int, float)):
                    rating_value = float(rating_value)
                else:
                    rating_value = 3.0
            else:
                rating_value = 3.0

            # 确保评分在0-5范围内，然后归一化到0-1
            rating_value = max(0, min(5, rating_value))
            rating_score = rating_value / 5.0

        except (ValueError, TypeError, AttributeError) as e:
            logger.debug("Rating conversion failed for dish %s: %s", dish.get('id'), str(e))
            # 使用默认评分

        # 加权计算最终分数
        return (base_score * 0.7) + (rating_score * 0.3)

    def _get_matched_needs(self, dish: Dict, all_need_codes: List[str]) -> List[Dict]:
        """获取匹配的需求信息"""
        matched_needs = []
        matched_needs.append({
            'need_code': dish['matched_needs_codes'],

        })
        # for need_code in all_need_codes:
        #     score = self._get_need_match_score(dish, need_code)
        #     if score >= self.config.min_match_score:
        #         matched_needs.append({
        #             'need_code': need_code,
        #             'match_score': score,
        #             'explanation': self._generate_explanation(need_code, score)
        #         })
        return matched_needs

    def _get_need_match_score(self, dish: Dict, need_code: str) -> float:
        """获取菜品对特定需求的匹配分数"""
        # 方法1: 从预计算的数据中获取
        if 'matched_need_codes' in dish and dish['matched_need_codes']:
            matched_codes = dish['matched_need_codes'].split(',')
            if need_code in matched_codes:
                # 如果有加权分数，使用加权分数
                if 'weighted_score' in dish:
                    return float(dish.get('weighted_score', 0))
                # 否则使用基础匹配分数
                return float(dish.get('match_score', 0))

        # 方法2: 如果没有预计算数据，返回0
        return 0.0

    def _generate_explanation(self, need_code: str, match_score: float) -> str:
        """生成匹配解释"""
        explanations = {
            'highCalcium': "富含钙质，有助于骨骼健康",
            'highIron': "铁含量丰富，有助于补血",
            'lowFat': "低脂肪，适合控制体重",
            'lowSalt': "低盐配方，适合高血压人群",
            'HIGH_PROTEIN': "高蛋白，有助于肌肉生长",
            'LOW_FAT': "低脂肪，健康选择"
        }
        return explanations.get(need_code, f"符合{need_code}需求")

    def _get_fallback_recommendations(self, member_ids: List[int], max_results: int) -> List[Dict]:
        """获取降级推荐"""
        try:
            constraints = self.data_access.get_member_constraints(member_ids)
            return self.data_access.get_popular_dishes(constraints, max_results)
        except Exception as e:
            logger.error("Fallback recommendation also failed: %s", str(e))
            return []