from typing import List, Dict

from flask import Blueprint, Flask, render_template, request, redirect, url_for, jsonify

from ejiacanAI.dish2_combo_models import MealRequest
from models.search_data import SearchData
from ejiacanAI.dish2_combo_generator import MealGeneratorV2

search_bp = Blueprint('search', __name__, url_prefix='/search')


# ------------- 页面1：dish 列表 -------------
@search_bp.route("/keyword", methods=['POST'])
def search_dishes_by_keyword():
    try:
        data = request.get_json()
        keyword = data.get('keyword', "")
        limit = 20
        req = MealRequest(
            keyword=keyword,
        )
        result = SearchData.search_dishes_by_keyword(req, 200)
        dish_list = MealGeneratorV2.build_true_dishes(result,req)
        limit_dishes = dish_list[:min(limit, len(dish_list))]
        # 转换为字典返回
        return jsonify({
            'success': True,
            "data": limit_dishes,
            'result': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500