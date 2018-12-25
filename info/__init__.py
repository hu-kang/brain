from logging.handlers import RotatingFileHandler
import logging
from flask import Flask, render_template, current_app, g
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis
from config import conf

# 将数据库操作对象全局化，方便其他视图文件使用
db = None  # type:SQLAlchemy
sr = None  # type:StrictRedis


# 配置日志
def setup_log(log_level):
    # 设置日志的记录等级
    logging.basicConfig(level=log_level)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(pathname)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


# 封装创建app的工厂函数
def create_app(type):
    # 创建app
    app = Flask(__name__)
    # 选择配置类型
    config = conf[type]
    app.config.from_object(config)
    # 创建sql 数据库操作对象
    global db, sr
    db = SQLAlchemy(app)
    # 创建redis数据库操作对象
    sr = StrictRedis(host=config.REDIS_IP, port=config.REDIS_PORT, decode_responses=True)
    # 设置session存储
    Session(app)
    # 初始化迁移器
    Migrate(app, db)
    # 导入蓝图对象
    from info.modules.home import home_blu
    # 注册蓝图对象
    app.register_blueprint(home_blu)
    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)
    from info.modules.news import news_blu
    app.register_blueprint(news_blu)
    from info.modules.user import user_blu
    app.register_blueprint(user_blu)
    from info.modules.admin import admin_blu
    app.register_blueprint(admin_blu)

    # 配置日志
    setup_log(config.LOG_LEVEL)

    # 关联模型文件（不关联flask不知道这些继承db的模型）
    import info.models

    from utils.common import index_converter
    # 添加过滤器
    app.add_template_filter(index_converter, "index_converter")

    from utils.common import user_login_data
    # 捕获４０４错误并显示指定界面
    @app.errorhandler(404)
    @user_login_data
    def page_not_found(e):
        current_app.logger.error(e)

        user = g.user.to_dict() if g.user else None
        return render_template("news/404.html", user=user)

    # 开启csrf保护  只要是POST请求,都会校验令牌, 没有就会拒绝访问
    # TODO 功能完成后, 打开csrf保护, 单独校验即可
    # CSRFProtect(app)

    return app
