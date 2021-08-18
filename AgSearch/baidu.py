import traceback, re
from lxml import etree
try:
    from public.baiduspider import BaiduSpider
except:
    import os, sys
    sys.path.append("..")
    sys.path.extend([os.path.join(root, name) for root, dirs, _ in os.walk("../") for name in dirs])
    from baiduspider import BaiduSpider

config, Manager, log, lock = 0,0,0,0 #保存宿主传递的环境 分别为配置文件， 模块管理器，日志，全局线程锁
def _default_config(root, name): #返回默认配置文件 载入时被调用 root为数据文件根目录 name为当前模块名称
    return {
        'modInformation':{ #该模块的信息
            'Name': 'Search by Baidu',
            'Author': 'Limour @limour.top',
            'Version': '1.0',
            'description': '获取百度的搜索结果'
        },
        'crontab_Interval': 0, #不用执行
        'Cookie': 'BIDUPSID=CA16753CF20338F61EFF2308D75FD378; PSTM=1610690081; BAIDUID=CA16753CF20338F6B2F0E1BEB8012DB7:FG=1; delPer=0; BD_CK_SAM=1; PSINO=6; H_PS_PSSID=33425_33466_33358_33259_33344_31254_33286_33414_26350; BD_UPN=12314753; H_PS_645EC=7537lWQ5t2PgtXC38yxw3ryuLYY7rT9I4Etn%2F9E%2BnTSJosnALJXW66DITPs; BA_HECTOR=8g2180048laka020i61g02bh40r; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598'
    }

Baidu = 0
def _init(m_name, _config, _Manager, _log): #载入时被调用
    global config, Manager, log, lock
    config, Manager, log, lock = _config, _Manager, _log, 0 #保存宿主传递的环境
    global Baidu
    Baidu = BaiduSpider(cookie=config['Cookie'])

def _patch_tieba(tag):
    html = etree.HTML(str(tag))
    html = html.xpath('.//div[@tpl="tieba_general"]')[0]
    item = {}
    item['url'] = html.xpath(r'./@mu')[0]
    item['title'] = html.xpath(r'.//h3/a/em/text()')[0] + "吧"
    item["cover"] = r'https://gss3.bdstatic.com/84oSdTum2Q5BphGlnYG/timg?wapp&quality=80&size=b150_150&subsize=20480&cut_x=0&cut_w=0&cut_y=0&cut_h=0&sec=1369815402&srctrace&di=49f718fd25f2bad0e939d45cb78a0493&wh_rate=null&src=http%3A%2F%2Fimgsrc.baidu.com%2Fforum%2Fpic%2Fitem%2F826f3b10b912c8fcacd52597f5039245d78821af.jpg'
    item["des"] = '百度贴吧——全球最大的中文社区。'
    tmp = html.xpath(r'.//div[@class="c-font-normal"]')[0]
    tmp = tmp.xpath(r'./span/span/text()')
    item["total"] = tmp[1]
    item["followers"] = tmp[0]
    hot = []
    for x in html.xpath(r'.//div'):
        tmp = x.xpath(r'./@class')
        if len(tmp) == 0: continue
        tmp = tmp[0]
        if 'c-row' not in tmp: continue
        h = {}
        h['title'] = x.xpath(r'.//a/text()')[0]
        h['url'] = x.xpath(r'.//a/@href')[0]
        x = x.xpath(r'./div/span/span/text()')
        h["clicks"] = x[0]
        h["replies"] = x[1]
        hot.append(h)
    item['hot'] = hot
    return item

_p_o = re.compile(r'\..+}')
def _patch_origin(origin):
    if origin is None: return ''
    return _p_o.sub('', origin)

def ha(url, des=None):
    return f'<a href="{url}" target="_blank">{des}</a>'
def hpic(url):
    return f'<img src="{url}" style="height:85px"></img>'
def hdiv(html):
    return f'<div>{html}</div>'

def getSong(x):
    album = x['album']
    singer = x['singer']
    song = x['song']
    if album: album = ha(album['url'], album['name'])
    if singer: singer = '/'.join(ha(item['url'], item['name']) for item in singer)
    if song:song = hpic(song['poster']) + ha(song['url'], song['name'])
    return hdiv(f'{song}\t{singer}\t{album}')


