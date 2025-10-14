from typing import List, Dict

from flask import Blueprint, Flask, render_template, request, redirect, url_for
import json
from management.dish_data import DishData
from management.dish_models import DishPage2SaveCmd

dish_bp = Blueprint('dish', __name__, url_prefix='/dish')


# ------------- 页面1：dish 列表 -------------
@dish_bp.route("/dishes")
def dish_list():
    # 1. 把前端多选框值合并成 List[str]
    selected_tags = request.args.getlist("tags")  # ['lu','yue','brunch']

    # 2. 查数据
    rows = DishData.list_dish_page(tag_codes=selected_tags)

    # 3. 复用原逻辑
    cuisineTags = DishData.list_oneTags("cuisine")
    mealtimetags = DishData.list_oneTags("meal_time")

    # 4. 回显用
    return render_template("dish_list.html",
                           dishes=rows,
                           cuisineTags=cuisineTags,
                           mealtimetags=mealtimetags,
                           selected_tags=selected_tags)

# ------------- 页面2：单菜编辑 -------------
@dish_bp.route("/<int:dish_id>")
def dish_edit(dish_id):
    dishtags = DishData.get_dish_tags(dish_id)
    dishfood = DishData.get_dish_food(dish_id)
    tags = DishData.list_tags()

    # 处理结果 - 即使没有标签也会有一条菜品记录
    from collections import defaultdict
    dish_map = defaultdict(list)

    for row in dishtags:
        dish_id = row['dish_id']
        dish_map[dish_id].append(row)

    rows = []
    for did, raw in dish_map.items():
        # 获取菜品基本信息（第一条记录就有）
        dish_info = {
            'dish_id': did,
            'name': raw[0]['dish_name'],
            'rating': raw[0]['rating'],
            'dish_cook_time': raw[0]['cook_time'],
            'tags': [],
            'food': [],
        }

        # 添加标签信息（如果有的话）
        for r in raw:
            if r['tag_id']:  # 只有当有标签ID时才添加
                dish_info['tags'].append({
                    'code': r['tag_code'],
                    'group': r['group_code'],
                    'name': r['tag_name']
                })
                # 添加食材信息（从dishfood中获取）
        for food_row in dishfood:
            if food_row['dish_id'] == did and food_row['foodCode']:  # 只有当有食材ID时才添加
                dish_info['food'].append({
                    'code': food_row['foodCode'],
                    'category1': food_row['category1'],
                    'category2': food_row['category2'],
                    'name': food_row['foodName'],
                    'amount_grams': food_row['amount_grams']
                })
        rows.append(dish_info)

    return render_template("dish_edit.html",
                           rows=rows,
                           tags=tags)

# ------------- 页面2：保存 -------------
@dish_bp.route("/<int:dish_id>/save", methods=["POST"],endpoint="save_dish")
def save_dish(dish_id: int):
    # 保存标签
    tag_ids = request.form.getlist("tags[]", type=int)
    DishData.save_dish_tags(dish_id, tag_ids)

    # 获取所有食材代码和用量（包括新添加的）
    food_codes = request.form.getlist("food_codes", type=str)
    food_amounts = []

    # 过滤掉空的食材代码并获取对应的用量
    valid_food_data = []
    for food_code in food_codes:
        if food_code.strip():  # 过滤空值
            amount_key = f"amount_grams_{food_code}"
            amount = request.form.get(amount_key, type=int)
            # 如果找不到特定食材的用量，使用通用的用量字段
            if amount is None:
                amount = request.form.get("amount_grams", type=int)
            valid_food_data.append((food_code, amount if amount is not None else 0))

    # 分离代码和用量
    if valid_food_data:
        food_codes, food_amounts = zip(*valid_food_data)
    else:
        food_codes, food_amounts = [], []

    # 保存食材
    DishData.save_dish_foods(dish_id, food_codes, food_amounts)
    return redirect(url_for("dish.dish_list"))
# ------------- 给某个dish打上标签，根据ejia_enum_diet_need_nutrient_rule定义 -------------
@dish_bp.route("/<int:dish_id>/needtag", methods=["POST"],endpoint="needtag_dish")
def needtag_dish(dish_id: int):
    """读规则 → 算营养 → 比阈值 → 写标签"""
    rules = DishData.get_need_rule()
    rows = DishData.get_dish_food_nut(dish_id)  # 原始食材行
    total = _calc_per_100g_raw(rows)  # 手动算

    hit_codes = []
    for rule in rules:
        val = total.get(rule.nutrient_name)
        if val is None:
            continue
        ok = False
        if rule.comparison_operator == ">=":
            ok = val >= rule.threshold_value
        elif rule.comparison_operator == "<=":
            ok = val <= rule.threshold_value
        if ok:
            hit_codes.append(rule.need_code)

    DishData.update_dish_needtag(dish_id, hit_codes)
    return redirect(url_for("dish.dish_list"))

def _calc_per_100g_raw(rows: List[dict]) -> Dict[str, float]:
    """
    手动按用量重新计算每100g成品菜的营养素
    视图里：
        营养列 = 每100g食材可食部含量
        food_amount_grams = 该食材在菜品里的用量(g)
    公式：
        贡献 = 营养列 * food_amount_grams * edible / 100
    再按菜品总重归一化到100g成品
    """
    # 菜品总重（生食总克数）
    total_weight = sum(float(r['food_amount_grams']) for r in rows)
    if total_weight == 0:
        return {}
    nutrient_cols = [
        "energyKCal", "protein", "fat", "CHO", "dietaryFiber",
        "cholesterol", "vitaminA", "thiamin", "riboflavin", "niacin",
        "vitaminC", "vitaminETotal", "Ca", "P", "K", "Na", "Mg",
        "Fe", "Zn", "Se", "Cu", "Mn"
    ]
    total = {col: 0.0 for col in nutrient_cols}

    for r in rows:
        w = float(r['food_amount_grams'])
        edible = float(r['edible']) / 100.0  # 可食部比例
        for col in nutrient_cols:
            per100g = float(r.get(col, 0))  # 每100g可食部含量
            total[col] += per100g * w * edible / 100.0

    # 归一化到每100g成品
    factor = 100.0 / total_weight
    return {col: val * factor for col, val in total.items()}

@dish_bp.route("/bodyimage")
def body_image():

    return render_template("bodyimage.html")
