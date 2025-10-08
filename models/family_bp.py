from typing import List, Dict

from flask import Blueprint, jsonify, request
from dbconnect.dbconn import db
from ejiacanAI.dish2_combo_generator import MealGeneratorV2
from ejiacanAI.dish2_combo_models import MealRequest
from ejiacanAI.dish_combo_generator import DishComboGenerator
from ejiacanAI.dish_combo_models import ComboMeal
from ejiacanAI.engine import ILPRecommender
from ejiacanAI.data_access import EnhancedDataAccess
from ejiacanAI.smart_recommender import SmartRecommender
import logging

from management.dish_data import DishData

logger = logging.getLogger(__name__)
family_bp = Blueprint('family', __name__, url_prefix='/family')

@family_bp.route('getMembers/<int:user_id>', methods=['GET'])
def get_members(user_id):
    """获取成员的饮食方案"""
    try:
        query = """
        SELECT  
            f.id          AS member_id,
            f.owner_id    AS family_id,
            f.name        AS name,
            ''            AS avatar,          -- ejia_user_family 暂无 avatar
            f.gender      AS gender,
            f.birthday    AS birth_date,
            f.relation    AS relation,
            ''            AS oxygen_level,
            ''            AS blood_pressure,
            ''            AS birth_rate,
            GROUP_CONCAT(DISTINCT d.need_code) AS needs,
            GROUP_CONCAT(DISTINCT a.name)      AS allergens
        FROM ejia_user_family_member f
        LEFT JOIN ejia_member_diet_need        d  ON f.id = d.member_id
        LEFT JOIN ejia_member_allergen  ma ON f.id = ma.member_id
        LEFT JOIN ejia_enum_allergen_tbl    a  ON ma.allergen_code = a.code
        WHERE f.owner_id = %s
        GROUP BY 
            f.id,
            f.owner_id,
            f.name,
            f.gender,
            f.birthday,
            f.relation
        LIMIT 0, 1000;
        """
        rows = db.query(query, (user_id,))
        for r in rows:
            r['needs'] = (r['needs'] or '').split(',')
            r['displayNeeds'] = r['needs']
            r['allergens'] = (r['allergens'] or '').split(',')
        return jsonify({"status": "success", "data": rows})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 初始化推荐引擎
dao = EnhancedDataAccess(db)
engine = ILPRecommender()

@family_bp.route('/getCombos/', methods=['GET'])
@family_bp.route('/getCombos/<member_ids>', methods=['GET'])
def get_combos(member_ids=None):
    try:
        meal_type = request.args.get('meal_type', 'lunch')
        cuisine = request.args.get('cuisine', None)
        category = request.args.get('category', None)
        activeSolutions = request.args.get('activeSolutions', None)

        # 1. 获取智能推荐结果
        # recommendations = recommender.recommend(member_ids_list, meal_type, max_results)
        # 使用套餐生成器生成全天套餐
        # all_day_meals = DishComboGenerator.generate_family_combo(
        #     member_ids=member_ids_list,
        #     meal_type="all",  # 或者使用传入的 meal_type 参数
        #     filter_allergens=True
        # )
        if member_ids is None:
            req = MealRequest(
                member_ids=[0],
                meal_type=meal_type,  # 生成三餐
                refresh_key=3,  # 每次换种子即可洗牌
                cook_time_limit=30,  # 30 分钟以内
                deficit_kcal=0,  # 无热量缺口
                dish_series=cuisine,  # 菜系ID
                dish_category=category,
                explicit_tags=activeSolutions.split(","),
            )
            all_day_meals = MealGeneratorV2.generate_per_meal_default(req)
        else:
            member_ids_list = list(map(int, member_ids.split(',')))
            req = MealRequest(
                member_ids=member_ids_list,
                meal_type=meal_type,  # 生成三餐
                refresh_key=3,  # 每次换种子即可洗牌
                cook_time_limit=30,  # 30 分钟以内
                deficit_kcal=0,  # 无热量缺口
                dish_series=cuisine,  # 菜系ID
                dish_category=category,
                explicit_tags=activeSolutions.split(","),
            )
            all_day_meals = MealGeneratorV2.generate_per_meal(req)

        if not all_day_meals:
            return jsonify({"status": "success", "data": [], "message": "未找到合适的菜品组合"})

        # 2. 将推荐结果转换为套餐格式（保持原有返回结构）
        #combos = _convert_recommendations_to_combos(recommendations)
        # combos = dao.fetch_matching_combos_new(recommendations)
        # combos = _convert_combos_to_response(all_day_meals)
        return jsonify({
            "status": "success",
            "data": all_day_meals,
            "metadata": {
                "recommendation_type": "smart",
                "total_recommendations": len(all_day_meals)
            }
        })

    except Exception as e:
        logger.error("Get combos error: %s", str(e))


def _convert_combos_to_response(combos: List[ComboMeal]) -> List[Dict]:
    """将 ComboMeal 对象转换为前端需要的 JSON 格式"""
    result = []

    for combo in combos:
        combo_data = {
            'comboName': combo.combo_name,
            'mealType': combo.meal_type,
            'cookTime': combo.total_cook_time,
            'need_codes': combo.need_codes,
            'dishes': [],
            'portion_plan': combo.portion_plan
        }

        # 转换菜品信息
        for dish in combo.dishes:
            dish_data = {
                'dish_id': dish.dish_id,
                'name': dish.name,
                'cookTime': dish.cook_time,
                'portion_size': dish.portion_size,
                'nutrients': dish.nutrients,
                'ingredients': dish.ingredients,
                'allergens': dish.allergens if hasattr(dish, 'allergens') else [],
                'tags': getattr(dish, 'matched_needs', [])
            }
            combo_data['dishes'].append(dish_data)

        result.append(combo_data)

    return result

