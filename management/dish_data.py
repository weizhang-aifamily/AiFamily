from typing import List, Dict, Optional
from management.dish_models import DishListItem, DishPage2SaveCmd, NutrientRule
from dbconnect.dbconn import db

class DishData:
    @staticmethod
    def list_dish_page(tag_codes: List[str] = None) -> List[DishListItem]:
        """
        返回页面1所需扁平字段，一行即一菜，无嵌套。
        字段顺序与页面列顺序保持一致。
        如果 tag_codes 为空则查全表。
        """
        if tag_codes:
            # ① 拼占位串
            in_str = ",".join([f"'{t.strip()}'" for t in tag_codes])
            # ② 关键：having 计数 = 传入 tag 个数
            where_tag = f"""
              AND d.dish_id IN (
                  SELECT d.id
                  FROM ejia_dish d
                  JOIN ejia_dish_tag_rel dtr ON d.id = dtr.dish_id
                  JOIN ejia_dish_tag_tbl dtt ON dtr.tag_id = dtt.id
                  WHERE dtt.tag_code IN ({in_str})
                  GROUP BY d.id
                  HAVING COUNT(DISTINCT dtt.tag_code) = {len(tag_codes)}
              )
            """
        else:
            where_tag = ""

        sql = f"""
            SELECT d.dish_id,
                   d.name,
                   d.rating,
                   d.dish_cook_time,
                   d.tags,
                   d.need_tags
            FROM v3_dish_list_all d
            WHERE 1=1 {where_tag}
            
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
                dfr.amount_grams,
                dfr.is_main_food
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
    @staticmethod
    def list_oneTags(group_code: str) -> List[Dict]:
        sql = """
            SELECT
                id          AS id,
                group_code  AS group_code,
                group_name  AS group_name,
                tag_code    AS tag_code,
                tag_name    AS tag_name,
                sort        AS sort
            FROM ejia_dish_tag_tbl
            where group_code = %s
            ORDER BY sort
        """
        return db.query(sql, group_code)

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
    def save_dish_foods(dish_id: int, food_codes: List[str], amount_grams: List[int],
                        is_main_food: List[int] = None) -> None:
        """
        幂等保存菜品食材关系
        :param dish_id: 菜品主键
        :param food_codes: 食材代码列表
        :param amount_grams: 对应的用量列表（克）
        :param is_main_food: 对应的是否为主料列表（1是主料，0不是主料）
        """
        # 1. 清空旧关系
        db.execute("DELETE FROM ejia_dish_food_rel WHERE dish_id = %s", dish_id)

        # 2. 批量写入新关系
        if food_codes and len(food_codes) == len(amount_grams):
            # 如果没有提供is_main_food参数，默认为0
            if is_main_food is None:
                is_main_food = [0] * len(food_codes)

            # 确保is_main_food长度与food_codes一致
            if len(is_main_food) != len(food_codes):
                is_main_food = [0] * len(food_codes)

            data = [
                (dish_id, food_code, amount, main_food)
                for food_code, amount, main_food in zip(food_codes, amount_grams, is_main_food)
            ]

            db.executemany(
                "INSERT INTO ejia_dish_food_rel(dish_id, food_id, amount_grams, is_main_food) VALUES (%s, %s, %s, %s)",
                data
            )

# ----------- 1. 读取需求标签规则表 -----------
    @staticmethod
    def get_need_rule() -> List[NutrientRule]:
        sql = """
            SELECT id, need_code, nutrient,
                   comparison_operator, threshold_value, unit
            FROM ejia_enum_diet_need_nutrient_rule
        """
        rows = db.query(sql)
        return [NutrientRule(**r) for r in rows]

    @staticmethod
    def get_dish_food_nut(dish_id: int) -> List[Dict]:
        """
        原样返回 v3_dish_food_complete_view 里该菜品的所有食材行
        不做任何汇总、转换，供上层按需处理
        """
        sql = """
            SELECT *
            FROM v3_dish_food_complete_view
            WHERE dish_id = %s
        """
        return db.query(sql, dish_id)

    def calc_per_100g_raw(rows: List[dict]) -> Dict[str, float]:
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

    @staticmethod
    def update_dish_needtag(dish_id: int, need_codes: List[str]) -> None:
        """
        幂等更新 ejia_dish.need_tags 字段
        空列表表示清空
        """
        # 去重并保持顺序
        sorted_codes = sorted(set(need_codes))
        tag_str = ",".join(sorted_codes) if sorted_codes else ""
        db.execute(
            "UPDATE ejia_dish SET need_tags = %s WHERE id = %s",
            (tag_str, dish_id)
        )