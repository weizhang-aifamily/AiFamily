from flask import Blueprint, jsonify
from dbconnect.dbconn import db

family_bp = Blueprint('family', __name__, url_prefix='/family')


@family_bp.route('getMembers/<int:user_id>', methods=['GET'])
def get_members(user_id):
    """获取成员的饮食方案"""
    try:
        query = """
                SELECT fm.member_id, \
                       fm.family_id, \
                       fm.name, \
                       fm.avatar, \
                       fm.gender, \
                       fm.birth_date, \
                       fm.relation, \
                       fm.oxygen_level, \
                       fm.blood_pressure, \
                       fm.birth_rate, \
                       GROUP_CONCAT(DISTINCT dnt.need_code) as needs, \
                       GROUP_CONCAT(DISTINCT a.name)        as allergens
                FROM family_member fm
                         LEFT JOIN member_diet_need mdn ON fm.member_id = mdn.member_id
                         LEFT JOIN diet_need_tag dnt ON mdn.need_code = dnt.need_code
                         LEFT JOIN member_allergen ma ON fm.member_id = ma.member_id
                         LEFT JOIN allergen a ON ma.allergen_id = a.allergen_id
                WHERE fm.family_id = %s \
                  AND fm.is_deleted = 0
                GROUP BY fm.member_id
                """
        rows = db.query(
            query,
            (user_id,))
        for r in rows:
            r['needs'] = (r['needs'] or '').split(',')
            r['displayNeeds'] = r['needs']
            r['allergens'] = (r['allergens'] or '').split(',')
        return jsonify({"status": "success", "data": rows})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
