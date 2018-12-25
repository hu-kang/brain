import random
import re
from datetime import datetime
from flask import request, abort, current_app, make_response, jsonify, Response, session
from info import sr, db
from info.lib.yuntongxun.sms import CCP
from info.models import User
from utils.captcha.pic_captcha import captcha
from utils.response_code import RET, error_map
from . import passport_blu


# 获取图片验证码
@passport_blu.route('/get_img_code')
def get_img_code():
    # 获取参数-图片key
    img_code_id = request.args.get('img_code_id')

    # 校验参数
    if not img_code_id:
        return abort(403)

    # 生成图片验证码
    name, img_code_text, img_code_bytes = captcha.generate_captcha()

    # 将图片验证码文字和图片key保存导数据库
    try:
        sr.set('img_code_id_' + img_code_id, img_code_text, ex=300)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(500)

    # 创建自定义响应对象（包含图片）
    response = make_response(img_code_bytes)  # type:Response
    response.content_type = 'image/jpeg'

    # 返回对象
    return response


# 获取短信验证码
@passport_blu.route('/get_sms_code', methods=['POST'])
def get_sms_code():
    # 获取参数-手机号/用户输入的图片验证码/图片验证码key
    img_code_id = request.json.get("img_code_id")
    mobile = request.json.get("mobile")
    img_code = request.json.get("img_code")

    # 校验参数
    if not all([img_code_id, mobile, img_code]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if not re.match(r"1[35678]\d{9}$", mobile):  # 手机号格式是否合格
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 判断用户是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg=error_map[RET.DATAEXIST])

    # 根据图片key取出数据库中的图片验证码文字
    try:
        real_img_text = sr.get("img_code_id_" + img_code_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 校验验证码是否过期/正确
    if not real_img_text:
        return jsonify(errno=RET.PARAMERR, errmsg='图片验证码已过期')

    if real_img_text != img_code.upper():
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 如果正确，生成短信验证码并发送
    # 生成短信验证码
    rand_num = '%04d' % random.randint(0, 9999)
    current_app.logger.info('短信验证码为：%s' % rand_num)

    # result = CCP().send_template_sms(mobile, [rand_num, 5], 1)
    # if result == -1:
    #     return jsonify(errno=RET.PARAMERR, errmsg="短信发送失败")

    # 短信发送成功，将短信验证码保存到数据库中
    try:
        sr.set('sms_code_' + mobile, rand_num, ex=60)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 用户注册
@passport_blu.route('/register', methods=['POST'])
def register():
    # 获取参数-手机号/密码/输入的短信验证码
    mobile = request.json.get('mobile')
    password = request.json.get('password')
    sms_code = request.json.get('sms_code')

    # 校验参数
    if not all([mobile, password, sms_code]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if not re.match(r'1[35678]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 从数据库取出短信验证码进行校验
    try:
        real_sms_code = sr.get('sms_code_' + mobile)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not real_sms_code:
        return jsonify(errno=RET.PARAMERR, errmsg='短信验证码已过期')

    if real_sms_code != sms_code:
        return jsonify(errno=RET.PARAMERR, errmsg='验证码输入错误')

    # 如果正确保存用户数据到数据库，注册成功
    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    user.password = password  # 进行密码加密操作

    try:
        db.session.add(user)
        db.session.commit()
    except BaseException as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 设置状态保持
    session["user_id"] = user.id
    # 记录最后登陆时间
    user.last_login = datetime.now()

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 用户登陆
@passport_blu.route('/login', methods=['POST'])
def login():
    # 获取参数-手机号/密码
    mobile = request.json.get('mobile')
    password = request.json.get('password')

    # 校验参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if not re.match(r'1[35678]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 查询是否有该用户
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not user:
        return jsonify(errno=RET.USERERR, errmsg=error_map[RET.USERERR])

    # 校验密码是否正确
    if not user.check_passoword(password):
        return jsonify(errno=RET.PWDERR, errmsg=error_map[RET.PWDERR])

    # 保持用户登陆状态
    session["user_id"] = user.id
    # 记录用户最后登陆时间
    user.last_login = datetime.now()

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])

@passport_blu.route('/logout')
def logout():
    # 删除session中的值
    session.pop("user_id",None)
    session.pop("is_admin", None)

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])
