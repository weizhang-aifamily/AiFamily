# demo.py
from ejiacanAI.dish2_combo_models import MealRequest
from ejiacanAI.dish2_combo_generator import MealGeneratorV2

if __name__ == "__main__":
    req = MealRequest(
        member_ids=[1, 2, 3],   # 假设库里 1,2,3 有需求
        meal_type="all",        # 生成三餐
        refresh_key=42,         # 每次换种子即可洗牌
        cook_time_limit=30,     # 30 分钟以内
        deficit_kcal=0,          # 无热量缺口
        dish_series=None,  # 菜系ID
    )

    # meals = MealGeneratorV2.generate(req)
    meals = MealGeneratorV2.generate_per_meal(req)

    print("========  Demo 输出  ========")
    for m in meals:
        print("餐次:", m.combo_name, "总烹饪时间:", m.total_cook_time, "分钟")
        for d in m.dishes:
            print("  -", d.name,
                  f"{d.exact_portion.size}({d.exact_portion.grams}g)",
                  "营养素:", d.nutrients)
        print("  购物清单:", m.shopping_list)
        print()