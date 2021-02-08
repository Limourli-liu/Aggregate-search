import pkgutil, sqlite3, json, traceback, os, threading, atexit, time
import logging, logging.config
from concurrent.futures import ThreadPoolExecutor

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
    with open(path, encoding='utf-8') as f:
        return json.load(f)
def _wJson(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
def _format_exception(e, res):
    if e.__context__ is not None:
        _format_exception(e.__context__, res)
        res.append('\n\nDuring handling of the above exception, another exception occurred:\n\n')
    res.append('Traceback (most recent call last):\n')
    res.extend(traceback.format_tb(e.__traceback__))
    res.append(f'{repr(e)}')
def format_exception(e):
    res = []
    _format_exception(e, res)
    return ''.join(res)
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

class Signal():
    sig = True # 控制信号， True表示线程继续执行
    state = False # 表明当前线程执行到哪一阶段
    def __init__(self):
        self._lock = threading.Lock() # 控制信号的锁
    def _set(self, sig):
        with self._lock:
            self.sig = sig
            return self.state
    def __call__(self, state):
        with self._lock:
            self.state = state
            return self.sig
class Timer(object):
    def __init__(self, _repeat, interval_scale = 60.0, _start=None):
        self._repeat = _repeat # 需要循环定时执行的函数
        self._i_scale = interval_scale # 时间间隔
        self._s = _start # 进入循环前执行的函数
        self.sig = Signal() # 交互控制信号
        self.t = threading.Thread(target=self._exec, daemon=True)
        self.t.start()
    def _exec(self):
        if self._s: self._s()
        _itv = _interval() # 间隔计时器
        while self.sig(False): # False表示可以中断的阶段
            slp = self._i_scale - next(_itv) # 需要休眠的时间
            if slp > 0: time.sleep(slp)
            next(_itv) # 重新开始计时
            if not self.sig(True): break # True表示需要等待的阶段
            self._repeat()
    def exit(self):
        if self.sig._set(False): # 设置为退出状态，并获取线程执行阶段
            self.t.join(self._i_scale+1) # 等待exec线程结束, 最多等interval_scale+1秒
            return not self.t.is_alive() # 是否成功结束
        return True

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
    def __init__(self, name, max_workers=4):
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
        crontab = {}
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
                interval = config.get('crontab_Interval', 0)
                if interval > 0: #加入定时执行池
                    crontab[m_name] = interval
            except:
                self.logger.error(f'ModManager {m_name}.init {traceback.format_exc()}')
        self.logger.debug(f'ModManager plugins.init all done')
        self.plugins = plugins
        self.crontab = crontab
        if self.crontab: #存在定时项目
            self.crontab_r = crontab.copy() #中间变量
            self.timer = Timer(self._crontab)
            self.logger.debug(f'ModManager crontab.start')
        self.threadPool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=f"{name}.")
    def _crontab(self):
        for m_name,interval in self.crontab_r.items():
            self.crontab_r[m_name] = interval - 1
            if self.crontab_r[m_name] <= 0:
                self.crontab_r[m_name] = self.crontab[m_name] #执行一次后重置倒计时
                self.logger.debug(f'ModManager {m_name}.crontab')
                try:
                    self.plugins[m_name]._crontab()
                except:
                    self.logger.error(f'ModManager {m_name}.crontab {traceback.format_exc()}')
    def _exit(self):
        self.threadPool.shutdown(wait=True)
        self.logger.debug(f'ModManager threadPool.shutdown')
        if self.crontab: #存在定时项目
            tmp = self.timer.exit()
            self.logger.debug(f'ModManager crontab.exit {tmp}')
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
        res = {}
        for  m_name,mod in self.plugins.items():
            self.logger.debug(f'ModManager {m_name}.{attr}')
            try:
                future = self.threadPool.submit(getattr(mod, attr), *args, **kw)
                res[m_name] = future
            except:
                self.logger.error(f'ModManager {m_name}.{attr} {traceback.format_exc()}')
        self.logger.debug(f'ModManager plugins.{attr} have been added to threadPool')
        resu = []
        for  m_name,future in res.items():
            try:
                r = future.result()
                excp = future.exception()
                if excp is None:
                    resu.append(r)
                else:
                    self.logger.error(f'ModManager {m_name}.{attr} {format_exception(excp)}')
            except:
                self.logger.error(f'ModManager {m_name}.{attr} {traceback.format_exc()}')
        self.logger.debug(f'ModManager plugins.{attr} all done')
        return resu
if __name__ == '__main__':
    test = ModManager('test')
    print(test.call('_test'))
    #time.sleep(2*60+1) #保准示例的crontab执行一次