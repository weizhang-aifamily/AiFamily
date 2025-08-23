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
        LEFT JOIN ejia_member_diet_need        d  ON f.id = d.member_id
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

@family_bp.route('/getCombos/<member_ids>', methods=['GET'])
def get_combos(member_ids):
    try:
        ids_tuple = tuple(map(int, member_ids.split(',')))
        if len(ids_tuple) == 1:
            ids_tuple = (ids_tuple[0], -1)

        sql = """
        SELECT
            c.id            AS combo_id,
            c.combo_name,
            c.combo_desc,
            c.meal_type,
            d.id            AS dish_id,
            d.name          AS dish_name,
            d.emoji,
            d.rating,
            dc.name         AS dish_category
        FROM ejia_combo           AS c
        JOIN ejia_combo_item      AS ci ON ci.combo_id = c.id
        JOIN ejia_dish            AS d  ON d.id  = ci.dish_id
        JOIN ejia_dish_category   AS dc ON dc.id = d.category_id
        ORDER BY c.id, ci.dish_id
        """
        # rows = db.query(sql, (ids_tuple,))
        rows = db.query(sql)

        # ---------- 纯 Python 聚合 ----------
        combo_map = {}   # {combo_id: {...}}
        for r in rows:
            cid = r['combo_id']
            # 套餐级别只初始化一次
            if cid not in combo_map:
                combo_map[cid] = {
                    'comboId':   r['meal_type'] or str(cid),  # morning / noon / night
                    'comboName': r['combo_name'],
                    'comboDesc': r['combo_desc'],
                    'dishes':    []
                }
            # 菜品级别
            combo_map[cid]['dishes'].append({
                'id':        r['dish_id'],
                'name':      r['dish_name'],
                'picSeed':   r['dish_name'].lower().replace(' ', ''),
                'tags':      [f"{r['dish_category']} +{int((r['rating'] or 4.7)*10)}%"],
                'checked':   True,
                'rating':    round(float(r['rating'] or 4.7), 1)
            })

        combo_data = list(combo_map.values())

        return jsonify({"status": "success", "data": combo_data})

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