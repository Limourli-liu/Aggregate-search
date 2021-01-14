from flask import Flask, jsonify, render_template, request
from ModManager import ModManager
app = Flask(__name__)
AgInfo = ModManager('AgInfo')

@app.route('/api/info')
def info():
    pid = request.args.get('pid', 0, type=int)
    resl = AgInfo.call('_info', pid)
    res = []
    for item in resl:
        res.extend(item)
    return jsonify(res)

@app.route('/')
def index():
    return render_template('index.html')

app.run(port=2021)
