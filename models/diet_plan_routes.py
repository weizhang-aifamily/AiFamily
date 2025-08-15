from flask import Blueprint, request, jsonify
from dbconnect.dbconn import db

diet_bp = Blueprint('diet', __name__, url_prefix='/diet')


@diet_bp.route('/plans/<int:member_id>', methods=['GET'])
def get_member_plans(member_id):
    """获取成员的饮食方案"""
    try:
        plans = db.query(
            "SELECT * FROM diet_plan WHERE member_id = %s ORDER BY created_at DESC",
            (member_id,))
        return jsonify({"status": "success", "data": plans})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@diet_bp.route('/plans', methods=['POST'])
def create_plan():
    """创建饮食方案"""
    try:
        data = request.get_json()
        db.query(
            "INSERT INTO diet_plan (member_id, plan_name) VALUES (%s, %s)",
            (data['member_id'], data['plan_name']))
        plan_id = db.query("SELECT LAST_INSERT_ID()")[0]['LAST_INSERT_ID()']
        return jsonify({"status": "success", "plan_id": plan_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@diet_bp.route('/requirements/<int:plan_id>', methods=['GET'])
def get_plan_requirements(plan_id):
    """获取方案营养需求"""
    try:
        reqs = db.query(
            "SELECT * FROM nutrition_requirement WHERE plan_id = %s",
            (plan_id,))
        return jsonify({"status": "success", "data": reqs})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@diet_bp.route('/dishes/generate', methods=['POST'])
def generate_dishes():
    """生成推荐菜品"""
    try:
        data = request.get_json()
        # 简化版生成逻辑 - 实际应根据营养需求匹配食材
        dishes = db.query("""
                          SELECT f.food_id, f.food_name, fn.nutrient_type, fn.amount, fn.unit
                          FROM recommended_food f
                                   JOIN food_nutrition fn ON f.food_id = fn.food_id
                          WHERE fn.nutrient_type IN (SELECT nutrient_type
                                                     FROM nutrition_requirement
                                                     WHERE plan_id = %s)
                          ORDER BY RAND() LIMIT 4
                          """, (data['plan_id'],))

        # 保存生成的菜品
        dish_ids = []
        for dish in dishes:
            db.query("""
                     INSERT INTO generated_dish (plan_id, dish_name)
                     VALUES (%s, %s)
                     """, (data['plan_id'], f"{dish['food_name']}搭配餐"))
            dish_id = db.query("SELECT LAST_INSERT_ID()")[0]['LAST_INSERT_ID()']
            dish_ids.append(dish_id)

        return jsonify({
            "status": "success",
            "data": [{"dish_id": did} for did in dish_ids]
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@diet_bp.route('/foods/recommended', methods=['GET'])
def get_recommended_foods():
    """获取推荐食材列表"""
    try:
        foods = db.query("""
            SELECT f.*, 
                   JSON_ARRAYAGG(
                       JSON_OBJECT(
                           'nutrient_type', fn.nutrient_type,
                           'amount', fn.amount,
                           'unit', fn.unit
                       )
                   ) as nutritions
            FROM recommended_food f
            LEFT JOIN food_nutrition fn ON f.food_id = fn.food_id
            GROUP BY f.food_id
            ORDER BY RAND()
            LIMIT 5
        """)
        return jsonify({
            "status": "success",
            "data": [{
                **food,
                "nutritions": json.loads(food['nutritions']) if food['nutritions'] else []
            } for food in foods]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@diet_bp.route('/dishes/<int:plan_id>', methods=['GET'])
def get_plan_dishes(plan_id):
    """获取方案菜品"""
    try:
        dishes = db.query("""
            SELECT * FROM generated_dish
            WHERE plan_id = %s
            ORDER BY created_at DESC
            LIMIT 6
        """, (plan_id,))
        return jsonify({"status": "success", "data": dishes})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@diet_bp.route('/foods/recommended', methods=['POST'])
def get_recommended_foods_by_plans():
    """根据多个方案获取推荐食材"""
    try:
        plan_ids = request.get_json().get('plan_ids', [])
        if not plan_ids:
            return jsonify({"status": "error", "message": "需要方案ID"}), 400

        # 获取所有方案的营养需求
        requirements = db.query("""
                                SELECT DISTINCT nutrient_type
                                FROM nutrition_requirement
                                WHERE plan_id IN %s
                                """, (tuple(plan_ids),))

        # 根据需求获取食材(简化版)
        foods = db.query("""
                         SELECT f.*,
                                JSON_ARRAYAGG(
                                        JSON_OBJECT(
                                                'nutrient_type', fn.nutrient_type,
                                                'amount', fn.amount,
                                                'unit', fn.unit
                                        )
                                ) as nutritions
                         FROM recommended_food f
                                  JOIN food_nutrition fn ON f.food_id = fn.food_id
                         WHERE fn.nutrient_type IN %s
                         GROUP BY f.food_id
                         ORDER BY RAND() LIMIT 2
                         """, (tuple(r['nutrient_type'] for r in requirements),))

        return jsonify({
            "status": "success",
            "data": [{
                **food,
                "nutritions": json.loads(food['nutritions']) if food['nutritions'] else []
            } for food in foods]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500