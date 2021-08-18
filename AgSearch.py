#!/usr/bin/env python3
from flask import Blueprint, jsonify, render_template, request
from ModManager import ModManager
app = Blueprint('agsearch', __name__, url_prefix='/',
                template_folder='templates',
                static_folder='static',
                static_url_path='static'
                )

def _extend(resl):
    if not resl: return resl
    resl.sort(key=len, reverse=True)
    leh = tuple(map(len, resl))
    res = []
    for i in range(leh[0]):
        for j,l in enumerate(leh):
            if i < l: res.append(resl[j][i])
            else: break
    return res

Mod = ModManager('AgSearch')
AgInfo = Mod.getCall("_info")
AgSearch = Mod.getCall("_search")
def _info(pid):
    return _extend(Mod.Call(AgInfo, pid))
def _search(s, pid):
    return _extend(Mod.Call(AgSearch, s, pid))

@app.route('/api/info')
def info():
    pid = request.args.get('pid', 0, type=int)
    resl = _info(pid)
    return jsonify(resl)
@app.route('/')
def index():
    return render_template('index.html', url_api='/api/info', url_ls='', title='首页')

@app.route('/api/search')
def search():
    s = request.args.get('ls')
    pid = request.args.get('pid', 0, type=int)
    resl = _search(s, pid)
    return jsonify(resl)
@app.route('/results')
def results():
    s = request.args.get('s')
    return render_template('index.html', url_api='/api/search', url_ls=s, title=s)

server = Mod.getMod("webserver")
server.register_blueprint(app)
server.wait()