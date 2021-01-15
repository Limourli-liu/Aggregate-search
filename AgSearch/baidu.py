import requests
from lxml import etree
try:
    from pubilc.baiduspider import BaiduSpider
except:
    import os, sys
    sys.path.append("..")
    sys.path.extend([os.path.join(root, name) for root, dirs, _ in os.walk("../") for name in dirs])
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
    Baidu.headers['Cache-Control'] =  'no-cache'
    Baidu.headers['Pragma'] =  'no-cache'
    Baidu.headers['Sec-Fetch-Dest'] =  'document'
    Baidu.headers['Sec-Fetch-Mode'] =  'navigate'
    Baidu.headers['Sec-Fetch-Site'] =  'none'
    Baidu.headers['Sec-Fetch-User'] =  '?1'
    Baidu.headers['Upgrade-Insecure-Requests'] =  '1'
    Baidu.headers['Cookie'] = 'BIDUPSID=CA16753CF20338F61EFF2308D75FD378; PSTM=1610690081; BAIDUID=CA16753CF20338F6B2F0E1BEB8012DB7:FG=1; delPer=0; BD_CK_SAM=1; PSINO=6; H_PS_PSSID=33425_33466_33358_33259_33344_31254_33286_33414_26350; BD_UPN=12314753; H_PS_645EC=7537lWQ5t2PgtXC38yxw3ryuLYY7rT9I4Etn%2F9E%2BnTSJosnALJXW66DITPs; BA_HECTOR=8g2180048laka020i61g02bh40r; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598'

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
        elif item['type'] == 'tieba':
            item = item['result']
            t = item['title']
            s = f'<div><img src="{item["cover"]}" style="height:85px"></img>{item["des"]}</div>'
            d = f'引擎：Baidu 来源：贴吧 帖数：{item["total"]} 关注：{item["followers"]}'
            u = item['url']
            hot = ''
            for x in item['hot']:
                hot = f'{x["title"]}_{x["clicks"]}_{x["replies"]}' 
                hot = f'<div><a href="{x["url"]}">{hot}</a></div>'
                s += hot
            res.append((t, s, d, u))
    return res

if __name__ == '__main__':
    t = BaiduSpider()
    t.headers['Cache-Control'] =  'no-cache'
    t.headers['Pragma'] =  'no-cache'
    t.headers['Sec-Fetch-Dest'] =  'document'
    t.headers['Sec-Fetch-Mode'] =  'navigate'
    t.headers['Sec-Fetch-Site'] =  'none'
    t.headers['Sec-Fetch-User'] =  '?1'
    t.headers['Upgrade-Insecure-Requests'] =  '1'
    t.headers['Cookie'] = 'BIDUPSID=CA16753CF20338F61EFF2308D75FD378; PSTM=1610690081; BAIDUID=CA16753CF20338F6B2F0E1BEB8012DB7:FG=1; delPer=0; BD_CK_SAM=1; PSINO=6; H_PS_PSSID=33425_33466_33358_33259_33344_31254_33286_33414_26350; BD_UPN=12314753; H_PS_645EC=7537lWQ5t2PgtXC38yxw3ryuLYY7rT9I4Etn%2F9E%2BnTSJosnALJXW66DITPs; BA_HECTOR=8g2180048laka020i61g02bh40r; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598'
    #a = t.search_web(query='异度侵入', pn=1)
    a = t.search_web(query='弱音吧', pn=1)
    