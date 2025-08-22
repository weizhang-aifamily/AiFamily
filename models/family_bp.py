from flask import Blueprint, jsonify
from dbconnect.dbconn import db

family_bp = Blueprint('family', __name__, url_prefix='/family')

@family_bp.route('getMembers/<int:user_id>', methods=['GET'])
def get_members(user_id):
    """获取成员的饮食方案"""
    try:
        query = """
        SELECT  f.id          AS member_id,
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
        LEFT JOIN ejia_diet_need        d  ON f.id = d.member_id
        LEFT JOIN ejia_member_allergen  ma ON f.id = ma.family_id
        LEFT JOIN ejia_enum_allergen    a  ON ma.allergen_code = a.code
        WHERE f.owner_id = %s
        GROUP BY f.id
        """
        rows = db.query(query, (user_id,))
        for r in rows:
            r['needs'] = (r['needs'] or '').split(',')
            r['displayNeeds'] = r['needs']
            r['allergens'] = (r['allergens'] or '').split(',')
        return jsonify({"status": "success", "data": rows})
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
            ids_tuple = (ids_tuple[0], -1)   # 单元素 IN 兼容

        sql = """
        SELECT DISTINCT
               ds.code,
               ds.name,
               ds.icon,
               ds.desc_text
        FROM ejia_diet_need        dn
        JOIN ejia_solution_rule    sr ON dn.nutrient  = sr.nutrient
                                     AND dn.direction = sr.direction
        JOIN ejia_diet_solution    ds ON sr.code      = ds.code
        WHERE dn.member_id IN %s
        """

        rows = db.query(sql, (ids_tuple,))
        result = {r['code']: {'name': r['name'], 'icon': r['icon'], 'desc': r['desc_text']} for r in rows}
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500