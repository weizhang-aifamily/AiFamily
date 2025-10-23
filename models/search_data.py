from typing import Dict, Any, Optional, List
from dbconnect.dbconn import db
from ejiacanAI.dish2_combo_models import DishFoodNutrient, MealRequest


class SearchData:

    @staticmethod
    def search_dishes_by_keyword(req: MealRequest, limit: int = 200) -> List[DishFoodNutrient]:
        try:
            keyword: str = req.keyword
            if not keyword:
                return []

            # 方案1：使用EXISTS替代IN
            sql = """
                SELECT v.*
                FROM v3_dish_food_complete_view v
                WHERE EXISTS (
                    SELECT 1
                    FROM ejia_dish d
                    LEFT JOIN ejia_dish_food_rel dfr ON d.id = dfr.dish_id
                    LEFT JOIN food_nutrition fn ON dfr.food_id = fn.foodCode
                    LEFT JOIN ejia_dish_tag_rel dtr ON d.id = dtr.dish_id
                    LEFT JOIN ejia_dish_tag_tbl dtt ON dtr.tag_id = dtt.id
                    WHERE d.status = 1
                      AND d.id = v.dish_id
                      AND (d.name LIKE %s 
                           OR fn.foodName LIKE %s 
                           OR dtt.tag_name LIKE %s
                           OR dtt.tag_code LIKE %s)
                )
                ORDER BY v.dish_id, v.food_id
                LIMIT %s
            """

            search_pattern = f"%{keyword}%"
            params = (search_pattern, search_pattern, search_pattern, search_pattern, limit)

            rows = db.query(sql, params)
            return [DishFoodNutrient(**r) for r in rows]

        except Exception as e:
            print(f"search_dishes_by_keyword错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return []