from dbconnect.dbconn import db
from ejiacanAI.data_access import DataAccess
from ejiacanAI.engine import ILPRecommender

dao = DataAccess(db)
engine = ILPRecommender()

menu = engine.recommend(
    dishes=dao.fetch_safe_dishes([1, 2, 3]),
    need=dao.fetch_family_need([1, 2, 3]),
    top_k=5
)

print(menu)