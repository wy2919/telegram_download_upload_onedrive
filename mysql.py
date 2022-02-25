import pymysql.cursors

# 连接数据库
from pymysql import OperationalError

connect = ''

def get_Connect(pd):
    global connect
    if pd == 1:
        connect = pymysql.Connect(
            host='remotemysql.com',  # 服务器地址
            port=3306,  # 端口
            user='xnf9bOerw3',  # 数据库用户名
            passwd='XaLiQRgcOB',  # 数据库密码
            db='xnf9bOerw3',  # 要连接的数据库
            charset='utf8'  # 连接编码，存在中文的时候，连接需要添加charset='utf8'，否则中文显示乱码。
        )
        return connect

    if connect != '':
        return connect
    else:

        connect = pymysql.Connect(
            host='remotemysql.com',  # 服务器地址
            port=3306,  # 端口
            user='xnf9bOerw3',  # 数据库用户名
            passwd='XaLiQRgcOB',  # 数据库密码
            db='xnf9bOerw3',  # 要连接的数据库
            charset='utf8'  # 连接编码，存在中文的时候，连接需要添加charset='utf8'，否则中文显示乱码。
        )
        return connect

def set(type,url,file_name,file_path,pd_name,pd_id,file_id):
    connect = pymysql.Connect(
        host='remotemysql.com',  # 服务器地址
        port=3306,  # 端口
        user='xnf9bOerw3',  # 数据库用户名
        passwd='XaLiQRgcOB',  # 数据库密码
        db='xnf9bOerw3',  # 要连接的数据库
        charset='utf8'  # 连接编码，存在中文的时候，连接需要添加charset='utf8'，否则中文显示乱码。
    )
    try:
        # 获取游标
        cursor = connect.cursor()

        sql="insert into data(type,url,file_name,file_path,pd_name,pd_id,file_id) values ('%s','%s','%s','%s','%s','%s','%s')"
        data = (type,url,file_name,file_path,pd_name,pd_id,file_id)
        cursor.execute(sql % data)
        connect.commit()
        print('数据插入成功：', str(file_id))
        if cursor.rowcount == 1:
            cursor.close()
            connect.close()
            return True
        else:
            cursor.close()
            connect.close()
            return False
    except Exception as e:
        print(e)
    except OperationalError as e:
        get_Connect(1)
        return set(type,url,file_name,file_path,pd_name,pd_id,file_id)

def get(file_id):
    connect = pymysql.Connect(
        host='remotemysql.com',  # 服务器地址
        port=3306,  # 端口
        user='xnf9bOerw3',  # 数据库用户名
        passwd='XaLiQRgcOB',  # 数据库密码
        db='xnf9bOerw3',  # 要连接的数据库
        charset='utf8'  # 连接编码，存在中文的时候，连接需要添加charset='utf8'，否则中文显示乱码。
    )
    # connect = get_Connect(2)
    try:
        # 获取游标
        cursor = connect.cursor()

        # 查询数据
        sql = "SELECT file_id FROM data WHERE file_id = '{}'".format(file_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        if len(data) == 0:
            cursor.close()
            connect.close()
            return True
        else:
            cursor.close()
            connect.close()
            return False
    except OperationalError as e:
        get_Connect(1)
        return get(file_id)
        # connect = pymysql.Connect(
        #     host='remotemysql.com',  # 服务器地址
        #     port=3306,  # 端口
        #     user='xnf9bOerw3',  # 数据库用户名
        #     passwd='XaLiQRgcOB',  # 数据库密码
        #     db='xnf9bOerw3',  # 要连接的数据库
        #     charset='utf8'  # 连接编码，存在中文的时候，连接需要添加charset='utf8'，否则中文显示乱码。
        # )
        # return get(file_id)


    # print()
    # for row in data:
    #     print(row[0])
    # print('共查找出', cursor.rowcount, '条数据')

# file = open("E:\爬虫/111.txt")
# for line in file:
#     sql = "INSERT INTO 图片链接 (url) VALUES ( '%s')"
#     data = (line.replace('\n',''))
#     cursor.execute(sql % data)
#     connect.commit()
#     print('成功插入', cursor.rowcount, '条数据')
#     # print(line)
#     # pass # do something
# file.close()
# 插入数据

#
# # 修改数据
# sql = "UPDATE db_name SET saving = %.2f WHERE account = '%s' "
# data = (8888, '13512345678')
# cursor.execute(sql % data)
# connect.commit()
# print('成功修改', cursor.rowcount, '条数据')
#
# # 查询数据
# sql = "SELECT url FROM 图片链接 WHERE id = %.2f "
# data = (430)
# cursor.execute(sql % data)
#
# for row in cursor.fetchall():
#     print(row[0])
# print('共查找出', cursor.rowcount, '条数据')
#
# # 删除数据
# sql = "DELETE FROM db_name WHERE account = '%s' LIMIT %d"
# data = ('13512345678', 1)
# cursor.execute(sql % data)
# connect.commit()
# print('成功删除', cursor.rowcount, '条数据')
#
# # 事务处理
# sql_1 = "UPDATE db_name SET saving = saving + 1000 WHERE account = '18012345678' "
# sql_2 = "UPDATE db_name SET expend = expend + 1000 WHERE account = '18012345678' "
# sql_3 = "UPDATE db_name SET income = income + 2000 WHERE account = '18012345678' "
#
# try:
#     cursor.execute(sql_1)  # 储蓄增加1000
#     cursor.execute(sql_2)  # 支出增加1000
#     cursor.execute(sql_3)  # 收入增加2000
# except Exception as e:
#     connect.rollback()  # 事务回滚
#     print('事务处理失败', e)
# else:
#     connect.commit()  # 事务提交
#     print('事务处理成功', cursor.rowcount)
#
# # 关闭连接
# cursor.close()
# connect.close()