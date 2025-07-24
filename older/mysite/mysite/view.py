from django.shortcuts import render
import pymysql
from django.conf import settings


def show_student(request):
    context = {'students': []}

    try:
        # 使用 Django 配置管理数据库连接信息（推荐）
        db_config = getattr(settings, 'DB_CONFIG', {
            'host': 'localhost',
            'user': 'root',
            'password': '153@TPJHtpjh',
            'db': 'dbsclab2018',
            'port': 3306
        })

        # 使用上下文管理器自动处理连接
        with pymysql.connect(
                cursorclass=pymysql.cursors.DictCursor,
                **db_config
        ) as connection:
            with connection.cursor() as cursor:
                if request.method == 'POST':
                    name = request.POST.get('name', '')
                    sql = "SELECT * FROM student WHERE name LIKE %s"
                    cursor.execute(sql, [f'%{name}%'])
                else:
                    sql = "SELECT * FROM student"
                    cursor.execute(sql)

                context['students'] = cursor.fetchall()

    except Exception as e:
        # 实际项目中应添加更详细的错误处理
        context['error'] = str(e)

    return render(request, 'student.html', context)