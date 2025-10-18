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