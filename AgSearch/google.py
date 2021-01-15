import traceback, requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from lxml import etree
try:
    from public.user_agents import getUA
except:
    import os, sys
    sys.path.append("..")
    sys.path.extend([os.path.join(root, name) for root, dirs, _ in os.walk("../") for name in dirs])
    from user_agents import getUA
from urllib.parse import unquote

config, db, log, lock = 0,0,0,0  #保存宿主传递的环境 分别为配置文件， 数据库，日志，全局线程锁
def _default_config(root, name): #返回默认配置文件 载入时被调用 root为数据文件根目录 name为当前模块名称
    return {
        'modInformation':{ #该模块的信息
            'Name': 'Search by Google',
            'Author': 'Limour @limour.top',
            'Version': '1.0',
            'description': '获取谷歌的搜索结果'
        },
        'Contab_Interval': 0, #不用执行
        'proxies': {
            'http':'http://127.0.0.1:1080', #http://user:password@host:port
            'https':'http://127.0.0.1:1080'
        },
        'headers': {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "max-age=0",
            "cookie": "CGIC=Inx0ZXh0L2h0bWwsYXBwbGljYXRpb24veGh0bWwreG1sLGFwcGxpY2F0aW9uL3htbDtxPTAuOSxpbWFnZS93ZWJwLGltYWdlL2FwbmcsKi8qO3E9MC44LGFwcGxpY2F0aW9uL3NpZ25lZC1leGNoYW5nZTt2PWIzO3E9MC45; ISSW=1; CONSENT=YES+BD.en+201909; SEARCH_SAMESITE=CgQIuJEB; 1P_JAR=2021-01-15-11; NID=207=KtcdqWrufgx8QD-bqsQbaIuE3fz3Xd_cTA6uCxNrk1gMeybZGgGz97wQDRaGbacyu77_ihltvUkLW4V-eZPL-mjrpLvd723L4mbDx3ToCPxwHL5loYHrQVNu4sorcRcDWrELdZKyl9iVyDJHnr_aWBoGMHaLThkbgafn7eH99pR0mgfKVrtdd8U0dM9SEpL4MvRwsnvmMjAfNqc",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1"
        }
    }

def _init(_config, _db, _log, _lock, m_name): #载入时被调用
    global config, db, log, lock
    config, log, lock = _config, _log, _lock #保存宿主传递的环境

def _contab():
    pass

def _exit():
    pass

def _showlxml(etr):
    if type(etr) is not list:
        if type(etr) is str:
            print (etr)
        else:
            t = etree.tostring(etr, encoding="utf-8", pretty_print=True)
            print(t.decode("utf-8"))
    else:
        for x in etr: _showlxml(x)

def getHtml(s, pid):
    url = f'https://www.google.com/search?q={s}&start={pid*10}'
    headers=config['headers']
    headers['user-agent'] = getUA()
    r = requests.get(url, headers=headers, proxies=config['proxies'], verify=False)
    if r.status_code != 200:
        log.debug('getHtml 网络错误')
        return
    r.encoding = 'utf-8'
    html= etree.HTML(r.text)
    return html

def getUrl(text:str):
    if text.startswith('/url?'):
        s = 7
        e = text.find('&', s)
        if e <= s:
            return f'https://www.google.com{text}'
        else:
            return unquote(text[s:e], 'utf-8')
    else:
        return text
def getText(el:list):
    res = []
    for x in el:
        x = x.strip()
        if x: res.append(x)
    return '_'.join(res)

def getR1(div):
    url = div.xpath('./div/div/div/div/a/@href')
    if len(url) == 1: url = getUrl(url[0])
    else:
        log.debug('getR1 len(url)错误')
        url = ""
    title = getText(div.xpath('./div/div/div/div/a//*/text()'))
    des = getText(div.xpath('./div/div/div/div/table//*/text()'))
    return url, title, des

def isRes(div):
    return len(div.xpath('./div/div/div/div/a')) == 1

def getRes(html):
    try:
        html = html.xpath(r'.//body/div')[1]
    except IndexError:
        log.error('getRes IndexError')
        #_showlxml(html)
        return []
    html = html.xpath(r'./div')
    res = [getR1(div) for div in html if isRes(div)]
    return res

def _search(s, pid):
    #[(标题,内容,注释,URL)]
    html = getHtml(s, pid)
    rl = getRes(html)
    return [(t, d, '引擎：Google', u) for u,t,d in rl]

if __name__ == '__main__':
    config = _default_config('', '')
    t = getHtml('为什么不出错', 0)
    _showlxml(t)
