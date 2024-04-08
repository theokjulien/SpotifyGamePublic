import requests
from urllib.parse import urlencode
import base64
import webbrowser
import token_generator
import time
import random
import Game

try:
    import redis
    from flask import Flask, render_template, redirect, request, send_from_directory, flash, url_for, session
    import os, re, json, time
    from flask_session import Session
except:
    print("Not able to import all of the calls needed from the Flask library.")

app = Flask(__name__)

#token = token_generator.fetch_token()
token = Game.token # hopefully will avoid double asking for tokens

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

player_names = [] # This will contain the names of everyone who's logged in
players = []
code = "xxxx"
app.game_open = True
app.start_time = time.time()
game_obj = Game.GAME()

# home login page
@app.route('/', methods =["GET", "POST"])
def gfg():
    if request.method == "POST":
        # getting input with name = fname in HTML form
        game_code = request.form.get("code")
        # getting input with name = lname in HTML form
        name = request.form.get("name")

        if (game_code == code):
            if name in player_names:
                return "Player name already taken"
            else:
                player_names.append(name)
                session['name'] = name
                session['player'] = Game.PLAYER(session['name'], user_headers, user_params)
                session['position'] = len(players)
                players.append(session['player'])
                game_obj.addPlayer(session['player'])
                session['last_page'] = ''
                assert session['player'] in game_obj.players
                #for testing purposesg
                # session['player'].submit("Here is a prompt") #_____TEST______#
                # return render_template(session['player'].page, data = session['player'].data)
                
                # session['player'].page_type = "search"
                return redirect(url_for('waiting_room'))
        else:
            return "Game Not Found"
    
    return render_template("join_game.html")

@app.route('/waiting_room', methods = ["GET", "POST"])
def waiting_room():
    if request.method == "POST": # if submission recieved from first player
        app.game_open = False # close game
        game_obj.createGame() # create a game with current players using the game object
        game_obj.play() # start game
        # return render_template("wait_updater.html")
        return redirect(url_for("game_in_progress"))
    try:
        name = session['name']
        #if app.game_open:
        if name in player_names:
            #if app.game_open:
            # return f"Hi {name} the game will start when {players[0]} says everyones in."
            # yield f"Hi {name} the game will start when {players[0]} says everyones in."
            return render_template("wait_updater.html")
            # else:
            #     return "why did you get here . . . idk"
        else:
            #return redirect(url_for('/'))
            return "Sign in again"
    except:
        return "Please join a game"

@app.get("/game_state")
def game_status(): # updated periodically by wait_updater
    if app.game_open:
        name = session['name']
        if name == player_names[0]:
            return render_template("start_game.html")
        else:
            return "party leader needs to start the game" + " ." * (int((time.time() - app.start_time)*2) % 4)
    else:
        try:
            print(session['name'] + " is updating")
            return redirect(url_for("game"))
            # return render_template("game_updater.html") # returns the actual game page
        except:
            return f"You can no longer join this game."
        
        
@app.route("/game_in_progress")
def game_in_progress():
    try:
        session['player']
        return render_template("game_updater.html")
        # return render_template("game_updater.html") # returns the actual game page
    except:
        return "You can no longer join this game."

@app.route('/game', methods = ["GET", "POST"]) # runs the actual game once it has begun, it is actively updated for players
def game():
    try:
        session['player'] = players[session['position']]
    except:
        return "You can no longer join this game."
    # return "made it to /game"
    if request.method == "POST":
        # session['last_page'] = "" # reset the last page to ensure an update (REMOVE if this not fix)
        # what type of response should we send
        response_type = session['player'].page_type
        # response_type = players[session['position']].page_type
        sbutton = request.form['submit_button']
        # is the player on a search page when they submitted
        if response_type == "search" or response_type == "prompt":
            print("search/prompt response detected")
            if sbutton == "search":
                session['player'].search(request.form.get("search"))
                # session['player'].wait("Waiting for everyone to submit")
                return redirect(url_for("waiting_room")) # this avoids the problem of taking the player out of the updating page
                return render_template(session['player'].page, data = session['player'].data)
            else:
                #if the search button was not hit it means they selected a song
                choice = int(sbutton) #get number of song choice
                # session['player'].song = session['track_list'][choice] #get track
                tracks = session['player'].tracks
                track_selection = tracks[int(choice)-1]
                print(f"The player selected{track_selection['name']}")
                session['player'].song = Game.TRACK(track_selection['id'], track_selection['name'], track_selection['artists'],5) # 5 is the start time rn
                session['player'].song_ready = True
                print(f"The song in the obj: {players[session['position']].song.name}" )
                session['player'].wait("Waiting for everyone to submit")
                return redirect(url_for("waiting_room"))
                return render_template(session['player'].page, data = session['player'].data)

        elif response_type == "vote":
            choice = int(sbutton)
            session['player'].voted_for = choice
            session['player'].voted = True
            session['player'].wait("waiting for everyone to vote")
            return redirect(url_for("waiting_room"))
            return render_template(session['player'].page, data = session['player'].data)

    else: # the player object will provide the needed page
        if needs_update(): # only update the page if needed
            session['last_page'] = session['player'].page
            return render_template(session['player'].page, data = session['player'].data)
        pass

@app.route("/update?")
def needs_update():
    if app.game_open:
        return 1
    return int(session['last_page'] != session['player'].page or session['player'].page_type == 'wait')

@app.route("/player_page")
def player_page():
    try:
        player = players[session['position']]
        return player.page + player.page_type

    except:
        return "No player object detected"


if __name__ == '__main__':
    # run() method of Flask class runs the application locally
    app.run(debug=True) 





