from flask import Blueprint, jsonify, json, request
from typing import List, Dict, Optional
from dbconnect.dbconn import db
from ejiacanAI.engine import ILPRecommender
from ejiacanAI.data_access import EnhancedDataAccess
from ejiacanAI.smart_recommender import SmartRecommender, RecommendationConfig
import logging
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

@family_bp.route('/getCombos/<member_ids>', methods=['GET'])
def get_combos(member_ids):
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
        combos = dao.fetch_matching_combos_new(recommendations)

        return jsonify({
            "status": "success",
            "data": combos,
            "metadata": {
                "recommendation_type": "smart",
                "total_recommendations": len(recommendations)
            }
        })

    except Exception as e:
        logger.error("Get combos error: %s", str(e))


@family_bp.route('getDietSolutions/<member_ids>', methods=['GET'])
def get_diet_solutions(member_ids):
    """
    /family/getDietSolutions/1,2,3
    """
    try:
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
              WHERE dn.member_id IN %s \
              """

        rows = db.query(sql, (ids_tuple,))
        result = {r['code']: {'name': r['name'], 'icon': r['icon'], 'desc': r['desc_text']} for r in rows}
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


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