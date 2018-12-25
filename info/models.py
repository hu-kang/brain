from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

from info import constants, db


class BaseModel(object):
    """模型基类，为每个模型补充创建时间与更新时间"""
    create_time = db.Column(db.DateTime, default=datetime.now)  # 记录的创建时间
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 记录的更新时间


class User(BaseModel, db.Model):
    """用户"""
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)  # 用户编号
    nick_name = db.Column(db.String(32), unique=True, nullable=False)  # 用户昵称
    password_hash = db.Column(db.String(128), nullable=False)  # 加密的密码
    mobile = db.Column(db.String(11), unique=True, nullable=False)  # 手机号
    avatar_url = db.Column(db.String(256))  # 用户头像路径
    last_login = db.Column(db.DateTime, default=datetime.now)  # 最后一次登录时间
    is_admin = db.Column(db.Boolean, default=False)
    signature = db.Column(db.String(512))  # 用户签名
    gender = db.Column(  # 订单的状态
        db.Enum(
            "MAN",  # 男
            "WOMAN"  # 女
        ),
        default="MAN")

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "nick_name": self.nick_name,
            "avatar_url": constants.QINIU_DOMIN_PREFIX + self.avatar_url if self.avatar_url else "",
            "mobile": self.mobile,
            "gender": self.gender if self.gender else "MAN",
            "signature": self.signature if self.signature else "",
            "followers_count": self.followers.count(),
            "news_count": self.news_list.count()
        }
        return resp_dict

    def to_admin_dict(self):
        resp_dict = {
            "id": self.id,
            "nick_name": self.nick_name,
            "mobile": self.mobile,
            "register": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": self.last_login.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return resp_dict

    @property
    def password(self):
        raise AttributeError("该属性不能直接读取")

    @password.setter
    def password(self, value):
        self.password_hash = generate_password_hash(value)

    def check_passoword(self, password):
        return check_password_hash(self.password_hash, password)
