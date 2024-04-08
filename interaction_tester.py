import requests
from urllib.parse import urlencode
import base64
import webbrowser
import token_generator
import time
import random
import Game
# from flask_sqlalchemy import SQLAlchemy


try:
    import redis
    from flask import Flask, render_template, redirect, request, send_from_directory, flash, url_for, session
    import os, re, json, time
    from flask_session import Session
except:
    print("Not able to import all of the calls needed from the Flask library.")

app = Flask(__name__)

token = token_generator.fetch_token()

user_headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json"
    }

user_params = {
    #"limit": 50,
    "market": "US",
    "additional_types":["track"]
    }

listening = requests.get(f"https://api.spotify.com/v1/me/player", params=user_params, headers=user_headers)#.json()
assert listening.status_code == 200
device_id = listening.json()['device']['id']
print(f"Your Device is: {device_id}")

user_params['device_id'] = device_id
app.secret_key = 'BAD_SECRET_KEY'

# Configure Redis for storing the session data on the server-side
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')

# Create and initialize the Flask-Session object AFTER `app` has been configured
server_session = Session(app)


@app.route('/', methods =["GET", "POST"])
def game():
    if request.method == "POST":
        pass
    session['player'] = Game.PLAYER("player", user_headers, user_params)
    session['player'].page = "get_vote.html"
    session['player'].data['prompt'] = "The funkiest or skrillexist"

    session['player'].data['choice1'] = "Bangerang"
    session['player'].data['choice2'] = "Funkytown"

    return "go to /player_page"

@app.route('/player_page', methods =["GET", "POST"])
def player_page():
    if request.method == "POST":
        return "submission detected"
    
    return render_template(session['player'].page, data = session['player'].data)



if __name__ == '__main__':
    # run() method of Flask class runs the application locally
    app.run(debug=True) 
