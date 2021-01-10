import requests, traceback
from lxml import etree
from pubilc.summary import getSummary

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
        res.append((d, t, f"http://www.jwc.fudan.edu.cn{u}"))
    return res
    #return etree.tostring(r,encoding='utf-8').decode('utf-8')

def getItem(item):
    r = requests.get(item[2])
    r.encoding = 'utf-8'
    html = etree.HTML(r.text)
    html = html.xpath('.//*/text()')
    text = []
    for st in html:
        st = st.strip()
        if st: text.append(st)
    s = text.index('通知公告') + 1
    e = text.index('快速链接', s)
    #print(text[s:e])
    text = ''.join(text[s:e])
    sumy = getSummary(text)
    return (item[0], item[1], sumy,item[2])

def _start(conf, db):
    return ('Limour', '复旦大学教务处通知', '1.0', '从复旦大学教务处网站获取通知推送。本人博客：limour.top')

def _exit():
    pass

def _contab():
    pass

def _info(pid):
    #[(标题,内容,注释,URL)]
    pid += 1 #改为从1开始
    try:
        al = getList(pid)
    except:
        traceback.print_exc()
        return []
    res = []
    for item in al:
        try:
            d,t,s,u = getItem(item)
        except:
            d,t,u = item
            s = '该内容需要登录才能获取摘要，请打开网页查看详细内容！'
            traceback.print_exc()
        res.append((t, s, f'来源：复旦教务处 时间：{d}', u))
    return res
