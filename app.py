from flask import Flask, render_template, request, jsonify
from dbconnect.dbconn import db
from routes.member_routes import member_bp

app = Flask(__name__)

# 注册蓝图
app.register_blueprint(member_bp)

# 保留原有的基本路由
@app.route('/')
def index():
    users = db.query("SELECT * FROM testdb")
    return render_template('index.html', users=users)

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form.get('keyword')
    results = db.query(
        "SELECT * FROM testdb WHERE user_name LIKE %s",
        (f"%{keyword}%",)
    )
    return render_template('search.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)