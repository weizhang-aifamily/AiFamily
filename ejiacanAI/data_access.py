from typing import List
from ejiacanAI.models import Dish, FamilyNeed

class DataAccess:
    def __init__(self, db):
        self.db = db

    def fetch_family_need(self, member_ids: List[int]) -> FamilyNeed:
        ids_str = ','.join(map(str, member_ids))
        sql = f"""
            SELECT
                COALESCE(SUM(CASE WHEN nutrient='calcium' AND direction=1  THEN threshold ELSE 0 END), 0) AS calcium_target,
                COALESCE(SUM(CASE WHEN nutrient='iron'    AND direction=1  THEN threshold ELSE 0 END), 0) AS iron_target,
                COALESCE(SUM(CASE WHEN nutrient='sodium'  AND direction=-1 THEN threshold ELSE 9999 END), 9999) AS sodium_limit,
                COALESCE(SUM(CASE WHEN nutrient='purine'  AND direction=-1 THEN threshold ELSE 9999 END), 9999) AS purine_limit,
                COALESCE(SUM(CASE WHEN nutrient='kcal'    AND direction=1  THEN threshold ELSE 2200 END), 2200) AS kcal_limit
            FROM ejia_member_diet_need_nutrient
            WHERE member_id IN ({ids_str})
        """
        row = self.db.query(sql)[0]
        # 确保所有数值都是浮点数
        row = {k: float(v) for k, v in row.items()}
        return FamilyNeed(**row)

    def fetch_safe_dishes(self, member_ids: List[int]) -> List[Dish]:
        ids_str = ','.join(map(str, member_ids))
        sql = f"""
            SELECT d.id, d.name, d.emoji, d.default_portion_g,
                   d.max_servings,
                   COALESCE(dn.calcium, 0) as calcium,
                   COALESCE(dn.iron, 0) as iron,
                   COALESCE(dn.sodium, 0) as sodium,
                   COALESCE(dn.purine, 0) as purine,
                   COALESCE(dn.kcal, 0) as kcal
            FROM ejia_dish d
            JOIN v_dish_nutrient_per_100g dn ON dn.dish_id = d.id
            WHERE d.id NOT IN (
                SELECT DISTINCT recipe_id
                FROM ejia_recipe_allergen ra
                JOIN ejia_member_allergen ma ON ma.allergen_code = ra.allergen_code
                WHERE ma.member_id IN ({ids_str})
            )
        """
        rows = self.db.query(sql)
        # 确保所有数值都是浮点数
        for row in rows:
            row['default_portion_g'] = float(row['default_portion_g'])
            row['calcium'] = float(row['calcium'])
            row['iron'] = float(row['iron'])
            row['sodium'] = float(row['sodium'])
            row['purine'] = float(row['purine'])
            row['kcal'] = float(row['kcal'])
        return [Dish(**r) for r in rows]