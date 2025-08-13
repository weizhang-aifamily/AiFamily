from flask import Flask, render_template, request
import pymysql

app = Flask(__name__)

# 数据库工具函数（可复用）
def get_db_data(sql, params=None):
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='你的密码',
        database='ejiacan'
    )
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute(sql, params or ())
    data = cur.fetchall()
    conn.close()
    return data

# 首页路由
@app.route('/')
def index():
    users = get_db_data("SELECT * FROM testdb")
    return render_template('index.html', users=users)

# 其他页面路由示例
@app.route('/page2')
def page2():
    data = get_db_data("SELECT user_name FROM testdb WHERE user_id > 1")
    return render_template('page2.html', items=data)

# 处理表单提交示例
@app.route('/search', methods=['POST'])
def search():
    keyword = request.form.get('keyword')
    results = get_db_data("SELECT * FROM testdb WHERE user_name LIKE %s",
                         (f"%{keyword}%",))
    return render_template('search_results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)