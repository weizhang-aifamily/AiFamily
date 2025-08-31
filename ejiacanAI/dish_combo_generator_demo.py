# dish_combo_generator_demo.py
from ejiacanAI.dish_combo_generator import DishComboGenerator
from ejiacanAI.dish_combo_models import ComboConfig


def demo_all_features():
    """演示所有功能的完整示例"""

    print("=" * 60)
    print("家庭套餐生成器 - 完整功能演示")
    print("=" * 60)

    # 示例家庭成员：成人*2 + 儿童*1
    member_ids = [1, 2, 3]  # 假设ID 1,2为成人，3为儿童

    # 演示1: 生成全天套餐（早中晚三个）
    print("\n1. 生成全天套餐 (meal_type='all')")
    print("-" * 40)
    all_day_meals = DishComboGenerator.generate_family_combo(
        member_ids=member_ids,
        meal_type="all",
        filter_allergens=True
    )

    for meal in all_day_meals:
        print(f"\n📋 {meal.combo_name} ({meal.meal_type})")
        print(f"   ⏰ 烹饪时间: {meal.total_cook_time}分钟")
        print(f"   🍽️ 菜品数量: {len(meal.dishes)}道")
        print(f"   🏷️ 需求标签: {meal.need_codes}")

        # 显示份量分配
        if meal.portion_plan:
            print("   📊 份量分配:")
            for category, dishes in meal.portion_plan.items():
                print(f"     {category}: {dishes}")

        # 显示菜品详情
        print("   🍲 菜品详情:")
        for dish in meal.dishes:
            allergen_info = f" [⚠️过敏: {dish.allergens}]" if dish.allergens else ""
            needs_info = f" [✅需求: {dish.matched_needs}]" if dish.matched_needs else ""
            print(f"     - {dish.name} ({dish.portion_size}份){needs_info}{allergen_info}")
            print(
                f"       ⏱️{dish.cook_time}分钟 | 🥗主料: {list(dish.ingredients.keys())[0] if dish.ingredients else '未知'}")

    # 演示2: 只生成午餐套餐（自定义配置）
    print("\n\n2. 生成自定义午餐套餐")
    print("-" * 40)
    lunch_meal = DishComboGenerator.generate_family_combo(
        member_ids=member_ids,
        meal_type="lunch",
        max_per_meal=4,  # 指定4道菜
        cook_time_config={"lunch": 35},  # 午餐烹饪时间限制35分钟
        portion_config={"default": "L"},  # 全部大份
        filter_allergens=False  # 只标记，不过滤过敏原
    )

    print(f"\n📋 {lunch_meal.combo_name}")
    print(f"   ⏰ 总烹饪时间: {lunch_meal.total_cook_time}分钟")
    print(f"   🍽️ 菜品数量: {len(lunch_meal.dishes)}道")

    # 显示过敏原汇总（因为不过滤模式）
    all_allergens = set()
    for dish in lunch_meal.dishes:
        all_allergens.update(dish.allergens)
    if all_allergens:
        print(f"   ⚠️ 套餐含过敏原: {list(all_allergens)}")

    print("   🍲 菜品详情:")
    for dish in lunch_meal.dishes:
        allergen_info = f" [⚠️过敏: {dish.allergens}]" if dish.allergens else ""
        needs_info = f" [✅需求: {dish.matched_needs}]" if dish.matched_needs else ""
        print(f"     - {dish.name} ({dish.portion_size}份){needs_info}{allergen_info}")

    # 演示3: 生成早餐套餐（快速烹饪）
    print("\n\n3. 生成快速早餐套餐")
    print("-" * 40)
    breakfast_meal = DishComboGenerator.generate_family_combo(
        member_ids=member_ids,
        meal_type="breakfast",
        cook_time_config={"breakfast": 10},  # 早餐最多10分钟
        filter_allergens=True
    )

    print(f"\n📋 {breakfast_meal.combo_name}")
    print(f"   ⏰ 超快速: {breakfast_meal.total_cook_time}分钟总时长")
    print(f"   🍽️ 菜品数量: {len(breakfast_meal.dishes)}道")

    for dish in breakfast_meal.dishes:
        print(f"     - {dish.name} ({dish.portion_size}份) ⏱️{dish.cook_time}分钟")

    # 演示4: 有幼儿的特殊情况
    print("\n\n4. 有幼儿家庭的特殊处理")
    print("-" * 40)
    # 假设ID 4是幼儿（<3岁）
    family_with_toddler = [1, 2, 4]

    toddler_meals = DishComboGenerator.generate_family_combo(
        member_ids=family_with_toddler,
        meal_type="lunch",
        filter_allergens=True
    )

    print(f"\n📋 {toddler_meals.combo_name} (含幼儿)")
    print("   📊 特殊份量分配:")
    for category, dishes in toddler_meals.portion_plan.items():
        print(f"     {category}: {dishes}")

    # 演示5: 营养需求匹配展示
    print("\n\n5. 需求匹配详情展示")
    print("-" * 40)
    detailed_meal = DishComboGenerator.generate_family_combo(
        member_ids=member_ids,
        meal_type="dinner",
        filter_allergens=True
    )

    print(f"\n📋 {detailed_meal.combo_name}")
    print("   👥 成员需求匹配:")

    # 收集每个成员被哪些菜品满足的需求
    member_needs_map = {}
    for dish in detailed_meal.dishes:
        for member_id, needs in getattr(dish, '_member_matches', {}).items():
            if member_id not in member_needs_map:
                member_needs_map[member_id] = set()
            member_needs_map[member_id].update(needs)

    for member_id, needs in member_needs_map.items():
        print(f"     成员{member_id}: {list(needs)}")

    print("   🍲 各菜品需求贡献:")
    for dish in detailed_meal.dishes:
        member_matches = getattr(dish, '_member_matches', {})
        if member_matches:
            matches_str = ", ".join([f"成员{mid}:{needs}" for mid, needs in member_matches.items()])
            print(f"     - {dish.name}: {matches_str}")


def demo_config_customization():
    """演示配置自定义"""
    print("\n\n" + "=" * 60)
    print("配置自定义演示")
    print("=" * 60)

    # 自定义配置
    custom_config = ComboConfig(
        base_dish_count=2,
        dish_per_adult=2,
        dish_per_child=1,
        cook_time_breakfast=8,  # 早餐更快速
        cook_time_lunch=25,  # 午餐稍快
        nutrient_ratio_breakfast=0.25,  # 早餐25%
        nutrient_ratio_lunch=0.45,  # 午餐45%
        nutrient_ratio_dinner=0.30  # 晚餐30%
    )

    # 替换默认配置
    DishComboGenerator.CONFIG = custom_config

    print("使用自定义配置生成套餐...")
    meals = DishComboGenerator.generate_family_combo(
        member_ids=[1, 2, 3],
        meal_type="all"
    )

    for meal in meals:
        print(f"{meal.combo_name}: {len(meal.dishes)}道菜, {meal.total_cook_time}分钟")


if __name__ == "__main__":
    # 运行完整演示
    demo_all_features()

    # 运行配置自定义演示
    demo_config_customization()

    print("\n" + "=" * 60)
    print("演示完成！所有功能均已展示")
    print("=" * 60)