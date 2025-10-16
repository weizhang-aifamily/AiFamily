from typing import List, Dict


class MealStructureGenerator:
    def __init__(self):
        # 定义年龄组映射
        self.age_group_mapping = {
            'toddler': (1, 3),  # 幼儿
            'child': (4, 12),  # 儿童
            'teen': (13, 17),  # 青少年
            'young': (18, 35),  # 青年
            'middle': (36, 60),  # 中年
            'senior': (61, 120)  # 老年
        }

        # 基准菜品配置（主食数、主菜数、配菜数、汤数）
        self.base_config = {
            'breakfast': {'staple': 1, 'main_dish': 1, 'side_dish': 0, 'soup': 0, 'baby_food': 0},
            'lunch': {'staple': 1, 'main_dish': 1, 'side_dish': 1, 'soup': 1, 'baby_food': 0},
            'dinner': {'staple': 1, 'main_dish': 1, 'side_dish': 1, 'soup': 1, 'baby_food': 0},
            'banquet': {'staple': 1, 'main_dish': 2, 'side_dish': 2, 'soup': 1, 'baby_food': 0}
        }

        # 省份饮食偏好配置（调整系数）
        self.province_preferences = {
            # 北方省份：面食为主，汤较少
            'BJ': {'staple': 1.2, 'soup': 0.8},  # 北京
            'SD': {'staple': 1.3, 'soup': 0.7},  # 山东
            'HE': {'staple': 1.2, 'soup': 0.8},  # 河北
            # 南方省份：米饭为主，汤较多
            'GD': {'staple': 1.0, 'soup': 1.5},  # 广东
            'FJ': {'staple': 1.0, 'soup': 1.4},  # 福建
            'ZJ': {'staple': 1.0, 'soup': 1.3},  # 浙江
            # 西南省份：辣味主菜较多
            'SC': {'main_dish': 1.3, 'side_dish': 1.2},  # 四川
            'CQ': {'main_dish': 1.4, 'side_dish': 1.1},  # 重庆
            'HN': {'main_dish': 1.2, 'side_dish': 1.1},  # 湖南
            # 默认配置
            'default': {'staple': 1.0, 'main_dish': 1.0, 'side_dish': 1.0, 'soup': 1.0}
        }

    def calculate_meal_config(self, members: List[Dict], meal_type: str, province_code: str = 'default') -> Dict:
        """
        计算菜品配置的主函数

        Args:
            members: 成员列表，每个成员包含id, age, ageGroup, gender
            meal_type: 餐次类型 'breakfast', 'lunch', 'dinner', 'banquet'
            province_code: 省份代码，如 'GD', 'BJ', 'SC'等

        Returns:
            Dict: 包含主食数、主菜数、配菜数、汤数、幼儿辅食数的配置字典
        """
        if not members:
            return self._empty_config()

        # 获取基准配置
        config = self.base_config[meal_type].copy()

        # 统计特殊年龄组
        toddler_count = sum(1 for m in members if m['ageGroup'] == 'toddler')
        child_count = sum(1 for m in members if m['ageGroup'] == 'child')
        adult_count = self._count_adult_members(members)
        total_count = len(members)

        # 宴请场景的特殊逻辑
        if meal_type == 'banquet':
            config = self._adjust_banquet_config(config, adult_count, total_count)

        # 日常餐次的人数调整
        elif meal_type in ['lunch', 'dinner']:
            config = self._adjust_regular_meal_config(config, total_count)

        # 应用省份偏好
        config = self._apply_province_preferences(config, province_code)

        # 添加幼儿辅食
        if toddler_count > 0:
            config['baby_food'] += toddler_count

        # 儿童特殊处理：宴请时可能增加主菜多样性
        if meal_type == 'banquet' and child_count > 0:
            config['main_dish'] = max(config['main_dish'], 2)

        return config

    def _empty_config(self) -> Dict:
        """返回空的配置字典"""
        return {'staple': 0, 'main_dish': 0, 'side_dish': 0, 'soup': 0, 'baby_food': 0}

    def _adjust_banquet_config(self, config: Dict, adult_count: int, total_count: int) -> Dict:
        """调整宴请场景配置"""
        # 根据人数调整菜品数量
        if total_count >= 6:
            config['main_dish'] = min(adult_count // 2 + 1, 5)  # 最多5个主菜
            config['side_dish'] = min(adult_count // 2 + 1, 4)  # 最多4个配菜
            config['soup'] = 2  # 宴请大桌通常有2个汤
        elif total_count >= 4:
            config['main_dish'] = 3
            config['side_dish'] = 2
        return config

    def _adjust_regular_meal_config(self, config: Dict, total_count: int) -> Dict:
        """调整日常餐次配置"""
        # 根据人数适当调整
        if total_count >= 4:
            config['main_dish'] += 1
            config['side_dish'] += 1
        elif total_count <= 2:
            # 人少时减少配菜
            config['side_dish'] = max(0, config['side_dish'] - 1)
        return config

    def _apply_province_preferences(self, config: Dict, province_code: str) -> Dict:
        """应用省份饮食偏好"""
        preferences = self.province_preferences.get(province_code,
                                                    self.province_preferences['default'])

        for key, value in config.items():
            if key in preferences and key != 'baby_food':  # 幼儿辅食不受省份影响
                # 对数值型配置应用调整系数，并四舍五入
                config[key] = max(1, round(value * preferences[key])) if value > 0 else 0

        return config

    def _count_adult_members(self, members: List[Dict]) -> int:
        """统计成人数量（teen及以上视为成人）"""
        adult_groups = {'teen', 'young', 'middle', 'senior'}
        return sum(1 for member in members if member['ageGroup'] in adult_groups)


# 测试用例
def test_algorithm():
    planner = MealStructureGenerator()

    # 成员定义
    family_members = [
        {'id': 1, 'age': 35, 'ageGroup': 'middle', 'gender': 'M'},
        {'id': 2, 'age': 36, 'ageGroup': 'middle', 'gender': 'F'},
        {'id': 3, 'age': 10, 'ageGroup': 'child', 'gender': 'M'},
        {'id': 4, 'age': 3, 'ageGroup': 'toddler', 'gender': 'F'}
    ]

    guests_members = [
        {'id': 1, 'age': 35, 'ageGroup': 'middle', 'gender': 'M'},
        {'id': 2, 'age': 36, 'ageGroup': 'middle', 'gender': 'F'},
        {'id': 3, 'age': 10, 'ageGroup': 'child', 'gender': 'M'},
        {'id': 4, 'age': 3, 'ageGroup': 'toddler', 'gender': 'F'},
        {'id': 5, 'age': 65, 'ageGroup': 'senior', 'gender': 'M'},
        {'id': 6, 'age': 40, 'ageGroup': 'middle', 'gender': 'F'}
    ]

    couple_members = [
        {'id': 1, 'age': 30, 'ageGroup': 'young', 'gender': 'M'},
        {'id': 2, 'age': 28, 'ageGroup': 'young', 'gender': 'F'}
    ]

    print("测试用例1 - 广东家庭晚餐:")
    print(planner.calculate_meal_config(family_members, 'dinner', 'GD'))

    print("\n测试用例2 - 四川宴请场景:")
    print(planner.calculate_meal_config(guests_members, 'banquet', 'SC'))

    print("\n测试用例3 - 北京早餐:")
    print(planner.calculate_meal_config(couple_members, 'breakfast', 'BJ'))

    print("\n测试用例4 - 默认省份午餐:")
    print(planner.calculate_meal_config(family_members, 'lunch', 'default'))


if __name__ == "__main__":
    test_algorithm()