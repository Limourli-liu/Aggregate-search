import requests, traceback, threading
from lxml import etree
try:
    from pubilc.summary import getSummary
except:
    import os, sys
    sys.path.append("..")
    sys.path.extend([os.path.join(root, name) for root, dirs, _ in os.walk("../") for name in dirs])
    from summary import getSummary

from sqlite3 import IntegrityError

def _de(string):
    return string.replace("''","'")
def _en(string):
    return string.replace("'","''")


def getUrl_Title(a):
    return a.xpath('./@href')[0], a.xpath('./text()')[0]

def getList(pid):
    r = requests.get(f'http://www.jwc.fudan.edu.cn/9397/list{pid}.htm')
    r.encoding = 'utf-8'
    html= etree.HTML(r.text)
    articles = html.xpath('//table[@class="wp_article_list_table"]') 
    r = articles[0].xpath('./tr')
    res = []
    for item in r:
        u,t = getUrl_Title(item.xpath('.//a')[0])
        d = item.xpath('.//td[@align="right"]/text()')[0].rstrip()
        res.append((d, t, u))
    return res
    #return etree.tostring(r,encoding='utf-8').decode('utf-8')

def getAbstract(u):
    r = requests.get(f"http://www.jwc.fudan.edu.cn{u}")
    if r.status_code != 200: 
        log.error(f'getAbstract {u} 网络错误')
        return False
    r.encoding = 'utf-8'
    html = etree.HTML(r.text)
    html = html.xpath('.//*/text()')
    text = []
    for st in html:
        st = st.strip()
        if st: text.append(st)
    try:
        s = text.index('通知公告') + 1
        e = text.index('快速链接', s)
        #print(text[s:e])
        text = ''.join(text[s:e])
    except:
        return '该内容需要登录才能获取摘要，请打开网页查看详细内容！'
    sumy = getSummary(text)
    return sumy

config, db, log, lock = 0,0,0,0  #保存宿主传递的环境 分别为配置文件， 数据库，日志，全局线程锁
def _default_config(root, name): #返回默认配置文件 载入时被调用 root为数据文件根目录 name为当前模块名称
    return {
        'modInformation':{ #该模块的信息
            'Name': 'Information from Fudan University JWC',
            'Author': 'Limour @limour.top',
            'Version': '1.0',
            'description': '从复旦大学教务处官网获取最新通知'
        },
        'Contab_Interval': 60 #每小时执行一次_contab 粒度为1分钟
    }

def _init(_config, _db, _log, _lock, m_name): #载入时被调用
    global config, db, log, lock
    config, log, lock = _config, _log, _lock #保存宿主传递的环境
    db = _db.create(m_name, 'URL TEXT PRIMARY KEY, title varchar(255), abstract TEXT, udate') #创建新表或得到已创建的表
    thd = threading.Thread(target=_contab) #初始更新一次
    thd.start()

def add_news(d,t,u):
    try:
        db.insert('URL, title, udate', f"'{_en(u)}', '{_en(t)}', date('{d}')")
    except IntegrityError:
        return False
    return True

def _exit():
    pass

def _contab():
    try:
        log.debug('update start')
        al = getList(1)
        for item in al:
            if not add_news(*item): break
        log.debug('update getList done')
        #log.debug(list(db.select_('URL', 'abstract is null')))
        for u, in db.select_('URL', 'abstract is null'):
            abst = getAbstract(_de(u))
            #log.debug(f'update getAbstract {abst}')
            if abst:
                db.update(f"URL='{u}'", f"abstract='{_en(abst)}'")
        log.debug('update getAbstract done')
    except:
        log.error(traceback.format_exc())

def _info(pid):
    #[(标题,内容,注释,URL)]
    res = []
    for u,t,a,d in db.slip('URL,title,abstract,udate','udate desc', pid*5, 5):
        if a is None: a = '摘要正在获取中...'
        res.append((_de(t), _de(a), f'来源：复旦教务处 时间：{d}', f"http://www.jwc.fudan.edu.cn{_de(u)}"))
    return res
