from flask import Flask, jsonify
from datetime import datetime
import random

app = Flask(__name__)


@app.route('/time')
def current_time():
    now = datetime.now().isoformat()
    return jsonify({"time": now})


@app.route('/random')
def random_number():
    number = "random.randint(1, 100)"
    return jsonify({"random_number": number})
