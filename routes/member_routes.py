from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
from models.family_member import FamilyMember
from models.health_metric import HealthMetric
from models.diet_record import DietRecord

member_bp = Blueprint('members', __name__, url_prefix='/members')

# ---------------------- 页面路由 ----------------------
@member_bp.route('/list', methods=['GET'])
def members_page():
    """成员列表页面"""
    return render_template('members/list.html')

@member_bp.route('/<int:member_id>')
def member_detail(member_id):
    """成员详情页"""
    member = FamilyMember.get_by_id(member_id)
    return render_template('members/detail.html',
                         member=member,
                         member_id=member_id)
@member_bp.route('/add', methods=['GET'])
def members_add():
    """成员列表页面"""
    return render_template('members/form.html')

# ---------------------- API路由 ----------------------

@member_bp.route('/<int:member_id>/metrics/latest', methods=['GET'])
def get_latest_metrics(member_id):
    """获取成员各项指标的最新记录"""
    try:
        latest_metrics = HealthMetric.get_latest_metrics(member_id)
        return jsonify({
            "status": "success",
            "data": latest_metrics
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
@member_bp.route('/<int:member_id>/metrics', methods=['GET'])
def get_all_metrics(member_id):
    """获取成员所有健康指标"""
    try:
        metrics = HealthMetric.get_all_metrics(member_id)
        return jsonify({
            "status": "success",
            "data": metrics
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
@member_bp.route('/<int:member_id>/food-ranking', methods=['GET'])
def get_food_ranking(member_id):
    """获取成员饮食排名数据"""
    try:
        food_data = DietRecord.get_food_ranking(member_id)
        return jsonify({
            "status": "success",
            "data": food_data
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
@member_bp.route('/<int:member_id>/nutrition', methods=['GET'])
def get_nutrition_data(member_id):
    """获取成员营养摄入数据"""
    try:
        nutrition_data = HealthMetric.get_nutrition_data(member_id)
        return jsonify({
            "status": "success",
            "data": nutrition_data
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
@member_bp.route('/<int:member_id>/full-health', methods=['GET'])
def get_full_health_data(member_id):
    """获取成员完整健康数据"""
    try:
        # 1. 获取成员基本信息
        member = FamilyMember.get_by_id(member_id)
        if not member:
            return jsonify({"status": "error", "message": "成员不存在"}), 404

        # 2. 获取健康指标
        metrics = HealthMetric.get_by_member(member_id)

        # 3. 处理数据
        birth_date = datetime.strptime(member['birth_date'], '%Y-%m-%d')
        age = (datetime.now() - birth_date).days // 365

        response_data = {
            "basic_info": {
                "name": member['name'],
                "age": age,
                "height": next((m['metric_value'] for m in metrics if m['metric_code'] == 'HEIGHT'), None),
                "weight": next((m['metric_value'] for m in metrics if m['metric_code'] == 'WEIGHT'), None),
            },
            "health_status": {
                "bmi": next((m['metric_value'] for m in metrics if m['metric_code'] == 'BMI'), None),
                "calcium": next((m['metric_value'] for m in metrics if m['metric_code'] == 'CALCIUM'), None),
                "sodium": next((m['metric_value'] for m in metrics if m['metric_code'] == 'SODIUM'), None),
            },
            "nutrition": [
                {"label": "能量", "value": "1450/1800", "percent": "81%", "unit": "kcal"},
                {"label": "蛋白质", "value": "48/60", "percent": "80%", "unit": "g"},
                {"label": "钙", "value": "650/800", "percent": "81%", "unit": "mg"},
                {"label": "铁", "value": "8/10", "percent": "80%", "unit": "mg"},
                {"label": "锌", "value": "6/8", "percent": "75%", "unit": "mg"},
                {"label": "钠", "value": "2200/1500", "percent": "147%", "unit": "mg"}
            ],
            "food_ranking": [
                {"name": "炸鸡", "tags": ["高钠(1200mg/份)", "高热量(450kcal)"], "count": 3},
                {"name": "薯条", "tags": ["高钠(800mg/份)", "高脂肪"], "count": 2},
                {"name": "白米饭", "tags": ["碳水化合物", "低纤维"], "count": 7}
            ]
        }

        return jsonify({
            "status": "success",
            "data": response_data
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@member_bp.route('', methods=['GET'])
def get_members():
    members = FamilyMember.get_all()
    return jsonify({"status": "success", "data": members})

@member_bp.route('', methods=['POST'])
def create_member():
    """创建新成员"""
    required_fields = ['name', 'gender', 'birth_date', 'relation', 'family_id']
    data = request.get_json()

    # 数据验证
    if not all(field in data for field in required_fields):
        return jsonify({
            "status": "error",
            "message": f"缺少必填字段，需要: {', '.join(required_fields)}"
        }), 400

    if not isinstance(data['family_id'], int):
        return jsonify({
            "status": "error",
            "message": "family_id必须是整数"
        }), 400

    try:
        member_id = FamilyMember.create(data)
        return jsonify({
            "status": "success",
            "member_id": member_id
        }), 201
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@member_bp.route('/<int:member_id>', methods=['GET'])
def get_member(member_id):
    """获取单个成员详情"""
    try:
        member = FamilyMember.get_by_id(member_id)
        if not member:
            return jsonify({
                "status": "error",
                "message": "成员不存在"
            }), 404

        return jsonify({
            "status": "success",
            "data": member
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@member_bp.route('/search', methods=['GET'])
def search_members():
    """搜索家庭成员"""
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify({
            "status": "error",
            "message": "请输入搜索关键词"
        }), 400

    try:
        results = FamilyMember.search(keyword)
        return jsonify({
            "status": "success",
            "count": len(results),
            "data": results
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ---------------------- 健康指标相关路由 ----------------------
@member_bp.route('/<int:member_id>/metrics', methods=['GET'])
def get_member_metrics(member_id):
    """获取成员所有健康指标"""
    try:
        metrics = HealthMetric.get_by_member(member_id)
        return jsonify({
            "status": "success",
            "member_id": member_id,
            "count": len(metrics),
            "data": metrics
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@member_bp.route('/<int:member_id>/metrics', methods=['POST'])
def add_member_metric(member_id):
    """添加健康指标记录"""
    required_fields = ['metric_id', 'metric_value']
    data = request.get_json()

    # 数据验证
    if not all(field in data for field in required_fields):
        return jsonify({
            "status": "error",
            "message": f"缺少必填字段，需要: {', '.join(required_fields)}"
        }), 400

    if not isinstance(data['metric_id'], int):
        return jsonify({
            "status": "error",
            "message": "metric_id必须是整数"
        }), 400

    try:
        metric_id = HealthMetric.create(member_id, data)
        return jsonify({
            "status": "success",
            "metric_id": metric_id
        }), 201
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@member_bp.route('/<int:member_id>/basic', methods=['GET'])
def get_member_basic(member_id):
    """获取成员基本信息"""
    try:
        # 调用逻辑层获取数据
        basic_info = FamilyMember.get_basic_info(member_id)
        if not basic_info:
            return jsonify({"status": "error", "message": "成员不存在"}), 404

        return jsonify({
            "status": "success",
            "data": basic_info
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
@member_bp.route('/<int:member_id>/health-status', methods=['GET'])
def get_health_status(member_id):
    """获取成员健康状态"""
    try:
        health_status = HealthMetric.get_health_status(member_id)
        return jsonify({
            "status": "success",
            "data": health_status
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
