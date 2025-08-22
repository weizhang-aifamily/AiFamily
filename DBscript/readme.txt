下面用“页面功能 ➜ 对应数据 ➜ 用到的表”三张图的方式，把「peican.html / peican.js」里出现的所有功能点，与刚才给出的 MySQL 表结构一一映射。读完就能一眼看出：每块页面 UI 背后到底 CRUD 哪几张表、字段叫什么、为什么要这么设计。

--------------------------------------------------
1️⃣ 家庭成员区（顶部 smart-guard-bar / memberTags）
--------------------------------------------------
页面需求
- 展示头像、姓名、当前营养需求标签（低脂/补铁…）
- 点击头像可切换“参与/不参与”本次配餐
- 点击姓名跳转个人营养报告页

对应数据
- 成员基本信息（id、name、avatar）
- 成员当前被激活的营养需求（可多选）
- 过敏源图标集合

用到的表
ejia_family_member        —— 主键 id、name、avatar
ejia_member_need          —— 多对多关联（member_id ↔ need_id）
ejia_member_allergen      —— 多对多关联（member_id ↔ allergen_id）
ejia_allergen             —— 字典表（icon、name）

关系示意
memberTags 渲染时：
SELECT m.id, m.name, m.avatar,
       GROUP_CONCAT(n.code) AS needs,
       GROUP_CONCAT(a.icon) AS allergenIcons
FROM ejia_family_member m
LEFT JOIN ejia_member_need  mn ON m.id = mn.member_id
LEFT JOIN ejia_diet_need    n  ON n.id = mn.need_id
LEFT JOIN ejia_member_allergen ma ON m.id = ma.member_id
LEFT JOIN ejia_allergen     a  ON a.id = ma.allergen_id
GROUP BY m.id;

--------------------------------------------------
2️⃣ 方案与过滤区（solutionTags + 过敏源/忌口/预算/季节 过滤）
--------------------------------------------------
页面需求
- 根据“已选成员”实时合并出需要的营养方案（如同时出现 lowSalt+highCalcium）
- 可手动开关某个方案
- 提供排除过敏源、排除忌口、仅当季、低/中/高预算多组开关

对应数据
- 字典表：所有方案（lowSalt…）、所有过敏源（peanuts…）
- 成员-方案、成员-过敏源 两张关联表
- 过滤结果最终落在一个 WHERE 条件里：
  WHERE i.id NOT IN (过敏源食材) AND i.seasonal = 1 AND price BETWEEN …

用到的表
ejia_diet_need        —— 方案字典
ejia_member_need      —— 成员→方案
ejia_allergen         —— 过敏源字典
ejia_member_allergen  —— 成员→过敏源
ejia_ingredient       —— 食材表里的 seasonal、price_100g 字段

--------------------------------------------------
3️⃣ 食材推荐区（ingredientList 卡片）
--------------------------------------------------
页面需求
- 每个卡片：emoji、名称、克数、tag、描述、几人份、预计花费
- 支持“同类替换”弹窗，点选后实时替换当前卡片

对应数据
- 食材主档（ejia_ingredient）
- 横向可替换关系（ejia_ingredient_alt）
- 价格计算：price_100g × grams / 100

用到的表
ejia_ingredient
ejia_ingredient_alt   —— 用于弹窗里列出同类备选
（替换后前端把卡片 DOM 更新即可，也可以写一条替换日志到 ejia_member_diet_history）

--------------------------------------------------
4️⃣ 菜品/套餐区（dishList + comboSlides）
--------------------------------------------------
页面需求
- 单菜卡片：emoji、名称、评分
- 套餐幻灯片：3 个套餐（晨曦钙能宴、轻盈铁骑宴、晚安平衡宴），每套 3 道菜
- 每道菜可勾选/取消，右侧浮层实时显示已选数量、预估总价

对应数据
- 单菜：ejia_dish + 关联的食材（ejia_dish_ingredient）
- 套餐：ejia_combo + 套餐明细（ejia_combo_item）
- 历史记录：ejia_member_diet_history（存“今天吃了什么”）

用到的表
ejia_dish
ejia_combo
ejia_combo_item
ejia_dish_ingredient
ejia_member_diet_history

--------------------------------------------------
5️⃣ 尝鲜 & 近期吃过（tasteRowList / historyTrack）
--------------------------------------------------
页面需求
- 随机/按频次展示 3 道菜
- 点击“＋”可一键加入已选列表

对应数据
- 与菜品区共用 ejia_dish 表
- historyDishes 的数量来自 ejia_member_diet_history 的 COUNT(*)

SQL 示例（近期吃过）
SELECT d.*, COUNT(*) AS count
FROM ejia_member_diet_history h
JOIN ejia_dish d ON d.id = h.dish_id
GROUP BY d.id
ORDER BY count DESC
LIMIT 6;

--------------------------------------------------
6️⃣ 今日营养仪表盘（nutritionDash）
--------------------------------------------------
页面需求
- 能量、蛋白、钙、铁、钠、脂肪 6 条进度条
- 点击“重新计算”按钮实时刷新

对应数据
- 当日已选菜品 → 拆成食材 → 汇总营养素
- 目标值写死在前端常量，也可存一张 ejia_nutrient_target 表（按年龄段/性别）

用到的表
ejia_dish_ingredient  （知道每道菜含多少克食材）
ejia_ingredient        （知道每 100g 含多少钙、铁等）
计算逻辑（伪）
SELECT SUM(i.calcium * di.amount_grams / 100) AS today_calcium
FROM ejia_member_diet_history h
JOIN ejia_dish_ingredient di ON di.dish_id = h.dish_id
JOIN ejia_ingredient       i  ON i.id = di.ingredient_id
WHERE h.eat_date = CURDATE() AND h.member_id = ?;

--------------------------------------------------
7️⃣ 成就系统 & 预算
--------------------------------------------------
页面需求
- 使用 5 次后解锁「智能厨神」
- 经济/标准/豪华三档预算

对应数据
- 成就计数 → 在 ejia_member 表加一个 usage_count 字段，或单独建 ejia_member_achievement
- 预算 → 前端仅做价格过滤（见 ingredient.price_100g），无需持久化

--------------------------------------------------
小结（一句话背下来）
“页面上的每一个头像、标签、卡片、按钮，背后都是一张字典表 + 一张事实表 + 一张关联表；过滤就是把多选条件翻译成 WHERE IN / WHERE NOT IN，营养计算就是把菜品-食材-营养量三张表 JOIN 后 SUM。”