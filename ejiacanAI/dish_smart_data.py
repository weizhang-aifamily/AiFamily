# dish_smart_data.py
from typing import List, Dict
from dish_smart_models import FamilyMember, Dish, RecommendationConfig
from dbconnect.dbconn import db   # 已提供 query

class DishSmartData:
    # ---------- 用户画像 ----------
    @staticmethod
    def get_user_snapshot(member_id: int, cfg: RecommendationConfig) -> FamilyMember:
        # 1) 每日营养素目标
        sql_targets = """
            SELECT nutrient_id, need_qty
            FROM ejia_member_daily_nutrient
            WHERE member_id = %s
        """
        rows = db.query(sql_targets, (member_id,))
        daily_targets = {str(r["nutrient_id"]): float(r["need_qty"]) for r in rows}

        # 2) 需求权重（基因/肠菌） TODO ejia_need_dish_match 
        sql_weights = """
            SELECT dn.need_code, COALESCE(dn.offset_val, 1.0) AS weight
            FROM ejia_member_diet_need dn
            WHERE dn.member_id = %s
        """
        weights = {r["need_code"]: float(r["weight"]) for r in db.query(sql_weights, (member_id,))}

        # 3) 最近 N 天已吃
        sql_recent = f"""
            SELECT DISTINCT dish_id
            FROM ejia_member_food_log
            WHERE member_id = %s
              AND eat_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        """
        recent = [int(r["dish_id"]) for r in db.query(sql_recent, (member_id, cfg.history_window_days))]
        # 4) 过敏
        sql = """
              SELECT ea.code AS allergen_code
              FROM ejia_member_allergen ma
                       JOIN ejia_enum_allergen_tbl ea ON ea.code = ma.allergen_code
              WHERE ma.member_id = %s \
              """
        allergens = [str(row["allergen_code"]) for row in db.query(sql, (member_id,))]
        sql = """
              SELECT taboo_type
              FROM ejia_member_diet_taboo
              WHERE member_id = %s \
              """
        taboos = [str(row["taboo_type"]) for row in db.query(sql, (member_id,))]
        return FamilyMember(
            member_id=member_id,
            daily_targets=daily_targets,
            hard_caps={},               # 如需上限再扩展
            gene_weights=weights,
            micro_weights={},           # 如需肠菌再扩展
            recent_7d_dish_ids=recent,
            cfg=cfg,
            allergens=allergens,
            #taboos=taboos
        )

    # ---------- 菜品池 ----------
    @staticmethod
    def get_dish_pool(meal_type: str) -> List[Dish]:
        sql = """
            SELECT d.id AS dish_id,
                   d.name,
                   d.cook_time,
                   d.rating AS popularity,
                   n.nutrient_name,
                   n.nutrient_amount,
                   i.ingredient_name,
                   i.amount_grams
            FROM ejia_dish d
            JOIN view_dish_nutrients_long n ON n.dish_id = d.id
            JOIN (
                SELECT dfr.dish_id,
                       f.description AS ingredient_name,
                       dfr.amount_grams
                FROM ejia_dish_food_rel dfr
                JOIN foods f ON f.fdc_id = dfr.food_id
            ) i ON i.dish_id = d.id
            JOIN ejia_dish_meal_type mt ON mt.dish_id = d.id
            WHERE mt.meal_type = %s
        """
        rows = db.query(sql, (meal_type,))
        dish_map: Dict[int, Dish] = {}
        for r in rows:
            did = int(r["dish_id"])
            if did not in dish_map:
                dish_map[did] = Dish(
                    dish_id=did,
                    name=r["name"],
                    nutrients={},
                    ingredients={},
                    cook_time=int(r["cook_time"]),
                    popularity=float(r["popularity"]),
                    allergens=[]
                )
            dish_map[did].nutrients[r["nutrient_name"]] = float(r["nutrient_amount"])
            dish_map[did].ingredients[r["ingredient_name"]] = float(r["amount_grams"])
        return list(dish_map.values())

    # ---------- 等级配置 ----------
    @staticmethod
    def get_grade_dict() -> Dict[str, Dict]:
        """返回等级字典 {grade_code: {...}}"""
        sql = "SELECT grade_code, grade_name, min_points, max_points, description FROM ejia_grade_dict"
        rows = db.query(sql)
        return {r["grade_code"]: dict(r) for r in rows}

    @staticmethod
    def get_grade_config(grade_code: str) -> RecommendationConfig:
        """根据等级代码返回 RecommendationConfig"""
        sql = """
            SELECT config_key, config_value
            FROM ejia_grade_config
            WHERE grade_code = %s
        """
        rows = db.query(sql, (grade_code,))
        cfg = RecommendationConfig()
        for r in rows:
            setattr(cfg, r["config_key"], float(r["config_value"]))
        return cfg

    @staticmethod
    def get_user_grade(member_id: int) -> str:
        """返回用户当前等级代码"""
        sql = "SELECT grade_code FROM ejia_user_grade WHERE member_id = %s"
        row = db.query(sql, (member_id,))
        if row:
            return str(row[0])  # row 是 tuple，取第 0 列
        return "bronze"

    @staticmethod
    def get_dish_allergens(dish_id: int) -> List[str]:
        sql = """
            SELECT ea.code AS allergen_code
            FROM ejia_dish_food_rel dfr
            JOIN ejia_enum_allergen_tbl ea ON ea.food_id = dfr.food_id
            WHERE dfr.dish_id = %s
        """
        return [row["allergen_code"] for row in db.query(sql, (dish_id,))]

    @staticmethod
    def get_dish_taboos(dish_id: int) -> List[str]:
        sql = """
            SELECT edt.taboo_type
            FROM ejia_dish_food_rel dfr
            JOIN ejia_enum_diet_taboo edt ON edt.food_id = dfr.food_id
            WHERE dfr.dish_id = %s
        """
        return [row["taboo_type"] for row in db.query(sql, (dish_id,))]