import datetime
import random
from flask import current_app
from flask_migrate import MigrateCommand
from flask_script import Manager
from info import create_app

# 调用创建app的工厂函数


app = create_app('dev')
# 创建app管理器对象
mgr = Manager(app)
# 将迁移命令添加到管理者中
mgr.add_command('mc', MigrateCommand)


# 生成超级管理员
@mgr.option("-name", "-n", dest="name")
@mgr.option("-password", "-p", dest="password")
def create_superuser(name, password):
    if not all([name, password]):
        print("参数不足")
        return

    from info.models import User
    # 生成用户模型
    user = User()
    user.mobile = name
    user.password = password
    user.nick_name = name
    # 设置is_admin属性为true
    user.is_admin = True

    from info import db
    # 　保存到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except BaseException as e:
        current_app.logger.error(e)


# 添加测试用户数据
def add_test_users():
    from info import db
    from info.models import User
    users = []
    now = datetime.datetime.now()
    for num in range(0, 10000):
        try:
            user = User()
            user.nick_name = "%011d" % num
            user.mobile = "%011d" % num
            user.password_hash = "pbkdf2:sha256:50000$SgZPAbEj$a253b9220b7a916e03bf27119d401c48ff4a1c81d7e00644e0aaf6f3a8c55829"
            user.last_login = now - datetime.timedelta(seconds=random.randint(0, 2678400))
            user.create_time = now - datetime.timedelta(seconds=random.randint(0, 2678400))
            users.append(user)
            print(user.mobile)
        except Exception as e:
            print(e)
    db.session.add_all(users)
    db.session.commit()
    print('OK')


if __name__ == '__main__':
    mgr.run()
    # add_test_users()  # 添加测试用户数据
