 #!/usr/bin/env python
from flask import Flask, jsonify, render_template, request
from ModManager import ModManager
app = Flask(__name__)

def _extend(resl):
    res = []
    for item in resl:
        res.extend(item)
    return res
AgInfo = ModManager('AgInfo')
@app.route('/api/info')
def info():
    pid = request.args.get('pid', 0, type=int)
    resl = AgInfo.call('_info', pid)
    return jsonify(_extend(resl))
@app.route('/')
def index():
    return render_template('index.html', url_api='/api/info', url_ls='')

AgSearch = ModManager('AgSearch')
@app.route('/api/search')
def search():
    s = request.args.get('ls')
    pid = request.args.get('pid', 0, type=int)
    resl = AgSearch.call('_search', s, pid)
    return jsonify(_extend(resl))
@app.route('/results')
def results():
    s = request.args.get('s')
    return render_template('index.html', url_api='/api/search', url_ls=s)

app.run(host='0.0.0.0', port=2021)