def _search(s, pid):
    #[(标题,内容,注释,URL)]
    tmp = Baidu.search_web(query=s, pn=pid+1)
    res = []
    for item in tmp.plain:
        try:
            if item['type'] == 'result':
                t = item['title']
                s = item['des']
                d = f'引擎：Baidu 来源：{_patch_origin(item["origin"])} 时间：{item["time"]}'
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
                    d = f'引擎：Baidu 来源：{_patch_origin(news["author"])} 时间：{news["time"]}'
                    u = news['url']
                    res.append((t, s, d, u))
            elif item['type'] == 'video':
                for video in item['results']:
                    t = video['title']
                    if video["cover"] is not None:
                        s = hpic(video["cover"])
                    else:
                        s = video['des']
                    d = f'引擎：Baidu 来源：{_patch_origin(video["origin"])} 时长：{video["length"]}'
                    u = video['url']
                    res.append((t, s, d, u))
            elif item['type'] == 'baike':
                item = item['result']
                t = item['title']
                if item["cover-type"] is None:
                    s = item['des']
                elif item["cover-type"] == 'image':
                    s = hpic(item["cover"]) + item['des']
                elif item["cover-type"] == 'video':
                    #s = f'<iframe src="{item["cover"]}" style="width: 100%;height: 100%;object-fit: cover;"></iframe>' + item['des']
                    #s = f'<video controls="controls" autoplay="autoplay" style="width: 100%;height: 100%;object-fit: cover;"><source src="{item["cover"]}"/></video>' + item['des']
                    s = ha(item["cover"], "点击下载视频") + item['des']
                d = f'引擎：Baidu 来源：百度百科'
                u = item['url']
                res.append((t, s, d, u))
            elif item['type'] == 'tieba':
                item = item['result']
                if type(item) is not dict:
                    log.debug('tieba patch')
                    item = _patch_tieba(item)
                t = item.get('title')
                #log.debug(item)
                s = hdiv(hpic(item["cover"]) + item["des"])
                d = f'引擎：Baidu 来源：贴吧 帖数：{item["total"]} 关注：{item["followers"]}'
                u = item['url']
                hot = ''
                for x in item['hot']:
                    hot = f'{x["title"]}_{x["clicks"]}_{x["replies"]}' 
                    hot = hdiv(ha(x["url"], hot))
                    s += hot
                res.append((t, s, d, u))
            elif item['type'] == 'blog':
                item = item['result']
                t = item['title']
                u = item['url']
                d = f'引擎：Baidu 来源：博客'
                s = ''
                blogs = ''
                for x in item['blogs']:
                    bolgs = '_'.join(x['tags'])
                    bolgs = f'{x["title"]}_{x["des"]}_{x["origin"]}_{bolgs}'
                    bolgs = hdiv(ha(x["url"], bolgs))
                    s += bolgs
                res.append((t, s, d, u))
            elif item['type'] == 'gitee':
                item = item['result']
                t = item['title']
                u = item['url']
                d = f'引擎：Baidu 来源：Gitee'
                s = f'{item["des"]} {item["star"]}_{item["fork"]}_{item["watch"]}_{item["license"]}_{item["lang"]}_{item["status"]}'
                res.append((t, s, d, u))
            elif item['type'] == 'music':
                item = item['result']
                t = item['title']
                u = item['url']
                d = f'引擎：Baidu 来源：音乐'
                s = ''
                for x in item['songs']:
                    s += getSong(x)
                res.append((t, s, d, u))
            elif item['type'] == 'related' and pid == 0:
                t = '相关搜索'
                u = 'https://www.baidu.com/'
                d = f'引擎：Baidu 来源：百度'
                s = item['results']
                s = '\t'.join(s)
                res.append((t, s, d, u))
        except:
            log.error(traceback.format_exc())
    return res

if __name__ == '__main__':
    _init(0, _default_config(0,0), 0, 0)
    #a = t.search_web(query='异度侵入', pn=1)
    #a = Baidu.search_web(query='潮汐 歌曲', pn=1)
    print(_search('潮汐 歌曲', 0))
