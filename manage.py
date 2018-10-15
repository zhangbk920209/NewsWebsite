from info import create_app,models,db
from flask_script import Manager
from flask_session import Session
from flask_migrate import Migrate, MigrateCommand

# 调用工厂函数创建应用
app = create_app('development')
# 实例化管理器 关联管理器对象与应用对象
manage = Manager(app)
# 实例化Session类 关联Session对象与应用对象
Session(app)
# 迁移库关联应用对象及数据库
Migrate(app, db)
# 管理器添加命令
manage.add_command('db', MigrateCommand)

if __name__ == '__main__':
    print(app.url_map)
    manage.run()
