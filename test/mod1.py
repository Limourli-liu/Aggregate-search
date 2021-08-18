
config, Manager, log, lock = 0,0,0,0 #保存宿主传递的环境 分别为配置文件， 模块管理器，日志，全局线程锁
def _default_config(root, name): #返回默认配置文件 载入时被调用 root为数据文件根目录 name为当前模块名称
    return {
        'modInformation':{ #该模块的信息
            'Name': 'Example Mod',
            'Author': 'Limour @limour.top',
            'Version': '1.0',
            'description': 'an example of mods'
        },
        'crontab_Interval': 2, #每2分钟执行一次_crontab 粒度为1分钟
        'priority':9999 # 模块加载和调用的优先级，越大越先，默认为0
    }

def _init(m_name, _config, _Manager, _log): #载入时被调用
    global config, Manager, log, lock
    config, Manager, log, lock = _config, _Manager, _log, _Manager.threading_lock #保存宿主传递的环境
    _db = Manager.getMod('database').db
    db = _db.create(m_name, 'id integer PRIMARY KEY autoincrement, Name varchar(30), Age integer') #创建新表或得到已创建的表
    Manager.getMod("crontab").submit(m_name, config["crontab_Interval"], _crontab)
    pass

def _exit():# 载入时被调用
    log.debug('exit')
    pass

def _crontab():# 定时调用，间隔在默认配置文件中设置
    log.debug('crontab')
    import time
    time.sleep(1)
    pass

def c():
    try:
        int('xyz')
    except:
        1/0

def b():
    c()

def a():
    b()


def _test():
    log.debug('_test')
    # a()
    return 1

