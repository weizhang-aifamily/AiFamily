from flask import Blueprint, jsonify, json
from dbconnect.dbconn import db
from ejiacanAI.data_access import DataAccess
from ejiacanAI.engine import ILPRecommender

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
        FROM ejia_user_family f
        LEFT JOIN ejia_member_diet_need        d  ON f.id = d.member_id
        LEFT JOIN ejia_member_allergen  ma ON f.member_id = ma.member_id
        LEFT JOIN ejia_allergen_tbl    a  ON ma.allergen_code = a.code
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
dao = DataAccess(db)
engine = ILPRecommender()
@family_bp.route('/getCombos/<member_ids>', methods=['GET'])
def get_combos(member_ids):
    """
    /family/getCombos/1,2,3
    使用ILP引擎推荐最优的菜品组合，然后从套餐表中匹配最相似的套餐
    """
    try:
        # 将字符串转换为整数列表
        member_ids_list = list(map(int, member_ids.split(',')))

        # 使用ILP推荐引擎生成最优菜品组合
        recommended_dishes = engine.recommend(
            dishes=dao.fetch_safe_dishes(member_ids_list),
            need=dao.fetch_family_need(member_ids_list),
            top_k=5
        )

        if not recommended_dishes:
            return jsonify({"status": "success", "data": [], "message": "未找到合适的菜品组合"})

        # 获取推荐菜品的ID列表
        recommended_dish_ids = [dish['dish_id'] for dish in recommended_dishes]
        recommended_dish_ids_str = ','.join(map(str, recommended_dish_ids))

        # 从套餐表中查找包含这些推荐菜品的套餐
        sql_find_combos = f"""
        SELECT
            c.id as combo_id,
            c.combo_name as combo_name,
            c.combo_desc as combo_desc,
            c.meal_type,
            COUNT(ci.dish_id) as match_count,
            JSON_ARRAYAGG(
                JSON_OBJECT(
                    'dish_id',  d.id,
                    'name',     d.name,
                    'emoji',    d.emoji,
                    'rating',   d.rating,
                    'category', dc.name
                )
            ) AS dishes
        FROM ejia_combo c
        JOIN ejia_combo_item ci ON c.id = ci.combo_id
        JOIN ejia_dish d ON d.id = ci.dish_id
        JOIN ejia_dish_category dc ON dc.id = d.category_id
        WHERE ci.dish_id IN ({recommended_dish_ids_str})
        GROUP BY c.id, c.combo_name, c.combo_desc, c.meal_type
        ORDER BY match_count DESC, c.id
        LIMIT 5;
        """

        combo_rows = db.query(sql_find_combos)

        # 组装成前端需要的结构
        combos = []
        for r in combo_rows:
            dishes = json.loads(r['dishes'])
            for dish in dishes:
                dish['picSeed'] = dish['name'].lower().replace(' ', '')
                dish['tags'] = [f"{dish['category']} +{int((dish['rating'] or 4.7) * 10)}%"]
                dish['checked'] = True
                dish['rating'] = round(float(dish['rating'] or 4.7), 1)

            # 计算套餐的营养得分（基于ILP推荐的结果）
            score = min(5, r['match_count'] + 2)  # 基础分 + 匹配奖励

            combos.append({
                'comboId': r['meal_type'] or str(r['combo_id']),
                'comboName': r['combo_name'],
                'comboDesc': r['combo_desc'],
                'score': score,
                'dishes': dishes
            })

        return jsonify({"status": "success", "data": combos})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
                       JOIN ejia_diet_need_tbl ds ON dn.need_code = ds.code
              WHERE dn.member_id IN %s \
              """

        rows = db.query(sql, (ids_tuple,))
        result = {r['code']: {'name': r['name'], 'icon': r['icon'], 'desc': r['desc_text']} for r in rows}
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500