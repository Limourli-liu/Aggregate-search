import pkgutil, sqlite3, json, traceback, os, threading, atexit, time
import logging, logging.config

def _interval():
    last = time.time()
    while True:
        now = time.time()
        yield now - last
        last = now
def _path(name, root=None):
    p =  os.path.join(root or os.getcwd(), name)
    return (os.path.exists(p) or not os.makedirs(p)) and p
def _rJson(path):
    with open(path) as f:
        return json.load(f)
def _wJson(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
def _logDefault(path, name):
        config = {
        "version": 1,
        "disable_existing_loggers": False, # 禁用已经存在的logger实例
        "formatters":{ # 日志格式化(负责配置log message 的最终顺序，结构，及内容)
            "simple":{ #简单的格式
                "format":"%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers":{ # 负责将Log message 分派到指定的destination
            "console":{ # 打印到终端的日志
                "class":"logging.StreamHandler", # 打印到屏幕
                "level":"DEBUG",
                "formatter":"simple",
                "stream":"ext://sys.stdout"
            },
            "common":{ # 打印到log文件的日志,收集info及以上的日志
                "class":"logging.handlers.RotatingFileHandler", # 保存到文件
                "level":"INFO",
                "formatter":"simple",
                "filename":path, # 日志文件路径
                "maxBytes":10485760, #日志大小 10M
                "backupCount":3, # 备份3个日志文件
                "encoding":"utf8" # 日志文件的编码
            },
        },
        "loggers":{ # logger实例
            name:{
                "level":"DEBUG",
                "handlers":["console", "common"], # log数据打印到控制台和文件
                "propagate": True # 向上（更高level的logger）传递
            }
        }}
        return config
def _getConf(path, Default):
    if os.path.exists(path):
        config = _rJson(path)
        return config
    else:
        _wJson (path, Default)
        return Default
class Config(dict):
    def __init__(self, root, name, Default):
        self.path = f'{root}/{name}.json'
        self.update(_getConf(self.path, Default))
    def save(self):
        _wJson(self.path, self)

class DB_Table(object):
    def __init__(self, name, cursor, lock):
        self.name = name
        self.cursor = cursor
        self.lock = lock
    def insert(self, col, values):
        with self.lock:
            return self.cursor.execute(f'INSERT INTO {self.name} ({col}) VALUES ({values})')
    def select(self, col):
        with self.lock:
            return tuple(self.cursor.execute(f'SELECT {col} from {self.name}'))
    def select_(self, col, where):
        with self.lock:
            return tuple(self.cursor.execute(f'SELECT {col} from {self.name} where {where}'))
    def slip(self, col, ord, range_start, range_size):
        with self.lock:
            return tuple(self.cursor.execute(f'SELECT {col} from {self.name} order by {ord} limit {range_start},{range_size}'))
    def update(self, where, _set):
        with self.lock:
            return self.cursor.execute(f'UPDATE {self.name} set {_set} where {where}')
    def delete(self, where):
        with self.lock:
            return self.cursor.execute(f'DELETE from {self.name} where {where}')
    def show(self):
        cursor = self.select('*')
        for row in cursor:
            print(*row)
class DataBase(object):
    def __init__(self, path):
        self.lock = threading.Lock()
        with self.lock:
            self.datab = sqlite3.connect(path, check_same_thread=False)
            self.cursor =  self.datab.cursor() 
    def close(self):
        with self.lock:
            self.datab.close()
    def commit(self):
        with self.lock:
            self.datab.commit()
    def execute(self, sql):
        with self.lock:
            return self.cursor.execute(sql)
    def create(self, name, structure):
        with self.lock:
            tmp = self.cursor.execute("select count(*) from sqlite_master where type='table' and name = ?", (name,))
            if next(tmp)[0] == 0: tmp = self.cursor.execute(f'CREATE TABLE {name} ({structure});')
            if tmp is not None:
                return self.getTable(name)
    def getTable(self, name):
        return DB_Table(name, self.cursor, self.lock)

class ModManager(object):
    def __init__(self, name):
        self.name = name
        self.root = _path(f'data/{name}')
        logConf = Config(self.root, 'logging', _logDefault(f'data/{name}/Mod.log', name))
        logging.config.dictConfig(logConf)# 导入上面定义的logging配置
        self.logger = logging.getLogger(name)
        self.logger.debug(f'ModManager __init__({name})')
        self.threading_lock = threading.Lock()
        self.logger.debug(f'ModManager.threading_lock {self.threading_lock}')
        self.db = DataBase(f'{self.root}/Mod.db')
        self.logger.debug('ModManager.DataBase connected')
        atexit.register(self._exit)
        self.logger.debug('ModManager exitfunc registered')
        plugins = {}
        for finder,m_name,ispck in pkgutil.walk_packages([_path(name)]):
            self.logger.debug(f'ModManager plugin load {m_name}')
            loader = finder.find_module(m_name)
            try:
                mod = loader.load_module(m_name)
                plugins[m_name] = mod
            except:
                self.logger.error(f'ModManager load {m_name} {traceback.format_exc()}')
        self.logger.debug('ModManager plugins all loaded')
        contab = {}
        for m_name,mod in plugins.items():
            self.logger.debug(f'ModManager {m_name}.init')
            try:
                default = mod._default_config(self.root, m_name)
            except:
                default = {}
                self.logger.error(f'ModManager {m_name}._default_config {traceback.format_exc()}')
            try:
                config = Config(self.root, m_name, default)
                mod._init(config, self.db, logging.getLogger(f'{name}.{m_name}'), self.threading_lock, m_name)
                interval = config.get('Contab_Interval', 0)
                if interval > 0: #加入定时执行池
                    contab[m_name] = interval
            except:
                self.logger.error(f'ModManager {m_name}.init {traceback.format_exc()}')
        self.logger.debug(f'ModManager plugins.init all done')
        self.plugins = plugins
        self.contab = contab
        self.contab_r = contab.copy()
        self.interval = _interval()
        self.contab_t = threading.Thread(target=self._contab, daemon=True)
        self.contab_c = True #主线程控制信号， True表示子线程循环执行
        self.contab_w = False #不要求主线程等待，可以直接结束
        self.contab_t.start()
        self.logger.debug(f'ModManager contab.start')
    def _contab(self):
        while self.contab_c: #主线程控制信号， True继续
            slp = 60.0 - next(self.interval)
            self.logger.debug(f'ModManager contab.sleep time {slp}')
            time.sleep(0 if slp < 0 else slp)
            next(self.interval) #重新开始计时
            for m_name,interval in self.contab_r.items():
                if not self.contab_c: break #主线程控制信号， Fales退出
                self.contab_r[m_name] = interval - 1
                if self.contab_r[m_name] <= 0:
                    self.contab_r[m_name] = self.contab[m_name] #执行一次后重置倒计时
                    self.logger.debug(f'ModManager {m_name}.contab')
                    try:
                        self.contab_w = True #需要主线程等待，以防冲突
                        self.plugins[m_name]._contab()
                    except:
                        self.logger.error(f'ModManager {m_name}.contab {traceback.format_exc()}')
                    self.contab_w = False #不需要主线程等待，可以直接结束
        self.logger.debug(f'ModManager contab.exit')
    def _exit(self):
        self.contab_c = False
        if self.contab_w:
            self.logger.debug(f'ModManager waiting contab.exit')
            self.contab_t.join(61) #等待contab线程结束, 最多等61秒
        else:
            self.logger.debug(f'ModManager not waiting contab.exit')
        for  m_name,mod in self.plugins.items():
            self.logger.debug(f'ModManager {m_name}.exit')
            try:
                mod._exit()
            except:
                self.logger.error(f'ModManager {m_name}.exit {traceback.format_exc()}')
        self.logger.debug(f'ModManager plugins.exit all done')
        self.db.commit()
        self.db.close()
        self.logger.debug(f'ModManager.DataBase committed and closed')
        self.logger.debug(f'ModManager exit')
    def call(self, attr, *args, **kw):
        res = []
        for  m_name,mod in self.plugins.items():
            self.logger.debug(f'ModManager {m_name}.{attr}')
            try:
                res.append(getattr(mod, attr)(*args, **kw))
            except:
                self.logger.error(f'ModManager {m_name}.{attr} {traceback.format_exc()}')
        self.logger.debug(f'ModManager plugins.{attr} all done')
        return res
if __name__ == '__main__':
    test = ModManager('test')
    #print(test.call('_test'))
    #time.sleep(2*60+1) #保准示例的contab执行一次
    b = test.db
    c = b.create('text2', 'id integer PRIMARY KEY autoincrement, Name varchar(30), Age integer, udate')
    c.insert('age','1')
    c.insert('age','2')
    c.insert('age','3')
    c.insert('age','4')
    c.show()
    d = c.select_('age', 'name is null')