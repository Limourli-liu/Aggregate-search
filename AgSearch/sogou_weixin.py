import traceback, requests, time
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from lxml import etree

config, Manager, log, lock = 0,0,0,0  #保存宿主传递的环境 分别为配置文件， 模块管理器，日志，全局线程锁
def _default_config(root, name): #返回默认配置文件 载入时被调用 root为数据文件根目录 name为当前模块名称
    return {
        'modInformation':{ #该模块的信息
            'Name': 'Search by Sogou Weixin',
            'Author': 'Limour @limour.top',
            'Version': '1.0',
            'description': '获取搜狗微信的搜索结果'
        },
        'crontab_Interval': 0, #不用执行
        'headers': {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Cookie": "SUID=0BF5E38B6920A00A000000005F32B098; SUV=1597157530836586; usid=sDnAqJRUF4ZLOKW2; wuid=AAG4fV2tMAAAAAqgDEUzygAAkwA=; ssuid=3111235315; sw_uuid=8110520805; IPLOC=CN4313; ld=uZllllllll2kakBrlllllplmxu7lllllTi15mlllll9lllll9klll5@@@@@@@@@@; ABTEST=7|1614045346|v1; SNUID=37D95C1EC2C77936F54090D5C2904E27; weixinIndexVisited=1; JSESSIONID=aaa7KPEKV5nXU4AQc9TDx",
            "Host": "gzh.sogou.com",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"
        }
    }

def _init(m_name, _config, _Manager, _log): #载入时被调用
    global config, Manager, log, lock
    config, Manager, log, lock = _config, _Manager, _log, _Manager.threading_lock #保存宿主传递的环境

def _crontab():
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
    url = f'https://gzh.sogou.com/weixin?query={s}&_sug_type_=&s_from=input&_sug_=n&type=2&page={pid+1}&ie=utf8'
    headers=config['headers']
    r = requests.get(url, headers=headers, verify=False)
    if r.status_code != 200:
        log.debug('getHtml 网络错误')
        return
    r.encoding = 'utf-8'
    html= etree.HTML(r.text.encode('utf-8'))
    return html

def getUrl(u:str):
    if u.startswith('http'):
        return u
    elif u.startswith('//'):
        s = u.find('&url=')
        if s > 0:
            return  u[s+5:]
        else:
            return  u[2:]
    else:
        return 'https://gzh.sogou.com' + u

def getData(c0):
    text = c0.xpath(r'./div[@class="txt-box"]')
    text = text[0]
    #url
    u = getUrl(text.xpath(r'./h3/a/@href')[0])

    #title description 公众号
    t = ''.join(text.xpath(r'./h3//text()')).strip()
    s = ''.join(text.xpath(r'./p//text()')).strip()
    gzh = ''.join(text.xpath(r'./div[@class="s-p"]/a//text()')).strip()
    #time
    ti = ''.join(text.xpath(r'./div[@class="s-p"]/span//text()')).strip()
    ti_s = ti.find("timeConvert(") + 13
    ti_e = ti.find(")", ti_s) - 1
    ti = ti[ti_s: ti_e]
    timeArray = time.localtime(int(ti))
    ti = time.strftime(r"%Y-%m-%d", timeArray)

    # img
    img = c0.xpath(r'./div[@class="img-box"]/a/img/@src')
    if len(img) == 1:
        img = getUrl(img[0])
        s +=  f'<img src="{img}" style="height:85px"></img>' 
    else:
        img = text.xpath(r'./div[@class="img-d"]/a/span/img/@src')
        if len(img) > 0:
            for ig0 in img:
                s +=  f'<img src="{getUrl(ig0)}" style="height:85px"></img>' 
    d = f'引擎：搜狗微信 来源：{gzh} 时间：{ti}'
    return (t, s, d, u)

def _search(s:str, pid):
    #[(标题,内容,注释,URL)]
    html = getHtml(s, pid)
    if html is None:
        return []
    b = html.xpath(r'.//ul[@class="news-list"]')
    if len(b) != 1:
        log.debug('_search len(b) != 1')
        return []
    c = b[0].xpath('./li')
    res = []
    for c0 in c:
        try:
            res.append(getData(c0))
        except:
            log.error(traceback.format_exc())
    return res

if __name__ == '__main__':
    config = _default_config('', '')
    # t = getHtml('卫生统计学', 0)
    # _showlxml(t)
    with open('../test/test.html', 'rb') as f:
        t = etree.HTML(f.read())
    b = t.xpath(r'.//ul[@class="news-list"]')
    b = b[0]
    c = b.xpath('./li')
    c0 = c[5]
    # img = c0.xpath(r'./div[@class="img-box"]/a/img/@src')
    # img = img[0]
    # img = img[50+5:]
    # text = c0.xpath(r'./div[@class="txt-box"]')
    # text = text[0]
    # u = text.xpath(r'./h3/a/@href')[0]
    # u = 'https://gzh.sogou.com' + u
    # t = ''.join(text.xpath(r'./h3//text()')).strip()
    # d = ''.join(text.xpath(r'./p//text()')).strip()
    # gzh = ''.join(text.xpath(r'./div/a//text()')).strip()
    # ti = ''.join(text.xpath(r'./div/span//text()')).strip()
    # ti_s = ti.find("timeConvert(") + 13
    # ti_e = ti.find(")", ti_s) - 1
    # ti = ti[ti_s: ti_e]
    # timeArray = time.localtime(int(ti))
    # ti = time.strftime(r"%Y-%m-%d", timeArray)