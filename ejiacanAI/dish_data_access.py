from typing import List, Dict
from models import UserSnapshot, Dish, Context   # 仅依赖模型

class EnhancedDataAccess:
    def __init__(self, db):
        self.db = db

    # ---------- 用户画像 ----------
    def get_user_snapshot(self, member_id: int) -> UserSnapshot:
        # 1) 每日营养素目标 & 上限
        sql_targets = f"""
            SELECT nutrient_id, need_qty
            FROM ejia_member_daily_nutrient
            WHERE member_id = {member_id}
        """
        rows = self.db.query(sql_targets)
        daily_targets = {r["nutrient_id"]: float(r["need_qty"]) for r in rows}

        # 2) 需求代码权重（基因/肠菌等）
        sql_weights = f"""
            SELECT dn.need_code, COALESCE(dn.offset_val, 1.0) AS weight
            FROM ejia_member_diet_need dn
            WHERE dn.member_id = {member_id}
        """
        weights = {r["need_code"]: float(r["weight"]) for r in self.db.query(sql_weights)}

        # 3) 最近 7 天已吃菜品
        sql_recent = f"""
            SELECT DISTINCT dish_id
            FROM ejia_member_food_log
            WHERE member_id = {member_id}
              AND eat_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        """
        recent = [int(r["dish_id"]) for r in self.db.query(sql_recent)]

        return UserSnapshot(
            member_id=member_id,
            daily_targets=daily_targets,
            hard_caps={},            # 如需上限，可再查表
            gene_weights=weights,
            recent_7d_dish_ids=recent
        )

    # ---------- 菜品池 ----------
    def get_dish_pool(self, meal_type: str) -> List[Dish]:
        # 取该餐次所有菜品
        sql = f"""
            SELECT d.id           AS dish_id,
                   d.name as food_name,
                   d.cook_time,
                   dn.nutrient_name,
                   dn.nutrient_amount,
                   d.name,
                   fi.amount_grams
            FROM ejia_dish d
            JOIN view_dish_nutrients_long dn ON dn.dish_id = d.id
            JOIN (
                SELECT dish_id, amount_grams
                FROM ejia_dish_food_rel dfr
                JOIN foods f ON f.fdc_id = dfr.food_id
            ) fi ON fi.dish_id = d.id
            JOIN ejia_dish_meal_type dmt on d.id = dmt.dish_id
            WHERE dmt.meal_type = '{meal_type}'
        """
        rows = self.db.query(sql)

        # 按 dish_id 聚合
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
                    last_seen_days=0   # 由算法动态计算
                )
            dish_map[did].nutrients[r["nutrient_name"]] = float(r["nutrient_amount"])
            dish_map[did].ingredients[r["food_name"]] = float(r["amount_grams"])

        return list(dish_map.values())