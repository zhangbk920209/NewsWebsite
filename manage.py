from flask import current_app
from flask import jsonify

from info import create_app,models,db
from flask_script import Manager
from flask_session import Session
from flask_migrate import Migrate, MigrateCommand

# 调用工厂函数创建应用
from info.models import User
from info.utils.response_code import RET

app = create_app('development')
# 实例化管理器 关联管理器对象与应用对象
manage = Manager(app)
# 实例化Session类 关联Session对象与应用对象
Session(app)
# 迁移库关联应用对象及数据库
Migrate(app, db)
# 管理器添加命令
manage.add_command('db', MigrateCommand)


# 创建管理员账户
# 在script扩展，自定义脚本命令，以自定义函数的形式实现创建管理员用户
# 以终端启动命令的形式实现；
# 在终端使用命令：python manage.py create_supperuser -n admin -p 123456
@manage.option('-n', '-name', dest='name')
@manage.option('-p', '-password', dest='password')
def create_superuser(name, password):
    if not all([name, password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    super_user = User()
    super_user.is_admin = True
    super_user.nick_name = name
    super_user.mobile = name
    super_user.password =password
    try:
        db.session.add(super_user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据存储异常')



if __name__ == '__main__':
    print(app.url_map)
    manage.run()
