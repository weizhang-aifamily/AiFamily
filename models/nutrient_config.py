# nutrient_config.py
NUTRIENT_CODE_MAPPING = {
    'calories': 1,           # 热量 (kcal)
    'protein': 2,            # 蛋白质 (g)
    'fat': 3,                # 脂肪 (g)
    'carbs': 4,              # 碳水化合物 (g)
    'calcium': 5,            # 钙 (mg)
    'iron': 6,               # 铁 (mg)
    'vitamin_c': 7,          # 维生素C (mg)
    'vitamin_d': 8,          # 维生素D (μg)
    'zinc': 9,               # 锌 (mg)
    'magnesium': 10,         # 镁 (mg)
    'vitamin_a': 11,         # 维生素A (μg)
    'vitamin_b12': 12,       # 维生素B12 (μg)
    'folate': 13,            # 叶酸 (μg)
    'sodium': 14,            # 钠 (mg)
    'potassium': 15,         # 钾 (mg)
    'phosphorus': 16,        # 磷 (mg)
    'selenium': 17,          # 硒 (μg)
    'copper': 18,            # 铜 (mg)
    'manganese': 19,         # 锰 (mg)
    'vitamin_e': 20,         # 维生素E (mg)
    'vitamin_k': 21,         # 维生素K (μg)
    'thiamin': 22,           # 硫胺素 (mg)
    'riboflavin': 23,        # 核黄素 (mg)
    'niacin': 24,            # 烟酸 (mg)
    'vitamin_b6': 25,        # 维生素B6 (mg)
    'biotin': 26,            # 生物素 (μg)
    'pantothenic_acid': 27   # 泛酸 (mg)
}

# 反向映射，用于从代码获取名称
NUTRIENT_NAME_MAPPING = {v: k for k, v in NUTRIENT_CODE_MAPPING.items()}

# 营养素单位映射
NUTRIENT_UNITS = {
    'calories': 'kcal',
    'protein': 'g',
    'fat': 'g',
    'carbs': 'g',
    'calcium': 'mg',
    'iron': 'mg',
    'vitamin_c': 'mg',
    'vitamin_d': 'μg',
    'zinc': 'mg',
    'magnesium': 'mg',
    'vitamin_a': 'μg',
    'vitamin_b12': 'μg',
    'folate': 'μg',
    'sodium': 'mg',
    'potassium': 'mg',
    'phosphorus': 'mg',
    'selenium': 'μg',
    'copper': 'mg',
    'manganese': 'mg',
    'vitamin_e': 'mg',
    'vitamin_k': 'μg',
    'thiamin': 'mg',
    'riboflavin': 'mg',
    'niacin': 'mg',
    'vitamin_b6': 'mg',
    'biotin': 'μg',
    'pantothenic_acid': 'mg'
}
MEAL_RATIO = {"breakfast": 0.30, "lunch": 0.40, "dinner": 0.30}
# 2. 定义营养优先级
nutrient_priority = {
    'protein': 10,  # 最高优先级
    'calories': 9,  # 高优先级
    'fat': 8,  # 高优先级
    'carbohydrate': 7,  # 中优先级
    'dietary_fiber': 6,  # 中优先级
    # 其他营养素默认优先级为1
}
structure_def = {
    'main_dish': [],
    'side_dish': [],
    'staple': [],
    'soup': [],
    'baby_food': []
}

NUTRIENT_MAPPING = {
    # 宏量
    'protein': 'Protein',
    'fat': 'Fat',
    'CHO': 'Carbohydrate',
    'dietaryFiber': 'DietaryFiber',
    'ash': 'Ash',
    # 能量
    'energyKCal': 'EnergyKCal',
    'energyKJ': 'EnergyKJ',
    # 矿物质
    'Ca': 'Calcium', 'P': 'Phosphorus', 'K': 'Potassium',
    'Na': 'Sodium', 'Mg': 'Magnesium', 'Fe': 'Iron',
    'Zn': 'Zinc', 'Se': 'Selenium', 'Cu': 'Copper',
    'Mn': 'Manganese',
    # 维生素
    'vitaminA': 'VitaminA',
    'carotene': 'Carotene',
    'retinol': 'Retinol',
    'thiamin': 'Thiamin',
    'riboflavin': 'Riboflavin',
    'niacin': 'Niacin',
    'vitaminC': 'VitaminC',
    'vitaminETotal': 'VitaminETotal',
    'vitaminE1': 'VitaminE1',
    'vitaminE2': 'VitaminE2',
    'vitaminE3': 'VitaminE3',
    # 其他
    'cholesterol': 'Cholesterol',
    'water': 'Water',
    'edible': 'EdibleRatio'
}
# 新增食物类别映射配置（基于你提供的实际分类）
FOOD_CATEGORY_MAPPING = {
    # 谷薯类
    '谷类及其制品': 'cereal',
    '薯类淀粉及其制品': 'cereal',

    # 肉蛋类
    '畜肉类及其制品': 'protein',
    '禽肉类及其制品': 'protein',
    '蛋类及其制品': 'protein',
    '鱼虾蟹贝类': 'protein',

    # 蔬果类
    '蔬菜类及其制品': 'vege_fruit',
    '水果类及其制品': 'vege_fruit',
    '菌藻类': 'vege_fruit',

    # 奶豆类
    '乳类及其制品': 'dairy_bean',
    '干豆类及其制品': 'dairy_bean',
    '坚果种子类': 'dairy_bean',

    # 油脂类
    '动物油脂类': 'oil',
    '植物油': 'oil',
    '油脂类': 'oil',

    # 其他
    '调味品': 'other',
    '饮料': 'other',
    '婴幼儿食品': 'other',
    '其他类': 'other'
}

# 每餐食物类别目标配置（新增）
MEAL_FOOD_CATEGORY_TARGETS = {
    'breakfast': {
        'cereal': {'min': 1, 'max': 2},
        'protein': {'min': 1, 'max': 1},
        'dairy_bean': {'min': 0, 'max': 1},
        'vege_fruit': {'min': 0, 'max': 1}
    },
    'lunch': {
        'cereal': {'min': 1, 'max': 1},
        'protein': {'min': 1, 'max': 2},
        'vege_fruit': {'min': 2, 'max': 3},
        'dairy_bean': {'min': 0, 'max': 1}
    },
    'dinner': {
        'cereal': {'min': 1, 'max': 1},
        'protein': {'min': 1, 'max': 1},
        'vege_fruit': {'min': 2, 'max': 2},
        'dairy_bean': {'min': 0, 'max': 1}
    }
}
all_categories = ['cereal', 'protein', 'vege_fruit', 'dairy_bean', 'oil', 'other']