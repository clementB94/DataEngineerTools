from flask import Flask, make_response, render_template, request
import pymongo
from pymongo import MongoClient

import pandas as pd
import plotly
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json

from scraping import scrap
from insert_db import insert_db

app = Flask(__name__)

client = MongoClient(host="mongodb", port=27017)


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

@app.route('/getPlotCSV/<ligue>', methods=['POST', 'GET'])
def dl(ligue):
    # Download a csv file with all rows in the mongodb document
    db = client['football_db']
    cursor = db[ligue].find()
    df =  pd.DataFrame(list(cursor))
    csv = df.to_csv(index=False)
    response = make_response(csv)
    cd = 'attachment; filename='+ligue+'.csv'
    response.headers['Content-Disposition'] = cd 
    response.mimetype='text/csv'

    return response

def get_strongest_club(ligue='ligue1'):

    db = get_db()

    if ligue == 'championsleague' or ligue == 'europaleague':
        strongest_clubs = db[ligue].aggregate([{"$group" : {"_id" : "$Team",
        "average_goals_by_comps" : {"$avg" : "$Goal"},
        "average_taken_goals_by_comps" : {"$avg" : "$Goal_against"},
        "matched_played" : {"$sum" : "$Match_played"},
        "average_matches_by_comps" : {"$avg" : "$Match_played"} }}])
        df = []
        for x in strongest_clubs:
            df.append([x['_id'], x['average_goals_by_comps'], x['average_taken_goals_by_comps'], x['average_matches_by_comps'], x['matched_played']])
        df = pd.DataFrame(df, columns = ['Club', 'average_goals_by_comps', 'average_taken_goals_by_comps', 'average_matches_by_comps', 'matched_played'])
        df['average_goals'] = df['average_goals_by_comps']/df['average_matches_by_comps']
        df['average_taken_goals'] = df['average_taken_goals_by_comps']/df['average_matches_by_comps']
        df = df.sort_values(by=['average_goals'], ascending=False)

        fig = make_subplots(rows=2, cols=1, vertical_spacing=0.1, specs=[[{"type": "bar"}], [{"type": "table"}]])
        fig.add_trace(go.Bar(name='Average Goals By Club', x=df['Club'][0:25], y=df['average_goals'][0:25]), row=1, col=1)
        fig.add_trace(go.Bar(name='Average Taken Goals By Club', x=df['Club'][0:25], y=df['average_taken_goals'][0:25]), row=1, col=1)
        fig.update_layout(barmode='group')

        fig.add_trace(go.Table(columnwidth=[40, 40, 40, 40, 40],
                                        header=dict(values=['Club', 'average_goals', 'average_taken_goals',
                                        'matched played', 'average match played by comps']),
                                        cells=dict(values=[df.Club, df.average_goals,
                                                           df.average_taken_goals, df.matched_played,
                                                           df.average_matches_by_comps])), row=2, col=1)
        fig.update_layout(
            height=1000,
            title_text="Best team of : " + str(ligue),
        )

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    else:
        strongest_clubs = db[ligue].aggregate([{"$group" : {"_id" : "$HomeTeam",
        "average_goals_by_clubs" : {"$avg" : "$FTHG"},
        "average_taken_goals_by_clubs" : {"$avg" : "$FTAG"} }}])
        df = []
        for x in strongest_clubs:
            df.append([x['_id'], x['average_goals_by_clubs'], x['average_taken_goals_by_clubs']])
        df = pd.DataFrame(df, columns = ['Club', 'Average_Goals_By_Club', 'Average_Taken_Goals_By_Club'])
        df['diff'] = df['Average_Goals_By_Club'] - df['Average_Taken_Goals_By_Club']
        df = df.sort_values(by=['diff'], ascending=False)
        fig = make_subplots(rows=2, cols=1, vertical_spacing=0.1, specs=[[{"type": "bar"}],[{"type": "table"}]])
        fig.add_trace(go.Bar(name='Average Goals By Club', x=df['Club'][0:25], y=df['Average_Goals_By_Club'][0:25]), row=1, col=1)
        fig.add_trace(go.Bar(name='Average Taken Goals By Club', x=df['Club'][0:25], y=df['Average_Taken_Goals_By_Club'][0:25]), row=1, col=1)
        fig.update_layout(barmode='group')

        fig.add_trace(go.Table(columnwidth=[45, 45, 45, 45],
                                        header=dict(values=['Club', 'average_goals_by_club', 'Average_Taken_Goals_By_Club', 'Goal difference']),
                                        cells=dict(values=[df.Club, df.Average_Goals_By_Club,
                                                           df.Average_Taken_Goals_By_Club, df['diff']])), row=2, col=1)

        fig.update_layout(
            height=1000,
            title_text="Best teams of : " + str(ligue),
        )

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


if __name__ == '__main__':
    scrap()
    insert_db()
    app.run(host='0.0.0.0', port=5000)