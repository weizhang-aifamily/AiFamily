from flask import Blueprint, Flask, render_template, request, redirect, url_for
import json
from management.dish_data import DishData
from management.dish_models import DishPage2SaveCmd

dish_bp = Blueprint('dish', __name__, url_prefix='/dish')


# ------------- 页面1：dish 列表 -------------
@dish_bp.route("/dishes")
def dish_list():
    rows = DishData.list_dish_page()
    return render_template("dish_list.html", dishes=rows)

# ------------- 页面2：单菜编辑 -------------
@dish_bp.route("/dish/<int:dish_id>")
def dish_edit(dish_id):
    meta   = DishData.get_dish_meta(dish_id)
    # cats   = DishData.list_categories()
    # series = DishData.list_series()
    tags   = DishData.list_tags()
    # meals  = DishData.list_meal_types()
    # 解析meta中每个菜品的tags字段（从JSON字符串转换为Python对象）
    for row in meta:
        if isinstance(row.get('tags'), str):
            try:
                row['tags'] = json.loads(row['tags'])
            except json.JSONDecodeError:
                row['tags'] = []  # 如果解析失败，设置为空列表
        elif row.get('tags') is None:
            row['tags'] = []  # 如果为None，也设置为空列表
    return render_template("dish_edit.html",
                           rows=meta,
                           tags=tags)

# ------------- 页面2：保存 -------------
@dish_bp.route("/dish/<int:dish_id>/save", methods=["POST"])
def dish_save(dish_id):
    cmd = DishPage2SaveCmd(dish_id=dish_id, **request.form)
    DishData.save_dish(cmd)
    return redirect(url_for("dish.dish_list"))