import requests
from lxml import etree
from baiduspider import BaiduSpider

config, db, log, lock = 0,0,0,0  #保存宿主传递的环境 分别为配置文件， 数据库，日志，全局线程锁
def _default_config(root, name): #返回默认配置文件 载入时被调用 root为数据文件根目录 name为当前模块名称
    return {
        'modInformation':{ #该模块的信息
            'Name': 'Search by Baidu',
            'Author': 'Limour @limour.top',
            'Version': '1.0',
            'description': '获取百度的搜索结果'
        },
        'Contab_Interval': 0 #不用执行
    }

Baidu = 0
def _init(_config, _db, _log, _lock, m_name): #载入时被调用
    global config, db, log, lock
    config, log, lock = _config, _log, _lock #保存宿主传递的环境
    global Baidu
    Baidu = BaiduSpider()

def _contab():
    pass

def _exit():
    pass

def _search(s, pid):
    #[(标题,内容,注释,URL)]
    tmp = Baidu.search_web(query=s, pn=pid+1)
    res = []
    for item in tmp['results']:
        if item['type'] == 'result':
            t = item['title']
            s = item['des']
            d = f'引擎：Baidu 来源：{item["origin"]} 时间：{item["time"]}'
            u = item['url']
            res.append((t, s, d, u))
        elif item['type'] == 'calc':
            t = f'在线计算器：{item["result"]}'
            s = item['process']
            d = '引擎：Baidu'
            u = 'https://zaixianjisuanqi.bmcx.com/'
            res.append((t, s, d, u))
        elif item['type'] == 'news':
            #log.debug(item)
            for news in item['results']:
                t = news['title']
                s = news['des']
                d = f'引擎：Baidu 来源：{news["author"]} 时间：{news["time"]}'
                u = news['url']
                res.append((t, s, d, u))
        elif item['type'] == 'video':
            for video in item['results']:
                t = video['title']
                if video["cover"] is not None:
                    s = f'<img src="{video["cover"]}" style="height:85px"></img>' + video['des']
                else:
                    s = video['des']
                d = f'引擎：Baidu 来源：{video["origin"]} 时长：{video["length"]}'
                u = video['url']
                res.append((t, s, d, u))
        elif item['type'] == 'baike':
            item = item['result']
            t = item['title']
            if item["cover-type"] is None:
                s = item['des']
            elif item["cover-type"] == 'image':
                s = f'<img src="{item["cover"]}" style="height:85px"></img>' + item['des']
            elif item["cover-type"] == 'video':
                #s = f'<iframe src="{item["cover"]}" style="width: 100%;height: 100%;object-fit: cover;"></iframe>' + item['des']
                #s = f'<video controls="controls" autoplay="autoplay" style="width: 100%;height: 100%;object-fit: cover;"><source src="{item["cover"]}"/></video>' + item['des']
                s = f'<a href="{item["cover"]}" target="_blank">点击下载视频</a>' + item['des']
            d = f'引擎：Baidu 来源：百度百科'
            u = item['url']
            res.append((t, s, d, u))
    return res

if __name__ == '__main__':
    t = BaiduSpider()
    a = t.search_web(query='弱音 百度百科', pn=1)
    