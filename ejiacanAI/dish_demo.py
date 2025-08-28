from dish_recommender import DishRecommender
from ejiacanAI.dish_data_access import EnhancedDataAccess
from dbconnect.dbconn import db
from models import Context

# 假设框架已注入 db 连接
data_access = EnhancedDataAccess(db)
rec = DishRecommender(data_access)

ctx = Context(meal_type="dinner", max_cook_time=25, surprise_level=0.3, stock=None)
top3 = rec.recommend(member_id=1, ctx=ctx, top_k=3)
for d in top3:
    print(d.dish_id, d.name, d.nutrients)