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
    def get_dish_tags(dish_id: int) -> List[Dict]:
        sql = """
                SELECT 
                    d.id as dish_id,
                    d.name as dish_name,
                    d.rating,
                    d.cook_time,
                    dtt.id as tag_id,
                    dtt.group_code,
                    dtt.group_name, 
                    dtt.tag_code,
                    dtt.tag_name 
                FROM ejia_dish d
                LEFT JOIN ejia_dish_tag_rel dtr ON d.id = dtr.dish_id
                LEFT JOIN ejia_dish_tag_tbl dtt ON dtr.tag_id = dtt.id
                WHERE d.id = %s 
                ORDER BY dtt.group_code, dtt.sort;
            """
        return db.query(sql, dish_id)

    @staticmethod
    def get_dish_food(dish_id: int) -> List[Dict]:
        sql = """
            SELECT 
                d.id as dish_id,
                d.name as dish_name,
                d.rating,
                d.cook_time,
                fn.foodCode,
                fn.category1,
                fn.category2,
                fn.foodName,
                dfr.amount_grams
            FROM ejia_dish d
            LEFT JOIN ejia_dish_food_rel dfr ON d.id = dfr.dish_id
            LEFT JOIN food_nutrition fn ON fn.foodCode = dfr.food_id
            WHERE d.id = %s
            ;
            """
        return db.query(sql, dish_id)

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

    # --------------- 页面2 保存 ---------------
    @staticmethod
    def save_dish_tags(dish_id: int, tag_ids: List[int]) -> None:
        """
        幂等保存菜品标签关系
        :param dish_id: 菜品主键
        :param tag_ids: 需要绑定的 tag_id 列表（空列表=清空）
        """
        # 1. 清空旧关系
        db.execute("DELETE FROM ejia_dish_tag_rel WHERE dish_id = %s", dish_id)

        # 2. 批量写入新关系
        if tag_ids:
            db.executemany(
                "INSERT INTO ejia_dish_tag_rel(dish_id, tag_id) VALUES (%s, %s)",
                [(dish_id, tid) for tid in tag_ids]
            )

    @staticmethod
    def save_dish_foods(dish_id: int, food_codes: List[str], amount_grams: List[int]) -> None:
        """
        幂等保存菜品食材关系
        :param dish_id: 菜品主键
        :param food_codes: 食材代码列表
        :param amount_grams: 对应的用量列表（克）
        """
        # 1. 清空旧关系
        db.execute("DELETE FROM ejia_dish_food_rel WHERE dish_id = %s", dish_id)

        # 2. 批量写入新关系
        if food_codes and len(food_codes) == len(amount_grams):
            data = [(dish_id, food_code, amount) for food_code, amount in zip(food_codes, amount_grams)]

            db.executemany(
                "INSERT INTO ejia_dish_food_rel(dish_id, food_id, amount_grams) VALUES (%s, %s, %s)",
                data
            )