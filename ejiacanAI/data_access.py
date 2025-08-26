from typing import List, Dict, Optional
from ejiacanAI.models import Dish, FamilyNeed, MemberConstraints, NeedInfo, RecommendationConfig
import logging

logger = logging.getLogger(__name__)


class EnhancedDataAccess:
    def __init__(self, db):
        self.db = db

    def get_member_needs(self, member_ids: List[int]) -> NeedInfo:
        """获取成员需求信息（包含权重）"""
        ids_str = ','.join(map(str, member_ids))

        sql = f"""
            SELECT 
                dn.member_id,
                dn.need_code,
                edn.name as need_name,
                COUNT(*) OVER (PARTITION BY dn.need_code) as need_frequency
            FROM ejia_member_diet_need dn
            JOIN ejia_enum_diet_need_tbl edn ON dn.need_code = edn.code
            WHERE dn.member_id IN ({ids_str})
        """

        rows = self.db.query(sql)

        member_needs = {}
        all_need_codes = set()
        need_weights = {}

        for row in rows:
            member_id = row['member_id']
            need_code = row['need_code']

            if member_id not in member_needs:
                member_needs[member_id] = []

            member_needs[member_id].append({
                'code': need_code,
                'name': row['need_name']
            })

            all_need_codes.add(need_code)
            need_weights[need_code] = row['need_frequency']

        return NeedInfo(
            member_needs=member_needs,
            all_need_codes=list(all_need_codes),
            need_weights=need_weights
        )

    def get_member_constraints(self, member_ids: List[int]) -> MemberConstraints:
        """获取成员约束条件"""
        ids_str = ','.join(map(str, member_ids))

        # 获取过敏信息
        allergy_sql = f"""
            SELECT DISTINCT ma.member_id
            FROM ejia_member_allergen ma
            WHERE ma.member_id IN ({ids_str})
        """
        allergy_rows = self.db.query(allergy_sql)
        allergy_member_ids = [row['member_id'] for row in allergy_rows]

        return MemberConstraints(allergy_member_ids=allergy_member_ids)

    def get_dishes_for_need(self, need_code: str, constraints: MemberConstraints,
                            min_score: float = 0.6, limit: int = 50) -> List[Dict]:
        """根据单一需求获取菜品（适应纵表结构）"""
        member_ids_str = ','.join(map(str, constraints.allergy_member_ids)) if constraints.allergy_member_ids else '-1'

        sql = f"""
            SELECT 
                d.id as dish_id,
                d.name,
                d.emoji,
                d.default_portion_g,
                d.max_servings,
                d.rating,
                nm.match_score,
                nm.need_code,
                -- 获取营养成分
                MAX(CASE WHEN dnl.nutrient_name = '钙' THEN dnl.nutrient_amount END) as calcium,
                MAX(CASE WHEN dnl.nutrient_name = '铁' THEN dnl.nutrient_amount END) as iron,
                MAX(CASE WHEN dnl.nutrient_name = '钠' THEN dnl.nutrient_amount END) as sodium,
                MAX(CASE WHEN dnl.nutrient_name = '脂肪' THEN dnl.nutrient_amount END) as fat,
                MAX(CASE WHEN dnl.nutrient_name = '蛋白质' THEN dnl.nutrient_amount END) as protein,
                MAX(CASE WHEN dnl.nutrient_name = '膳食纤维' THEN dnl.nutrient_amount END) as fiber,
                MAX(CASE WHEN dnl.nutrient_name = '嘌呤' THEN dnl.nutrient_amount END) as purine,
                MAX(CASE WHEN dnl.nutrient_name = '热量' THEN dnl.nutrient_amount END) as kcal
            FROM ejia_need_dish_match nm
            JOIN ejia_dish d ON d.id = nm.dish_id
            LEFT JOIN view_dish_nutrients_long dnl ON dnl.dish_id = d.id
            WHERE nm.need_code = %s
            AND nm.match_score >= %s
            AND d.id NOT IN (
                SELECT DISTINCT dfr.dish_id
                FROM ejia_dish_food_rel dfr
                JOIN ejia_enum_allergen_tbl ea ON ea.food_id = dfr.food_id
                JOIN ejia_member_allergen ma ON ma.allergen_code = ea.code
                WHERE ma.member_id IN ({member_ids_str})
            )
            GROUP BY d.id, d.name, d.emoji, d.default_portion_g, d.max_servings, d.rating, 
                     nm.match_score, nm.need_code
            ORDER BY nm.match_score DESC, d.rating DESC
            LIMIT %s
        """

        return self.db.query(sql, (need_code, min_score, limit))

    def get_dishes_for_multiple_needs(self, need_codes: List[str], constraints: MemberConstraints,
                                      need_weights: Dict[str, float], limit: int = 100) -> List[Dict]:
        """根据多重需求获取菜品（适应纵表结构）"""
        if not need_codes:
            return []

        need_codes_str = ','.join([f"'{code}'" for code in need_codes])
        member_ids_str = ','.join(map(str, constraints.allergy_member_ids)) if constraints.allergy_member_ids else '-1'

        # 构建权重条件
        weight_conditions = []
        for need_code, weight in need_weights.items():
            weight_conditions.append(f"WHEN nm.need_code = '{need_code}' THEN {weight}")

        weight_case = f"CASE {' '.join(weight_conditions)} ELSE 1 END"

        sql = f"""
            SELECT 
                d.id as dish_id,
                d.name,
                d.emoji,
                d.default_portion_g,
                d.max_servings,
                d.rating,
                SUM(nm.match_score * {weight_case}) as weighted_score,
                COUNT(DISTINCT nm.need_code) as matched_needs_count,
                GROUP_CONCAT(DISTINCT nm.need_code) as matched_need_codes,
                -- 获取营养成分
                MAX(CASE WHEN dnl.nutrient_name = '钙' THEN dnl.nutrient_amount END) as calcium,
                MAX(CASE WHEN dnl.nutrient_name = '铁' THEN dnl.nutrient_amount END) as iron,
                MAX(CASE WHEN dnl.nutrient_name = '钠' THEN dnl.nutrient_amount END) as sodium,
                MAX(CASE WHEN dnl.nutrient_name = '脂肪' THEN dnl.nutrient_amount END) as fat,
                MAX(CASE WHEN dnl.nutrient_name = '蛋白质' THEN dnl.nutrient_amount END) as protein,
                MAX(CASE WHEN dnl.nutrient_name = '膳食纤维' THEN dnl.nutrient_amount END) as fiber,
                MAX(CASE WHEN dnl.nutrient_name = '嘌呤' THEN dnl.nutrient_amount END) as purine,
                MAX(CASE WHEN dnl.nutrient_name = '热量' THEN dnl.nutrient_amount END) as kcal
            FROM ejia_dish d
            JOIN ejia_need_dish_match nm ON nm.dish_id = d.id
            LEFT JOIN view_dish_nutrients_long dnl ON dnl.dish_id = d.id
            WHERE nm.need_code IN ({need_codes_str})
            AND nm.match_score >= 0.6
            AND d.id NOT IN (
                SELECT DISTINCT dfr.dish_id
                FROM ejia_dish_food_rel dfr
                JOIN ejia_enum_allergen_tbl ea ON ea.food_id = dfr.food_id
                JOIN ejia_member_allergen ma ON ma.allergen_code = ea.code
                WHERE ma.member_id IN ({member_ids_str})
            )
            GROUP BY d.id, d.name, d.emoji, d.default_portion_g, d.max_servings, d.rating
            HAVING matched_needs_count >= 1
            ORDER BY weighted_score DESC, d.rating DESC
            LIMIT %s
        """

        return self.db.query(sql, (limit,))

    def fetch_matching_combos_new(self, recommended: List[dict]) -> List[dict]:
        """
        传入推荐菜品列表，去数据库查套餐，并保留推荐信息
        """
        if not recommended:
            return []

        # 获取所有可能的菜品ID字段
        dish_ids = []
        for rec in recommended:
            # 尝试多种可能的ID字段
            dish_id = rec.get('dish_id') or rec.get('id')
            if dish_id:
                dish_ids.append(str(dish_id))

        if not dish_ids:
            return []

        ids_str = ','.join(dish_ids)

        sql = f"""
            SELECT
                c.id               AS combo_id,
                c.combo_name,
                c.combo_desc,
                c.meal_type,
                cd.dish_id,
                d.name,
                d.emoji,
                d.rating,
                d.default_portion_g
            FROM ejia_combo c
            JOIN ejia_combo_dish_rel cd ON cd.combo_id = c.id
            JOIN ejia_dish d            ON d.id = cd.dish_id
            WHERE cd.dish_id IN ({ids_str})
            ORDER BY c.id
        """
        rows = self.db.query(sql)

        # 创建推荐信息映射
        rec_info_map = {}
        for rec in recommended:
            # 统一获取菜品ID
            dish_id = rec.get('dish_id') or rec.get('id')
            if dish_id:
                rec_info_map[dish_id] = {
                    'servings': rec.get('servings', 1),
                    'portion_g': rec.get('portion_g'),
                    'match_score': rec.get('final_score', 0),
                    'matched_needs': rec.get('matched_needs', [])
                }

        # 按套餐聚合
        combo_map = {}
        for r in rows:
            cid = r['combo_id']
            dish_id = r['dish_id']

            if cid not in combo_map:
                combo_map[cid] = {
                    'comboId': r['meal_type'] or str(cid),
                    'comboName': r['combo_name'],
                    'comboDesc': r['combo_desc'],
                    'score': 0,
                    'dishes': []
                }

            # 获取推荐信息
            rec_info = rec_info_map.get(dish_id, {})
            servings = rec_info.get('servings', 1)
            portion_g = rec_info.get('portion_g', float(r['default_portion_g']))

            # 获取匹配的需求标签
            matched_needs = rec_info.get('matched_needs', [])
            tags = [need['need_code'] for need in matched_needs] if matched_needs else []

            combo_map[cid]['dishes'].append({
                'dish_id': dish_id,
                'name': r['name'],
                'emoji': r['emoji'],
                'servings': servings,
                'portion_g': portion_g,
                'rating': float(r['rating']),
                'tags': tags,
                'match_score': rec_info.get('match_score', 0)
            })

            # 计算套餐得分
            combo_map[cid]['score'] = min(5, len(combo_map[cid]['dishes']) +
                                          sum(dish.get('match_score', 0) for dish in combo_map[cid]['dishes']) / 2)

        return sorted(combo_map.values(), key=lambda x: x['score'], reverse=True)[:5]

    def _load_nutrient_rules(self):
        """加载营养素判断规则"""
        sql = """
              SELECT need_code, \
                     nutrient_name_cn, \
                     comparison_operator,
                     threshold_value, \
                     unit, \
                     description
              FROM ejia_enum_diet_need_nutrient_rule \
              """
        rows = self.db.query(sql)
        self.nutrient_rules = {}
        for row in rows:
            if row['need_code'] not in self.nutrient_rules:
                self.nutrient_rules[row['need_code']] = []
            self.nutrient_rules[row['need_code']].append(row)

    def _calculate_dish_tags(self, dish: Dish, need_codes: List[str]) -> List[str]:
        """根据菜品营养成分计算符合的需求标签"""
        tags = []

        for need_code in need_codes:
            if need_code not in self.nutrient_rules:
                continue

            rules = self.nutrient_rules[need_code]
            meets_all_rules = True

            for rule in rules:
                nutrient_value = getattr(dish, self._get_nutrient_attr_name(rule['nutrient_name_cn']), 0)

                if rule['comparison_operator'] == '>=':
                    if nutrient_value < rule['threshold_value']:
                        meets_all_rules = False
                        break
                elif rule['comparison_operator'] == '<=':
                    if nutrient_value > rule['threshold_value']:
                        meets_all_rules = False
                        break
                elif rule['comparison_operator'] == '>':
                    if nutrient_value <= rule['threshold_value']:
                        meets_all_rules = False
                        break
                elif rule['comparison_operator'] == '<':
                    if nutrient_value >= rule['threshold_value']:
                        meets_all_rules = False
                        break

            if meets_all_rules:
                tags.append(need_code)

        return tags

    def _get_nutrient_attr_name(self, nutrient_name_cn: str) -> str:
        """将中文营养素名转换为Dish对象的属性名"""
        mapping = {
            '钙': 'calcium',
            '铁': 'iron',
            '钠': 'sodium',
            '脂肪': 'fat',
            '蛋白质': 'protein',
            '膳食纤维': 'fiber',
            '嘌呤': 'purine',
            '热量': 'kcal'
        }
        return mapping.get(nutrient_name_cn, nutrient_name_cn)

    def get_popular_dishes(self, constraints: MemberConstraints, limit: int = 20) -> List[Dict]:
        """获取受欢迎的菜品（无特殊需求时使用）- 使用纵表结构"""
        member_ids_str = ','.join(map(str, constraints.allergy_member_ids)) if constraints.allergy_member_ids else '-1'

        sql = f"""
            SELECT 
                d.id as dish_id,
                d.name,
                d.emoji,
                d.default_portion_g,
                d.max_servings,
                d.rating,
                0 as match_score,
                -- 获取营养成分
                MAX(CASE WHEN dnl.nutrient_name = '钙' THEN dnl.nutrient_amount END) as calcium,
                MAX(CASE WHEN dnl.nutrient_name = '铁' THEN dnl.nutrient_amount END) as iron,
                MAX(CASE WHEN dnl.nutrient_name = '钠' THEN dnl.nutrient_amount END) as sodium,
                MAX(CASE WHEN dnl.nutrient_name = '脂肪' THEN dnl.nutrient_amount END) as fat,
                MAX(CASE WHEN dnl.nutrient_name = '蛋白质' THEN dnl.nutrient_amount END) as protein,
                MAX(CASE WHEN dnl.nutrient_name = '膳食纤维' THEN dnl.nutrient_amount END) as fiber,
                MAX(CASE WHEN dnl.nutrient_name = '嘌呤' THEN dnl.nutrient_amount END) as purine,
                MAX(CASE WHEN dnl.nutrient_name = '热量' THEN dnl.nutrient_amount END) as kcal
            FROM ejia_dish d
            LEFT JOIN view_dish_nutrients_long dnl ON dnl.dish_id = d.id
            WHERE d.rating >= 4.0
            AND d.id NOT IN (
                SELECT DISTINCT dfr.dish_id
                FROM ejia_dish_food_rel dfr
                JOIN ejia_enum_allergen_tbl ea ON ea.food_id = dfr.food_id
                JOIN ejia_member_allergen ma ON ma.allergen_code = ea.code
                WHERE ma.member_id IN ({member_ids_str})
            )
            GROUP BY d.id, d.name, d.emoji, d.default_portion_g, d.max_servings, d.rating
            ORDER BY d.rating DESC, RAND()
            LIMIT %s
        """

        rows = self.db.query(sql, (limit,))

        # 处理数据类型转换
        processed_rows = []
        for row in rows:
            processed_row = {}
            for key, value in row.items():
                if key in ['rating', 'match_score', 'calcium', 'iron', 'sodium',
                           'fat', 'protein', 'fiber', 'purine', 'kcal', 'default_portion_g']:
                    try:
                        processed_row[key] = float(value) if value is not None else 0.0
                    except (ValueError, TypeError):
                        processed_row[key] = 0.0
                elif key == 'max_servings':
                    try:
                        processed_row[key] = int(value) if value is not None else 1
                    except (ValueError, TypeError):
                        processed_row[key] = 1
                else:
                    processed_row[key] = value
            processed_rows.append(processed_row)

        return processed_rows