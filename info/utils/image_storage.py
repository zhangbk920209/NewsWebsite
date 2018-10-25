from qiniu import Auth, put_data

access_key = 'cSbNmWNEvqNo3Oe4K_pGT74o3Ub_wY_5zI8Jebqo'
secret_key = '8NTGjLMrwKyzzELigWQbE4eFpQiNOopMAy3oCpnB'

bucket_name = 'bucket'


# 函数接收图片read()后的二进制数据 存储到七牛云中
def storage(data):
    try:
        q = Auth(access_key, secret_key)
        token = q.upload_token(bucket_name)
        ret, info = put_data(token, None, data)
        print(ret, info)
    except Exception as e:
        raise e

    if info.status_code != 200:
        raise Exception("上传图片失败")
    return ret["key"]


if __name__ == '__main__':
    file = input('请输入文件路径')
    with open(file, 'rb') as f:
        storage(f.read())