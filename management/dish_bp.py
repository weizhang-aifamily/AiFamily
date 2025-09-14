from flask import Blueprint, Flask, render_template, request, redirect, url_for
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
    cats   = DishData.list_categories()
    series = DishData.list_series()
    tags   = DishData.list_tags()
    meals  = DishData.list_meal_types()
    return render_template("dish_edit.html",
                           rows=meta,
                           categories=cats,
                           series=series,
                           tags=tags,
                           meals=meals)

# ------------- 页面2：保存 -------------
@dish_bp.route("/dish/<int:dish_id>/save", methods=["POST"])
def dish_save(dish_id):
    cmd = DishPage2SaveCmd(dish_id=dish_id, **request.form)
    DishData.save_dish(cmd)
    return redirect(url_for("dish.dish_list"))