from flask import Flask, jsonify
import pymongo
from pymongo import MongoClient

app = Flask(__name__)

def get_db():
    client = MongoClient("mongodb://192.168.1.10:27017/")
    db = client['sku_db']
    return db

@app.route('/')
def ping_server():
    return "Welcome bro !"

@app.route('/sku')
def fetch_sku():
    db = get_db()
    _sku = db.sku_tb.find()
    skus = [{"id": sku["id"], "name": sku["name"]} for sku in _sku]
    return jsonify({"skus": skus})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)