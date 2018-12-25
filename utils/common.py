import functools
from flask import session, g

from info.models import User


# 自定义过滤器
def index_converter(index):
    index_dict = {1: "first", 2: 'second', 3: 'third'}

    return index_dict.get(index, '')


# 自定义登陆装饰其
def user_login_data(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # 取出session中的数据判断是否登陆
        user_id = session.get('user_id')

        user = None  # type:User
        if user_id:
            user = User.query.get(user_id)

        g.user = user

        return f(*args, **kwargs)

    return wrapper
