from random import choice
import gzip

if __name__ == '__main__':
    with gzip.open('user_agents.txt.gz', 'rt', encoding='utf-8') as f:
        ual = f.readlines()
else:
    try:
        with gzip.open('./public/user_agents.txt.gz', 'rt', encoding='utf-8') as f:
            ual = f.readlines()
    except FileNotFoundError:
        with gzip.open('../public/user_agents.txt.gz', 'rt', encoding='utf-8') as f:
            ual = f.readlines()
def isPC(ua):
    if "Android" in ua: return False
    if 'SymbianOS' in ua or 'Windows Phone' in ua: return False
    if 'iPhone' in ua:
        return 'iPad' in ua or 'PlayBook' in ua or 'Tablet' in ua
    return True

def getUA():
    res = choice(ual)
    while not isPC(res):
        res = choice(ual)
    return res.rstrip()
