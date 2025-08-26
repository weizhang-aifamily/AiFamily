# update_recommendation_model.py
import time
import logging
from dbconnect.dbconn import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_need_dish_matches():
    """更新需求-菜品匹配数据（兼容纵表结构）"""
    try:
        logger.info("开始更新需求-菜品匹配数据...")

        # 调用存储过程
        result = db.query("CALL sp_init_need_dish_matches()")
        logger.info("存储过程执行结果: %s", result)

        # 验证更新结果
        count_result = db.query("SELECT COUNT(*) as count FROM ejia_need_dish_match WHERE match_score > 0")
        logger.info("有效匹配记录数: %d", count_result[0]['count'])

        logger.info("需求-菜品匹配数据更新完成")

    except Exception as e:
        logger.error("更新失败: %s", str(e))
        # 降级处理：逐个更新
        update_individual_matches()


def update_individual_matches():
    """逐个更新匹配规则（降级方案）"""
    try:
        logger.info("开始逐个更新匹配规则...")

        # 获取所有规则
        rules = db.query("""
                         SELECT need_code, nutrient_name_cn, comparison_operator, threshold_value
                         FROM ejia_enum_diet_need_nutrient_rule
                         """)

        for rule in rules:
            try:
                db.execute("""
                    CALL sp_update_need_dish_match(%s, %s, %s, %s)
                """, (rule['need_code'], rule['nutrient_name_cn'],
                      rule['comparison_operator'], rule['threshold_value']))
                logger.info("更新规则: %s - %s", rule['need_code'], rule['nutrient_name_cn'])

            except Exception as e:
                logger.warning("更新规则失败 %s-%s: %s",
                               rule['need_code'], rule['nutrient_name_cn'], str(e))

        logger.info("逐个更新完成")

    except Exception as e:
        logger.error("逐个更新也失败: %s", str(e))


if __name__ == "__main__":
    update_need_dish_matches()