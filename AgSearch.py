from flask import Flask, jsonify, render_template, request
import AgInfo
app = Flask(__name__)

@app.route('/api/info')
def info():
    pid = request.args.get('pid', 0, type=int)
    res = AgInfo._info(pid)
    return jsonify(res)

@app.route('/')
def index():
    return render_template('index.html')

app.run(port=2021)
