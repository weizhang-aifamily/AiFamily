# dish_combo_data.py  追加内容
from typing import List, Optional

from ejiacanAI.dish2_combo_models import DishFoodNutrient, MemberNeedNutrient, MealRequest, \
    MealStructure  # 保证与现有 import 风格一致
from dbconnect.dbconn import db

class DishComboData:
    ...  # 原有代码不动

    # -------------------------------------------------
    # 1. 读取 v3_dish_food_complete_view 视图
    # -------------------------------------------------
    @staticmethod
    def list_dish_food_nutrient(dish_ids: List[int], req: MealRequest) -> List[DishFoodNutrient]:
        # 1. 收集所有要满足的 tags
        must_tags = []
        if req.meal_type and req.meal_type != "all":
            must_tags.append(req.meal_type)
        must_tags = [t for t in must_tags if t]  # 去空

        # 2. 拼 tag 子查询（必须全部满足）
        tag_where = ""
        if must_tags:
            in_str = ",".join([f"'{t}'" for t in must_tags])
            tag_where = f"""
            AND v.dish_id IN (
                SELECT d.id
                FROM ejia_dish d
                JOIN ejia_dish_tag_rel dtr ON d.id = dtr.dish_id
                JOIN ejia_dish_tag_tbl dtt ON dtr.tag_id = dtt.id
                WHERE dtt.tag_code IN ({in_str})
                GROUP BY d.id
                HAVING COUNT(DISTINCT dtt.tag_code) = {len(must_tags)}
            )
            """

        # 3. 主查询
        dish_where = (
            "WHERE dish_id IN ({})".format(",".join(map(str, dish_ids))) if dish_ids else ""
        )
        sql = f"""
            SELECT *
            FROM v3_dish_food_complete_view v
            where 1=1
            {dish_where}
            {tag_where}
            ORDER BY dish_id, food_id
        """
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

    @staticmethod
    def get_meal_structure(max_dishs: int, req: MealRequest) -> Optional[MealStructure]:
        """根据菜品ID获取完整菜品信息"""
        sql = """
              SELECT d.main_dishes, 
                     d.side_dishes, 
                     d.staple_foods, 
                     d.soups
              FROM ejia_meal_structure d
              WHERE d.max_dishes = %s 
              and d.meal_type = %s
              """
        rows = db.query(sql, (max_dishs,req.meal_type))

        if not rows:
            return None

        # 取第一条记录获取基本信息
        first_row = rows[0]
        return MealStructure(
            main_dishes=first_row["main_dishes"],
            side_dishes=first_row["side_dishes"],
            staple_foods=first_row["staple_foods"],
            soups=first_row["soups"]
        )