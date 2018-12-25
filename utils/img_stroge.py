import qiniu

# 需要填写你的 Access Key 和 Secret Key
access_key = 'kJ8wVO7lmFGsdvtI5M7eQDEJ1eT3Vrygb4SmR00E'
secret_key = 'rGwHyAvnlLK7rU4htRpNYzpuz0OHJKzX2O1LWTNl'
# 内容空间的名称
bucket_name = "infonews"


# 上传文件
def upload_img(data):
    q = qiniu.Auth(access_key, secret_key)
    key = None  # 上传文件名 不设置会自动生成随机名称

    token = q.upload_token(bucket_name)
    ret, info = qiniu.put_data(token, key, data)
    if ret is not None:
        return ret.get("key")  # 取出上传的文件名
    else:
        raise Exception(info)
