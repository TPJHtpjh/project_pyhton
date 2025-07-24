import pymysql
import argparse

def getdb():
    try:
        # 连接数据库（根据实际配置修改）
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='153@TPJHtpjh',
            db='dbsclab2018',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        # 获取所有表名
        tables= [list(table.values())[0] for table in cursor]
        for table in tables:
            cursor.execute(f"SHOW CREATE TABLE `{table}`")
            result = cursor.fetchone()
            if result:
                print(result)
        return 0
    except pymysql.MySQLError as e:
        print(f"Error connecting to database: {e}\n")
        return None
        

if __name__ == "__main__":
    getdb()