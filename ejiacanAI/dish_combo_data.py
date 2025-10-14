# dish_combo_data.py
from typing import List, Dict, Tuple, Optional

from ejiacanAI.MealStructureGenerator import MealStructure
from ejiacanAI.dish_combo_models import Dish, MemberInfo
from dbconnect.dbconn import db

class DishComboData:

    # 1. 家庭总需求上限
    @staticmethod
    def get_family_needs(member_ids: List[int]) -> Dict[str, float]:
        ids_str = ",".join(map(str, member_ids))
        sql = f"""
            SELECT nutrient_code, COALESCE(SUM(max_need_qty), 0) AS max_total
            FROM ejia_member_daily_nutrient_actual
            WHERE member_id IN ({ids_str})
            GROUP BY nutrient_code
        """
        return {str(r["nutrient_code"]): float(r["max_total"]) for r in db.query(sql)}

    # 2. 需求池（已声明 + 外推 + 兜底）
    # dish_combo_data.py

    @staticmethod
    def get_need_pool(member_ids: List[int]) -> Dict[int, List[str]]:
        """
        获取成员需求映射 {member_id: [need_codes]}
        完全保持原有get_need_pool的逻辑，只改变返回格式
        """
        if not member_ids:
            return {}

        ids_str = ",".join(map(str, member_ids))

        # 完全保持原有的SQL逻辑，但修改返回格式
        sql = f"""
            SELECT 
                um.id as member_id,
                -- 已声明的需求
                COALESCE(
                    (SELECT GROUP_CONCAT(DISTINCT dmn.need_code) 
                     FROM ejia_member_diet_need dmn 
                     WHERE dmn.member_id = um.id), 
                    ''
                ) as declared_needs,
                -- 外部推断的需求
                COALESCE(
                    (SELECT GROUP_CONCAT(DISTINCT ec.code)
                     FROM ejia_enum_diet_need_tbl ec
                     WHERE ec.is_external = 1
                       OR ec.code IN (
                           SELECT CASE
                               WHEN um.age BETWEEN 3 AND 12 THEN 'CHILD'
                               WHEN um.age < 3 THEN 'TODDLER'
                               ELSE 'ADULT'
                           END
                       )),
                    ''
                ) as external_needs
            FROM ejia_user_family_member um
            WHERE um.id IN ({ids_str})
        """

        result = {}
        for row in db.query(sql):
            member_id = row["member_id"]
            needs = []

            # 已声明的需求
            if row["declared_needs"]:
                needs.extend(row["declared_needs"].split(','))

            # 外部推断的需求
            if row["external_needs"]:
                needs.extend(row["external_needs"].split(','))

            result[member_id] = list(set(needs))  # 去重

        return result

    # 3. 菜品池 + 过敏原（food_id）
    @staticmethod
    def get_dish_pool2() -> List[Dish]:
        sql = """
            SELECT d.id, d.name, d.cook_time, d.default_portion_g,
                   n.nutrient_code, n.nutrient_amount,
                   f.description AS ingredient
            FROM ejia_dish d
            JOIN view_dish_nutrients_long n ON n.dish_id = d.id
            JOIN ejia_dish_food_rel dfr ON dfr.dish_id = d.id
            JOIN foods f ON f.fdc_id = dfr.food_id
            WHERE d.cook_time <= 30
            ORDER BY d.rating DESC
        """
        rows = db.query(sql)
        dishes = []
        for r in rows:
            dishes.append(
                Dish(
                    dish_id=r["id"],
                    name=r["name"],
                    nutrients={r["nutrient_code"]: float(r["nutrient_amount"])},
                    ingredients={r["ingredient"]: float(r["default_portion_g"])},
                    cook_time=r["cook_time"]
                )
            )
        return dishes

    # 4. 家庭过敏原
    @staticmethod
    def get_family_allergens(member_ids: List[int]) -> List[str]:
        ids_str = ",".join(map(str, member_ids))
        return [row["allergen_code"] for row in db.query(
            f"SELECT DISTINCT allergen_code FROM ejia_member_allergen WHERE member_id IN ({ids_str})"
        )]

    # 5. 菜品过敏原（food 级）
    @staticmethod
    def get_dish_allergens2(dish_id: int, family_allergens: List[str]) -> List[str]:
        food_ids = [row["food_id"] for row in db.query(
            "SELECT food_id FROM ejia_dish_food_rel WHERE dish_id = %s", (dish_id,)
        )]
        if not food_ids:
            return []
        ids_str = ",".join(map(str, food_ids))
        sql = f"""
            SELECT DISTINCT allergen_code
            FROM ejia_allergen_food_rel
            WHERE food_id IN ({ids_str})
        """
        dish_allergens = [row["allergen_code"] for row in db.query(sql)]
        return list(set(dish_allergens) & set(family_allergens))

    @staticmethod
    def get_member_info(member_ids: List[int]) -> List[MemberInfo]:
        """获取成员详细信息"""
        ids_str = ",".join(map(str, member_ids))
        sql = f"""
            SELECT id, age, gender, height_cm, weight_kg
            FROM ejia_user_family_member
            WHERE id IN ({ids_str})
        """
        rows = db.query(sql)
        return [
            MemberInfo(
                member_id=row["id"],
                age=float(row["age"]),
                gender=row["gender"],
                height_cm=row["height_cm"],
                weight_kg=float(row["weight_kg"])
            ) for row in rows
        ]

    @staticmethod
    def get_member_nutrient_range(member_id: int) -> Dict[str, Dict[str, float]]:
        """获取成员营养需求区间"""
        sql = """
            SELECT nutrient_code, min_need_qty, max_need_qty
            FROM ejia_member_daily_nutrient_actual
            WHERE member_id = %s
        """
        rows = db.query(sql, (member_id,))
        return {
            row["nutrient_code"]: {
                "min": float(row["min_need_qty"]),
                "max": float(row["max_need_qty"])
            } for row in rows
        }

    @staticmethod
    def get_member_specific_needs(member_id: int) -> List[str]:
        """获取成员具体饮食需求"""
        sql = """
            SELECT need_code FROM ejia_member_diet_need 
            WHERE member_id = %s
        """
        rows = db.query(sql, (member_id,))
        return [row["need_code"] for row in rows]

    @staticmethod
    def get_dishes_by_need(need_code: str, limit: int = 10) -> List[Tuple[int, float]]:
        """根据需求代码获取匹配的菜品"""
        sql = """
            SELECT dish_id, match_score 
            FROM ejia_need_dish_match 
            WHERE need_code = %s 
            ORDER BY match_score DESC 
            LIMIT %s
        """
        rows = db.query(sql, (need_code, limit))
        return [(row["dish_id"], float(row["match_score"])) for row in rows]

    @staticmethod
    def get_dishes_by_any_needs(need_codes: List[str], take: int) -> List[Dish]:
        """
        返回满足任意 need_code 的空壳 Dish 列表，字段先留空
        """
        if not need_codes:
            return []
        codes_str = ",".join(f"'{c}'" for c in need_codes)
        sql = f"""
            SELECT dish_id,
                   MAX(match_score) AS max_score,
                   GROUP_CONCAT(DISTINCT need_code) AS need_codes
            FROM   ejia_need_dish_match
            WHERE  need_code IN ({codes_str})
            GROUP  BY dish_id
            ORDER  BY max_score DESC
            LIMIT  {take}
        """
        rows = db.query(sql)
        return [
            Dish(
                dish_id=int(r["dish_id"]),
                name="",  # 先空
                nutrients={},  # 先空
                ingredients={},  # 先空
                cook_time=0,  # 先空
                matched_needs=str(r["need_codes"]).split(","),
                match_score=float(r["max_score"])
            )
            for r in rows
        ]
    @staticmethod
    def get_dish_by_id(dish_id: int) -> Optional[Dish]:
        """根据菜品ID获取完整菜品信息"""
        sql = """
              SELECT d.id, \
                     d.name, \
                     d.cook_time, \
                     d.default_portion_g,
                     n.nutrient_code, \
                     n.nutrient_amount,
                     f.description AS ingredient
              FROM ejia_dish d
                       JOIN view_dish_nutrients_long n ON n.dish_id = d.id
                       JOIN ejia_dish_food_rel dfr ON dfr.dish_id = d.id
                       JOIN foods f ON f.fdc_id = dfr.food_id
              WHERE d.id = %s \
              """
        rows = db.query(sql, (dish_id,))

        if not rows:
            return None

        # 构建营养成分字典
        nutrients = {}
        ingredients = {}

        for row in rows:
            nutrients[row["nutrient_code"]] = float(row["nutrient_amount"])
            ingredients[row["ingredient"]] = float(row["default_portion_g"])

        # 取第一条记录获取基本信息
        first_row = rows[0]
        return Dish(
            dish_id=first_row["id"],
            name=first_row["name"],
            nutrients=nutrients,
            ingredients=ingredients,
            cook_time=first_row["cook_time"]
        )

    @staticmethod
    def get_dish_pool(cook_time_limit: int = 30) -> List[Dish]:
        """获取菜品池，支持烹饪时间过滤"""
        sql = """
              SELECT d.id, \
                     d.name, \
                     d.cook_time, \
                     d.default_portion_g,
                     n.nutrient_code, \
                     n.nutrient_amount,
                     f.description AS ingredient
              FROM ejia_dish d
                       JOIN view_dish_nutrients_long n ON n.dish_id = d.id
                       JOIN ejia_dish_food_rel dfr ON dfr.dish_id = d.id
                       JOIN foods f ON f.fdc_id = dfr.food_id
              WHERE d.cook_time <= %s
              ORDER BY d.rating DESC \
              """
        rows = db.query(sql, (cook_time_limit,))

        dishes_dict = {}
        for row in rows:
            dish_id = row["id"]
            if dish_id not in dishes_dict:
                dishes_dict[dish_id] = {
                    "dish_id": dish_id,
                    "name": row["name"],
                    "cook_time": row["cook_time"],
                    "nutrients": {},
                    "ingredients": {}
                }

            dishes_dict[dish_id]["nutrients"][row["nutrient_code"]] = float(row["nutrient_amount"])
            dishes_dict[dish_id]["ingredients"][row["ingredient"]] = float(row["default_portion_g"])

        return [
            Dish(
                dish_id=data["dish_id"],
                name=data["name"],
                nutrients=data["nutrients"],
                ingredients=data["ingredients"],
                cook_time=data["cook_time"]
            )
            for data in dishes_dict.values()
        ]

    @staticmethod
    def get_dish_allergens(dish_id: int, family_allergens: List[str]) -> List[str]:
        """获取菜品的过敏原信息（只返回与家庭过敏原匹配的部分）"""
        sql = """
              SELECT DISTINCT ar.allergen_code
              FROM ejia_allergen_food_rel ar
                       JOIN ejia_dish_food_rel dfr ON dfr.food_id = ar.food_id
              WHERE dfr.dish_id = %s \
              """
        rows = db.query(sql, (dish_id,))

        dish_allergens = [row["allergen_code"] for row in rows]

        # 只返回与家庭过敏原匹配的部分
        return list(set(dish_allergens) & set(family_allergens))

