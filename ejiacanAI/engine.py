import pulp
from typing import List, Dict
from ejiacanAI.models import Dish, FamilyNeed


class ILPRecommender:
    def __init__(self):
        # 直接使用 PULP_CBC_CMD，这是最稳定的选项
        self.solver = pulp.PULP_CBC_CMD(msg=False)

    # ---------- 统一入口 ----------
    @staticmethod
    def recommend(dishes: List[Dish],
                  member_id: int,
                  k: int = 10,
                  algo: int = 1) -> List[Dish]:
        if algo not in {1, 2, 3}:
            raise ValueError("algo must be 1,2,3")

        # 全局分数缓存
        scores = Recommender._fetch_scores(member_id)

        # 过滤掉最近 7 天已吃的
        recent = set(Recommender._recent7(member_id))
        dishes = [d for d in dishes if d.id not in recent]

        if algo == 1:
            return Recommender._algo_mmr(dishes, scores, k)
        if algo == 2:
            return Recommender._algo_cold_start(dishes, scores, k)
        if algo == 3:
            return Recommender._algo_bandit(dishes, member_id, k)


    # ---------- 三种算法 ----------
    @staticmethod
    def _algo_mmr(dishes: List[Dish], scores: Dict[int, float], k: int) -> List[Dish]:
        """MMR + 随机扰动"""
        # 这里用极简版：先把菜按分排序，加微小扰动后截断
        eps = 1e-4
        dishes = sorted(dishes,
                        key=lambda d: scores.get(d.id, 0) + random.uniform(-eps, eps),
                        reverse=True)
        return dishes[:k]

    @staticmethod
    def _algo_cold_start(dishes: List[Dish], scores: Dict[int, float], k: int) -> List[Dish]:
        """ε-Greedy 探索/利用"""
        eps = 0.1
        chosen, pool = [], list(dishes)
        for _ in range(min(k, len(pool))):
            if random.random() < eps:
                d = random.choice(pool)
            else:
                d = max(pool, key=lambda d: scores.get(d.id, 0))
            chosen.append(d)
            pool.remove(d)
        return chosen

    @staticmethod
    def _algo_bandit(dishes: List[Dish], member_id: int, k: int) -> List[Dish]:
        """Thompson Sampling"""
        # 从数据库读 alpha, beta
        sql = "SELECT dish_id, alpha, beta FROM bandit_stats WHERE member_id=%s"
        conn = pymysql.connect(**Recommender.DB_CONFIG)
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (member_id,))
                arms = {row[0]: (row[1], row[2]) for row in cur.fetchall()}
        finally:
            conn.close()

        # 缺省的 Beta(1,1)
        def beta(d):
            a, b = arms.get(d.id, (1, 1))
            return random.betavariate(a, b)

        chosen, pool = [], list(dishes)
        for _ in range(min(k, len(pool))):
            d = max(pool, key=beta)
            chosen.append(d)
            pool.remove(d)
        return chosen