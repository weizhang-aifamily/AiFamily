from dbconnect.dbconn import db
from ejiacanAI.data_access import DataAccess
from ejiacanAI.engine import ILPRecommender

dao = DataAccess(db)
engine = ILPRecommender()
member_ids = "1,2,3"
member_ids_list = list(map(int, member_ids.split(',')))
needs_info = dao.get_member_needs(member_ids_list)
all_need_codes = needs_info['all_need_codes']
need = dao.fetch_family_need_new(member_ids_list)
dishes_with_tags = dao.fetch_safe_dishes_with_tags(member_ids_list, all_need_codes)

# 在 family_bp.py 的 get_combos 方法中添加
print(f"成员ID: {member_ids_list}")
print(f"家庭需求: {need}")
print(f"可用菜品数量: {len(dishes_with_tags)}")

# 打印前5个菜品的详细信息
for i, dish in enumerate(dishes_with_tags[:5]):
    print(f"菜品 {i+1}: {dish.name}")
    print(f"  营养值 - 钙: {dish.calcium}, 铁: {dish.iron}, 蛋白质: {dish.protein}, 脂肪: {dish.fat}")
    print(f"  标签: {dish.tags}")

# 检查是否有营养成分全为0的情况
zero_nutrient_dishes = [d for d in dishes_with_tags if d.calcium == 0 and d.iron == 0]
print(f"营养成分全为0的菜品数量: {len(zero_nutrient_dishes)}")

menu = engine.recommend(
    dishes=dao.fetch_safe_dishes_with_tags([1, 2, 3],all_need_codes),
    need=dao.fetch_family_need_new([1, 2, 3]),
    top_k=5
)

print(dishes_with_tags)
print(menu)