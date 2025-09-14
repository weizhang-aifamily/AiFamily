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
            SELECT  d.id            AS dish_id,
                    d.name,
                    d.rating,
                    d.cook_time     AS dish_cook_time,
                    c.name          AS category_name,
                    dcr.match_score AS category_match_score,
                    dcr.rel_type    AS category_rel_type,
                    s.series_name,
                    t.tag_name,
                    m.meal_type_name
            FROM    ejia_dish d
            LEFT JOIN ejia_dish_category_rel dcr
                   ON d.id = dcr.dish_id
            LEFT JOIN ejia_dish_category_tbl c
                   ON dcr.category_id = c.id AND dcr.rel_type = 'category'
            LEFT JOIN ejia_dish_series_tbl s
                   ON dcr.category_id = s.series_id AND dcr.rel_type = 'series'
            LEFT JOIN ejia_dish_tags_tbl t
                   ON dcr.category_id = t.tag_id AND dcr.rel_type = 'tag'
            LEFT JOIN ejia_dish_meal_type m 
                    ON dcr.category_id = m.id AND dcr.rel_type = 'mealtype' 
            ORDER BY d.id
        """
        rows = db.query(sql)
        return [DishListItem(**r) for r in rows]
# --------------- 页面2 单菜下拉框数据 ---------------
    @staticmethod
    def get_dish_meta(dish_id: int) ->  List[Dict]:
        sql = """
            SELECT  d.id            AS dish_id,
                    d.name,
                    c.id            AS category_id,
                    c.name          AS category_name,
                    dcr.match_score AS category_match_score,
                    dcr.rel_type    AS category_rel_type,
                    s.series_id,
                    s.series_name,
                    t.tag_id,
                    t.tag_name,
                    mt.meal_type,
                    mt.meal_type_name
            FROM    ejia_dish d
              LEFT JOIN ejia_dish_category_rel dcr
                   ON d.id = dcr.dish_id
            LEFT JOIN ejia_dish_category_tbl c
                   ON dcr.category_id = c.id AND dcr.rel_type = 'category'
            LEFT JOIN ejia_dish_series_tbl s
                   ON dcr.category_id = s.series_id AND dcr.rel_type = 'series'
            LEFT JOIN ejia_dish_tags_tbl t
                   ON dcr.category_id = t.tag_id AND dcr.rel_type = 'tag'
            LEFT JOIN ejia_dish_meal_type mt 
                    ON dcr.category_id = mt.id AND dcr.rel_type = 'mealtype' 
            WHERE   d.id = %s
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
        return db.query("SELECT tag_id AS id, tag_name AS name FROM ejia_dish_tags_tbl ORDER BY tag_id")

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