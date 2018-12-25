from flask import render_template, g, redirect, jsonify, request, abort, current_app

from info import db
from info.constants import QINIU_DOMIN_PREFIX
from info.models import User
from utils.common import user_login_data
from utils.img_stroge import upload_img
from utils.response_code import RET, error_map
from . import user_blu


# 显示用户信息
@user_blu.route('/user_info')
@user_login_data
def user_info():
    user = g.user
    if not user:
        return redirect("/")

    return render_template("news/user.html", user=user.to_dict())


# 基本资料显示／修改
@user_blu.route('/base_info', methods=["GET", "POST"])
@user_login_data
def user_base_info():
    user = g.user
    if not user:
        return abort(404)

    if request.method == "GET":
        return render_template("news/user_base_info.html", user=user.to_dict())

    # 获取参数-个性签名/昵称/性别
    signature = request.json.get("signature")
    nick_name = request.json.get("nick_name")
    gender = request.json.get("gender")

    # 校验参数
    if not all([signature, nick_name, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if gender not in ["MAN", "WOMAN"]:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 修改数据库中的数据
    user.gender = gender
    user.signature = signature
    user.nick_name = nick_name

    # 返回json
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 用户头像显示／修改
@user_blu.route('/pic_info', methods=['POST', 'GET'])
@user_login_data
def pic_info():
    user = g.user
    if not user:
        return abort(404)

    if request.method == "GET":
        return render_template("news/user_pic_info.html", user=user.to_dict())
    # 不是GET,就是修改数据
    try:
        img_bytes = request.files.get("avatar").read()
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 上传文件  云存储平台   压缩方式优化, 传输宽带高, 数据去重
    try:
        key = upload_img(img_bytes)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])

    user.avatar_url = key

    # 将文件的访问url返回给前端
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data={"avatar_url": QINIU_DOMIN_PREFIX + key})


# 修改密码
@user_blu.route('/pass_info', methods=['POST', 'GET'])
@user_login_data
def pass_info():
    user = g.user
    if not user:
        return abort(404)

    if request.method == "GET":
        return render_template("news/user_pass_info.html")

    # 获取参数-旧密码/新密码
    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")

    # 校验参数
    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if not user.check_passoword(old_password):
        return jsonify(errno=RET.PWDERR, errmsg=error_map[RET.PWDERR])

    # 修改数据库中密码数据
    user.password = new_password

    # 返回结果
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 发布新闻
@user_blu.route('/news_release', methods=['POST', 'GET'])
@user_login_data
def news_release():
    user = g.user
    if not user:
        return abort(404)

    if request.method == "GET":
        categores = []
        # 取出所有的分类
        try:
            categores = Category.query.all()
        except BaseException as e:
            current_app.logger.error(e)

        if len(categores):
            categores.pop(0)
        return render_template("news/user_news_release.html", categores=categores)

    # 获取参数－标题／分类／摘要／图片／内容
    title = request.form.get("title")
    category_id = request.form.get("category_id")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_img = request.files.get("index_image")

    # 校验参数
    if not all([title, category_id, digest, content, index_img]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 格式转换
    try:
        category_id = int(category_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 　上传图片
    try:
        index_img_bytes = index_img.read()
        key = upload_img(index_img_bytes)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])

    # 创建新闻模型
    news = News()
    news.title = title
    news.digest = digest
    news.user_id = user.id
    news.category_id = category_id
    news.content = content
    news.index_image_url = QINIU_DOMIN_PREFIX + key
    news.source = "个人发布"

    # 设置发布状态
    news.status = 1

    db.session.add(news)

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 显示个人主页
@user_blu.route('/other')
@user_login_data
def other():
    # 获取参数
    user_id = request.args.get("user_id")
    try:
        user_id = int(user_id)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(404)

    try:
        author = User.query.get(user_id)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(404)

    if not author:
        return abort(404)

    user = g.user

    is_followed = False
    # 登录状态
    if user:
        # 判断当前用户是否关注了这个作者
        if author in user.followed:
            is_followed = True

    # 获取参数
    page = request.args.get("p", 1)
    try:
        page = int(page)
    except BaseException as e:
        current_app.logger.error(e)
        page = 1

    # 查询该用户发布的新闻
    news_list = []
    total_pages = 1
    try:
        pn = News.query.filter(News.user_id == author.id, News.status == 0).paginate(page, USER_COLLECTION_MAX_NEWS)
        news_list = [news.to_review_dict() for news in pn.items]
        total_pages = pn.pages
    except BaseException as e:
        current_app.logger.error(e)

    data = {
        "total_page": total_pages,
        "news_list": news_list,
        "cur_page": page
    }
    user = user.to_dict() if user else None

    return render_template("news/other.html", author=author.to_dict(), user=user, is_followed=is_followed, data=data)
