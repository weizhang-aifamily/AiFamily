from flask import Flask, render_template, request
from dbconnect.dbconn import db
from bak.member_routes import member_bp
from models.family_bp import family_bp

app = Flask(__name__)

# 注册蓝图
app.register_blueprint(member_bp)
app.register_blueprint(family_bp)

# 保留原有的基本路由
@app.route('/')
def index():
    users = db.query("SELECT * FROM ejia_user ")
    return render_template('peican.html', users=users)

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