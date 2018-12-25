from flask import Blueprint

# 创建蓝图对象
user_blu = Blueprint('user',__name__,url_prefix="/user")

from .views import *