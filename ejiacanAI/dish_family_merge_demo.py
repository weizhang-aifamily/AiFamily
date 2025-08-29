# family_merge_demo.py
from dish_smart_models import FamilyMember
from dish_family_merge_recommender import FamilyMergeRecommender

def demo():
    # 模拟 3 口之家
    members = "1,2,3"
    merged = FamilyMergeRecommender.merge(members, meal_type="lunch", max_dishes=4)

    print("家庭合并菜单：", [d.name for d in merged])
    for d in merged:
        print(f"  {d.name}  钙:{d.nutrients.get('钙', 0):.0f}mg  "
              f"标签:{d.allergens} rating:{d.popularity}")

if __name__ == "__main__":
    demo()