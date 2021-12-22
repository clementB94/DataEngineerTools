from flask import Flask, jsonify, render_template, request
import pymongo
from pymongo import MongoClient

import pandas as pd

app = Flask(__name__)

client = MongoClient(host="mongodb", port=27017)

def insert_db():
    db = client['football_db']
    years = [1213, 1314, 1415, 1516, 1617, 1718, 1819]
    for league in ['ligue1', 'premiereleague']:
        db[league].drop()
        li = []
        for year in years:
            df = pd.read_csv(f"/app/data_to_insert/{league}/season-{year}_csv.csv", index_col=None, header=0)
            li.append(df)
        df_to_insert = pd.concat(li, axis=0, ignore_index=True)

        db[league].insert_many(df_to_insert.to_dict('records'))


def get_db():
    db = client['football_db']
    return db

@app.route('/')
def ping_server():
    return "Welcome bro !"

@app.route('/football')
def fetch_sku():
    mofc, mdfc = get_mofc_mdfc('ligue1')
    moec, mdec = get_mofc_mdfc('premiereleague')
    return render_template("football.html", mofc = mofc, mdfc = mdfc, moec = moec, mdec = mdec)


def get_mofc_mdfc(ligue):

    db = get_db()

    most_offensive_french_clubs = db[ligue].aggregate([{"$group" : {"_id" : "$HomeTeam", "average_goals_by_clubs" : {"$avg" : "$FTHG"}}},
     {"$sort" : {"average_goals_by_clubs" : -1}}])
    moc = []
    for x in most_offensive_french_clubs:
        moc.append([x['_id'], x['average_goals_by_clubs']])

    most_deffensive_french_clubs = db[ligue].aggregate([{"$group" : {"_id" : "$HomeTeam", "average_goals_by_clubs" : {"$avg" : "$FTAG"}}},
     {"$sort" : {"average_goals_by_clubs" : 1}}])
    mdc = []
    for x in most_deffensive_french_clubs:
        mdc.append([x['_id'], x['average_goals_by_clubs']])

    return moc, mdc


if __name__ == '__main__':
    insert_db()
    app.run(host='0.0.0.0', port=5000)