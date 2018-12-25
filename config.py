from datetime import timedelta
import logging
from redis import StrictRedis


# 创建配置类
class Config:
    DEBUG = True  # 开启调试
    # sql数据库地址
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/brain'
    # 是否追踪sql数据库的变化
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # redis  数据库配置ip和端口
    REDIS_IP = '127.0.0.1'
    REDIS_PORT = 6379
    # 选择用什么数据库存储 session
    SESSION_TYPE = 'redis'
    # 创建session存储的数据库对象
    SESSION_REDIS = StrictRedis(host=REDIS_IP, port=REDIS_PORT)
    # 设置session数据的加密
    SESSION_USE_SIGNER = True
    # 设置秘钥
    SECRET_KEY = "pGSco16hquNSS2hOAs6FAT9QsMz1AXpAvi8Gqq1lDOpbi/EKumG3/SmOLhaocUPq"
    # 设置session过期时间
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True


# 创建配置子类--开发模式
class DevelopConfig(Config):
    # 是否开启调试
    DEBUG = True
    # 记录日志的级别
    LOG_LEVEL = logging.DEBUG


class ProductConfig(Config):
    # 是否开启调试
    DEBUG = False
    # 记录日志的级别
    LOG_LEVEL = logging.ERROR


# 设置配置字典
conf = {
    'dev': DevelopConfig,
    'pro': ProductConfig
}
