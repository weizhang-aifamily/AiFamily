from flask import Flask, render_template, request
from dbconnect.dbconn import db  # 导入数据库实例

app = Flask(__name__)

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