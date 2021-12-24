from flask import Flask, jsonify, render_template, request
import pymongo
from pymongo import MongoClient

import pandas as pd
import plotly
import plotly.graph_objects as go
import json
from scraping import scrap

app = Flask(__name__)

client = MongoClient(host="mongodb", port=27017)

def insert_db():

    db = client['football_db']
    years = [1213, 1314, 1415, 1516, 1617, 1718, 1819]

    for league in ['ligue1', 'premiereleague', 'seria', 'bundesliga', 'laliga']:
        db[league].drop()
        li = []
        for year in years:
            df = pd.read_csv(f"/app/data_to_insert/{league}/season-{year}_csv.csv", index_col=None, header=0)
            li.append(df)
        df_to_insert = pd.concat(li, axis=0, ignore_index=True)

        db[league].insert_many(df_to_insert.to_dict('records'))

    for league in ['championsleague', 'europaleague']:
        db[league].drop()
        df_to_insert = pd.read_csv(f"/app/data_to_insert/{league}.csv", index_col=None, header=0)

        db[league].insert_many(df_to_insert.to_dict('records'))


def get_db():
    db = client['football_db']
    return db

@app.route('/')
def ping_server():
    return "Welcome bro !"

@app.route('/callback', methods=['POST', 'GET'])
def cb():
    return get_strongest_club(request.args.get('data'))

@app.route('/football')
def fetch_sku():
    return render_template("football.html", graphJSON=get_strongest_club())

def get_strongest_club(ligue='ligue1'):

    db = get_db()

    if ligue == 'championsleague' or ligue == 'europaleague':
        strongest_clubs = db[ligue].aggregate([{"$group" : {"_id" : "$Team",
        "average_goals_by_comps" : {"$avg" : "$Goal"},
        "average_taken_goals_by_comps" : {"$avg" : "$Goal_against"},
        "average_matches_by_comps" : {"$avg" : "$Match_played"} }}])
        df = []
        for x in strongest_clubs:
            df.append([x['_id'], x['average_goals_by_comps'], x['average_taken_goals_by_comps'], x['average_matches_by_comps']])
        df = pd.DataFrame(df, columns = ['Club', 'average_goals_by_comps', 'average_taken_goals_by_comps', 'average_matches_by_comps'])
        df['average_goals'] = df['average_goals_by_comps']/df['average_matches_by_comps']
        df['average_taken_goals'] = df['average_taken_goals_by_comps']/df['average_matches_by_comps']
        df = df.sort_values(by=['average_goals'], ascending=False)
        fig = go.Figure(data=[
        go.Bar(name='Average Goals By Club', x=df['Club'][0:25], y=df['average_goals'][0:25]),
        go.Bar(name='Average Taken Goals By Club', x=df['Club'][0:25], y=df['average_taken_goals'][0:25])])
        fig.update_layout(barmode='group')
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    else:
        strongest_clubs = db[ligue].aggregate([{"$group" : {"_id" : "$HomeTeam",
        "average_goals_by_clubs" : {"$avg" : "$FTHG"},
        "average_taken_goals_by_clubs" : {"$avg" : "$FTAG"} }}])
        df = []
        for x in strongest_clubs:
            df.append([x['_id'], x['average_goals_by_clubs'], x['average_taken_goals_by_clubs']])
        df = pd.DataFrame(df, columns = ['Club', 'Average_Goals_By_Club', 'Average_Taken_Goals_By_Club']).sort_values(by=['Average_Goals_By_Club'], ascending=False)
        fig = go.Figure(data=[
        go.Bar(name='Average Goals By Club', x=df['Club'][0:25], y=df['Average_Goals_By_Club'][0:25]),
        go.Bar(name='Average Taken Goals By Club', x=df['Club'][0:25], y=df['Average_Taken_Goals_By_Club'][0:25])])
        fig.update_layout(barmode='group')
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


if __name__ == '__main__':
    scrap()
    insert_db()
    app.run(host='0.0.0.0', port=5000)