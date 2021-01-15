from random import choice
import gzip

try:
    with gzip.open('./public/user_agents.txt.gz', 'rt', encoding='utf-8') as f:
        ual = f.readlines()
except FileNotFoundError:
    with gzip.open('user_agents.txt.gz', 'rt', encoding='utf-8') as f:
        ual = f.readlines()

def getUA():
    return choice(ual).rstrip()
