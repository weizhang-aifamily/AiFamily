from dbconnect.dbconn import db
import openai, json

def get_diet_needs(goal_codes, checkup_codes):
    prompt = f"""
你是一个注册营养师。
用户目标：{json.dumps(goal_codes)}
体检异常：{json.dumps(checkup_codes)}
请返回一个 JSON 数组，每个元素包含：
{ "code": "唯一英文小写标识", "name": "中文名称", "icon": "单个emoji", "desc": "50字以内解释" }
"""
    resp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        temperature=0
    )
    arr = json.loads(resp.choices[0].message.content)
    # 直接写库
    for it in arr:
        db.execute(
            "INSERT IGNORE INTO ejia_diet_need_tbl(code,name,icon,desc_text) VALUES(%s,%s,%s,%s)",
            (it['code'], it['name'], it['icon'], it['desc'])
        )
    return [it['code'] for it in arr]
