from typing import List, Dict, Optional
from management.dish_models import DishListItem, DishPage2SaveCmd
from dbconnect.dbconn import db

class DishData:
    @staticmethod
    def list_dish_page() -> List[DishListItem]:
        """
        返回页面1所需扁平字段，一行即一菜，无嵌套。
        字段顺序与页面列顺序保持一致。
        """
        sql = """
            SELECT d.dish_id            AS dish_id,
                    d.name,
                    d.rating,
                    d.dish_cook_time     AS dish_cook_time,
                    d.tags AS tags
                    FROM v3_dish_list d
        """
        rows = db.query(sql)
        return [DishListItem(**r) for r in rows]
# --------------- 页面2 单菜下拉框数据 ---------------
    @staticmethod
    def get_dish_meta(dish_id: int) ->  List[Dict]:
        sql = """
            SELECT d.dish_id            AS dish_id,
                    d.name,
                    d.rating,
                    d.dish_cook_time     AS dish_cook_time,
                    d.tags AS tags
                    FROM v3_dish_list_json d
            WHERE   d.dish_id = %s
        """
        return db.query(sql, dish_id)

    # --------------- 下拉框备选项 ---------------
    @staticmethod
    def list_categories() -> List[Dict]:
        return db.query("SELECT id, name FROM ejia_dish_category_tbl ORDER BY id")

    @staticmethod
    def list_series() -> List[Dict]:
        return db.query("SELECT series_id AS id, series_name AS name FROM ejia_dish_series_tbl ORDER BY series_id")

    @staticmethod
    def list_tags() -> List[Dict]:
        sql = """
            SELECT
                id          AS id,
                group_code  AS group_code,
                group_name  AS group_name,
                tag_code    AS tag_code,
                tag_name    AS tag_name,
                sort        AS sort
            FROM ejia_dish_tag_tbl
            ORDER BY group_code, sort
        """
        return db.query(sql)

    @staticmethod
    def list_meal_types() -> List[Dict]:
        return db.query("SELECT id, meal_type_name AS name FROM ejia_dish_meal_type ORDER BY id")
    # --------------- 页面2 保存 ---------------
    @staticmethod
    def save_dish(cmd: DishPage2SaveCmd) -> None:
        """
        先删再插，保持与原有 rel 表逻辑一致。
        所有下拉框值均可能为 None，表示清空对应关系。
        """
        # 1. 清空该菜品的所有相关 rel 记录
        db.execute("""
            DELETE FROM ejia_dish_category_rel
            WHERE  dish_id = %s
              AND  rel_type IN ('category', 'series', 'tag')
        """, cmd.dish_id)

        # 2. 分类
        if cmd.category_id is not None:
            db.execute("""
                INSERT INTO ejia_dish_category_rel(dish_id, category_id, rel_type, match_score)
                VALUES (%s, %s, 'category', %s)
            """, (cmd.dish_id, cmd.category_id, cmd.category_match_score or 0))

        # 3. 菜系
        if cmd.series_id is not None:
            db.execute("""
                INSERT INTO ejia_dish_category_rel(dish_id, category_id, rel_type)
                VALUES (%s, %s, 'series')
            """, (cmd.dish_id, cmd.series_id))

        # 4. 标签
        if cmd.tag_id is not None:
            db.execute("""
                INSERT INTO ejia_dish_category_rel(dish_id, category_id, rel_type)
                VALUES (%s, %s, 'tag')
            """, (cmd.dish_id, cmd.tag_id))

        # 5. 餐型（直接更新原表即可）
        if cmd.meal_type is not None:
            db.execute("""
                INSERT INTO ejia_dish_category_rel(dish_id, category_id, rel_type)
                VALUES (%s, %s, 'mealtype')
            """, (cmd.dish_id, cmd.meal_type))