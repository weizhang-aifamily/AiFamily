import pymysql
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='Dd2009zw#',  # 请修改
    database='ejiacan'
)
print("连接成功！")
conn.close()