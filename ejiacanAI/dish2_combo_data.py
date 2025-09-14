# dish_combo_data.py  追加内容
from typing import List
from ejiacanAI.dish2_combo_models import DishFoodNutrient, MemberNeedNutrient   # 保证与现有 import 风格一致
from dbconnect.dbconn import db

class DishComboData:
    ...  # 原有代码不动

    # -------------------------------------------------
    # 1. 读取 v2_dish_food_nutrient 视图
    # -------------------------------------------------
    @staticmethod
    def list_dish_food_nutrient(dish_ids: List[int]) -> List[DishFoodNutrient]:
        """
        直接从 v2_dish_food_nutrient 视图查询，返回模型列表
        """
        sql = """
            SELECT *
            FROM v3_dish_food_complete_view
            {}
            ORDER BY dish_id, food_id
        """.format(
            "WHERE dish_id IN ({})".format(",".join(map(str, dish_ids))) if dish_ids else ""
        )
        rows = db.query(sql)
        return [DishFoodNutrient(**r) for r in rows]

    # -------------------------------------------------
    # 2. 读取 v2_member_need_nutrient 视图
    # -------------------------------------------------
    @staticmethod
    def list_member_need_nutrient(member_ids: List[int]) -> List[MemberNeedNutrient]:
        """
        直接从 v2_member_need_nutrient 视图查询，返回模型列表
        """
        sql = """
            SELECT *
            FROM v2_member_need_nutrient
            WHERE member_id IN ({})
        """.format(",".join(map(str, member_ids)) if member_ids else "NULL")
        rows = db.query(sql)
        return [MemberNeedNutrient(**r) for r in rows]

    # 4. 家庭过敏原
    @staticmethod
    def get_family_allergens(member_ids: List[int]) -> List[str]:
        ids_str = ",".join(map(str, member_ids))
        return [row["allergen_code"] for row in db.query(
            f"SELECT DISTINCT allergen_code FROM ejia_member_allergen WHERE member_id IN ({ids_str})"
        )]