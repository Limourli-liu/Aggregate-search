import pkgutil, sqlite3, json, sys, traceback
conf = {}
def readConf():
    global conf
    with open(r'./data/AgInfo.json') as f:
        conf = json.load(f)
def saveConf():
    with open(r'./data/AgInfo.json', 'w') as f:
        json.dump(conf, f, indent=4, ensure_ascii=False)
readConf()
class DataBase(object):
    def __init__(self):
        self.datab = sqlite3.connect(f'./data/infodata.db')
        self.cursor =  self.datab.cursor() 
    def close(self):
        self.datab.close()
    def execute(self, sql):
        return self.cursor.execute(sql)
    def commit(self):
        self.datab.commit()
    def create(self, name, structure):
        return self.cursor.execute(f'CREATE TABLE {name} \n ({structure});')
    def insert(self, name, col, values):
        return self.cursor.execute(f'INSERT INTO {name} ({col}) VALUES ({values})')
    def select(self, name, col):
        return self.cursor.execute(f'SELECT {col} from {name}')
    def update(self, name, where, set):
        return self.cursor.execute(f'UPDATE {name} set {set} where {where}')
    def delete(self, name, where):
        return self.cursor.execute(f'DELETE from {name} where {where}')
    def show(self, name):
        cursor = self.select(name, '*')
        for row in cursor:
            print(*row)
db = DataBase()

_plugins = []
mod_information = []
for finder,name,ispck in pkgutil.walk_packages(["./info"]):
    loader = finder.find_module(name)
    mod = loader.load_module(name)
    _plugins.append(mod)

for mod in _plugins:
    mod_information.append(mod._start(conf, db))

def _info(pid):
    res = []
    for mod in _plugins:
        try:
            res.extend(mod._info(pid))
        except:
            traceback.print_exc()
    return res

def exitfunc():
    for mod in _plugins:
        mod._exit()
    db.close()
    print ('AgInfo exit!')
sys.exitfunc=exitfunc