@family_bp.route('/getDishReco/<member_ids>', methods=['GET'])
def getDishReco(member_ids):
    try:
        member_ids_list = list(map(int, member_ids.split(',')))
        meal_type = request.args.get('meal_type', 'lunch')
        max_results = min(int(request.args.get('max_results', 10)), 50)

        # 1. 获取智能推荐结果
        recommendations = recommender.recommend(member_ids_list, meal_type, max_results)

        if not recommendations:
            return jsonify({"status": "success", "data": [], "message": "未找到合适的菜品组合"})

        # 2. 将推荐结果转换为套餐格式（保持原有返回结构）
        #combos = _convert_recommendations_to_combos(recommendations)
        combos = _convert_dishes_to_response(recommendations)

        return jsonify({
            "status": "success",
            "data": combos,
            "metadata": {
                "recommendation_type": "smart",
                "total_recommendations": len(recommendations)
            }
        })

    except Exception as e:
        logger.error("Get getDishReco error: %s", str(e))

def _convert_dishes_to_response(recommended: List[dict]) -> List[dict]:
    """
    传入推荐菜品列表，找到包含这些菜品的套餐，并标记推荐菜品
    """
    result = []
    if not recommended:
        return []

    for r in recommended:
        nutri_tags = r.get('matched_need_codes', [])
        if isinstance(nutri_tags, str):
            nutri_tags = [nutri_tags]  # 如果是字符串，转为数组
        elif not isinstance(nutri_tags, list):
            nutri_tags = []  # 如果不是列表，设为空数组
        # 构建菜品信息
        dish_info = {
            'dish_id': r.get('id') or r.get('dish_id'),  # 兼容不同字段名
            'name': r.get('name', ''),
            'emoji': r.get('emoji', '🍽️'),
            'servings': r.get('servings', 1),
            'portion_g': r.get('portion_g', r.get('default_portion_g', 100)),
            'rating': float(r.get('rating', 0)),
            'checked': "false",  # 标记是否被推荐
            'match_score': float(r.get('match_score', r.get('final_score', 0))),
            'nutri-tag': nutri_tags,  # 兼容不同字段名
            'cookTime': r.get('cook_time', 0),
            'allergens': r.get('allergens', [])
        }
        # 清理空值
        dish_info = {k: v for k, v in dish_info.items() if v is not None}
        result.append(dish_info)

    return result


@family_bp.route('getDietSolutions/', methods=['GET'])
@family_bp.route('getDietSolutions/<member_ids>', methods=['GET'])
def get_diet_solutions(member_ids=None):
    """
    /family/getDietSolutions/
    /family/getDietSolutions/1,2,3
    """
    try:
        # 如果没有传入 member_ids，查询所有记录
        if member_ids is None:
            sql = """
                  SELECT DISTINCT ds.code, \
                                  ds.name, \
                                  ds.icon, \
                                  ds.desc_text
                  FROM ejia_enum_diet_need_tbl ds where ds.is_select = 1
                  """
            rows = db.query(sql)
        else:
            # 把 "1,2,3" 转成元组供 SQL IN
            ids_tuple = tuple(map(int, member_ids.split(',')))
            if len(ids_tuple) == 1:
                ids_tuple = (ids_tuple[0], -1)  # 单元素 IN 兼容

            sql = """
                  SELECT DISTINCT ds.code, \
                                  ds.name, \
                                  ds.icon, \
                                  ds.desc_text
                  FROM ejia_member_diet_need dn
                           JOIN ejia_enum_diet_need_tbl ds ON dn.need_code = ds.code
                  WHERE dn.member_id IN %s
                  """
            rows = db.query(sql, (ids_tuple,))

        result = {r['code']: {'name': r['name'], 'icon': r['icon'], 'desc': r['desc_text']} for r in rows}
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@family_bp.route('/getTagTbl/<group_code>', methods=['GET'])
def getTagTbl(group_code):
    try:
        cuisineTags = DishData.list_oneTags(group_code)
        if not cuisineTags:
            return jsonify({"status": "success", "data": [], "message": "未找到tags"})

        return jsonify({
            "status": "success",
            "data": cuisineTags
        })

    except Exception as e:
        logger.error("Get getDishReco error: %s", str(e))


# 初始化
recommender = SmartRecommender(dao)


@family_bp.route('/smartRecommendation/<member_ids>', methods=['GET'])
def smart_recommendation(member_ids):
    try:
        member_ids_list = list(map(int, member_ids.split(',')))
        meal_type = request.args.get('meal_type', 'lunch')
        max_results = min(int(request.args.get('max_results', 10)), 50)

        recommendations = recommender.recommend(
            member_ids_list, meal_type, max_results
        )

        # 格式化返回结果
        formatted_recommendations = []
        for rec in recommendations:
            formatted_rec = {
                'dish_id': rec['id'],
                'name': rec['name'],
                'emoji': rec.get('emoji', '🍽️'),
                'servings': 1,
                'portion_g': rec.get('default_portion_g', 100),
                'rating': rec.get('rating', 0),
                'match_score': rec.get('final_score', 0),
                'matched_needs': rec.get('matched_needs', [])
            }
            formatted_recommendations.append(formatted_rec)

        return jsonify({
            "status": "success",
            "data": formatted_recommendations,
            "metadata": {
                "total_count": len(formatted_recommendations),
                "meal_type": meal_type,
                "member_ids": member_ids_list
            }
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"推荐失败: {str(e)}"
        }), 500