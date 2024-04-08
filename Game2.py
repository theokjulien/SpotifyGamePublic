import time
import random
import requests
from urllib.parse import urlencode
import token_generator
from IPython.display import clear_output
import game_screen

try:
    from flask import Flask, render_template, redirect, request, send_from_directory, flash, url_for, session
    import os, re, json, time
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
prompts = ["One minute of this song is too long!", "The world is ending!", "Play this at my funeral. . .", 
"This goes crazy in the Vatican . . .", "I had to issue an apology for playing this at the PTA meeting . . .",
"Your uncle's favorite song", "Grandma was high-key hittin it to this . . .", "👊", "👨🏼‍💼", 
"Certified Elementary School fun-run banger . . .", "Critics won't admit it but this shaped music history forever.",
"2am panic attack typa beat", "I'm convinced this wasn't made by a real person.", "My dad says this is real music",
"Tucker Carlson hates that he kinda likes this song.", "This song has been proven to cause brain damage",
"👹👹👹👹", "Meth in mp3 form.", "I was shocked when I heard this will be the next World Cup song.", 
"Hmm . . . it's definitely interesting.", "The prosecution submited this as evidence at my trial . . . I'm screwed :(",
"My therapist was concerned to see this on my playlist", "Over hated and underated", "This song is just a good time",
"The only song on a playlist I call 'To all the tiny cameras hidden in my house by the government.'", "Just a good song",
"Late night drive", "Fire lyrics", "Y2k", "Contains 'smooth' in the lyrics or title", "The best song that the voters have never heard",
"Play a song with a charismatic vocalist", "Best show intro song", "This song does the most with the least", "🎶🎷", 
"No one else is writing songs about this"]

# functions for deciding round pairings
from itertools import combinations
def first_pair(pairs, not_used, item):
    '''returns the first pair that includes item and none of the items in used'''
    for pair in pairs:
        if item in pair:
            if pair[pair.index(item) - 1] in not_used: #other item is unused
                return pair

def rounds_create(players, n_rounds):
    '''creates the round pairings for a game'''
    all_pairs = list(combinations(players,2))
    random.shuffle(all_pairs)
    rounds = []
    for r in range(n_rounds):
        #used_players = []
        not_used = players.copy()
        pairs = []

        for i in range(len(players)//2):
            player = not_used[0]
            #print(f"{not_used=}")
            pair = first_pair(all_pairs, not_used, player)
            if not(pair): #if there wasn't a pair then we need to restart
                return rounds_create(players, n_rounds) #brute force :)
            not_used.remove(pair[0])
            not_used.remove(pair[1])

            
            all_pairs.remove(pair)

            pairs.append(pair)
            #print(pair)
        
        rounds.append(pairs)
    
    return rounds

# considering not using a game class. . . I don't think they can be used for flask functions
from tkinter import *
root = Tk()
root.geometry("750x270")
root.title("Spotify Game Window")
screen = game_screen.GameFrame(root)

class GAME:
    '''class controlling a game of our jackbox style beatbattle'''
    def __init__(self, game_code = "XXXX", players = [], nrounds = 3):
        self.screen = screen
        self.game_code = game_code
        self.screen.clear()
        self.screen.lobby(game_code)
        root.update_idletasks()
        root.update()
        self.game_ready = False
        self.prompts = prompts.copy()
        self.nplayers = len(players)
        self.player_names = [player.name for player in players]
        self.players = players
        self.nrounds = nrounds
        self.access_token = token #access_token
        self.user_headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": "application/json"
        }
        
        self.user_params = {
        #"limit": 50,
        "market": "US",
        "additional_types":["track"]
        }
        #TODO: way of getting players ========================================

        # self.players = [PLAYER(input(f"Player{i+1} name?"), self.user_headers, self.user_params) for i in range(nplayers)]
        # self.player_names = [player.name for player in self.players]
        self.rounds = rounds_create(self.players, nrounds)
        self.r = 1 #round number
        self.battles = []
        self.defaultTrack = "1S7mumn7D4riEX2gVWYgPO" # track that will be submitted a player doesnt submit in time

        # print("Starting game with: " + ", ".join(self.player_names[:-1]) + ", and " + self.player_names[-1])

        # status = requests.get(f"https://api.spotify.com/v1/me/player", params=self.user_params, headers=self.user_headers)#.json()
        # assert status.status_code == 200, f"Response code was {status.status_code}: {status.reason}. Not 200"
        # status = status.json()
        # print(f"Playing music on {status['device']['name']}")
        # self.device_id = status['device']['id']

        self.pairs = self.players.copy()
        random.shuffle(self.pairs)
    
    def addPlayer(self, player):
        self.screen.addPlayer(player.name)
        root.update_idletasks()
        root.update()
        self.players.append(player)
    
    def createGame(self):
        self.__init__(self.game_code, self.players)
        print("Starting game with: " + ", ".join(self.player_names[:-1]) + ", and " + self.player_names[-1])
        self.game_ready = True
        

    def get_submissions(self):
        '''distributes the prompts to all players and recieves their submissions'''
        random.shuffle(self.prompts)
        self.battles = self.rounds[self.r - 1]
        for i in range(len(self.battles)):
            self.battles[i][0].submit(self.prompts[i]) #makes players select a song
            self.battles[i][1].submit(self.prompts[i])

            self.battles[i] = (self.battles[i][0], self.battles[i][1], self.prompts[i]) #adds the prompt to the tuple
        self.prompts = self.prompts[len(self.battles):] #removes the prompts from the pool
    
    def wait_for_submissions(self):
        self.screen.clear()
        self.screen.waitForSubmissions()
        start_time = time.time()
        submission_states = [player.song_ready for player in self.players]
        while (time.time() - start_time) < 60 and (False in submission_states):
            time.sleep(.1)
            self.screen.updateTimer()
            root.update_idletasks()
            root.update()
            submission_states = [player.song_ready for player in self.players]

        for player in self.players:
            if not(player.song_ready):
                player.song = self.defaultTrack
    
    def wait_for_votes(self, voters):
        self.screen.clear()
        self.screen.waitForVotes()
        start_time = time.time()
        submission_states = [votie.voted for votie in voters] #fix
        while (time.time() - start_time) < 60 and (False in submission_states):
            time.sleep(.1)
            self.screen.updateTimer()
            root.update_idletasks()
            root.update()
            submission_states = [votie.voted for votie in voters]
        
    def play(self):
        while self.r <= self.nrounds:
            self.play_round()
            self.r+=1
            time.sleep(5)
        self.screen.showScores(self.players)
        root.update_idletasks()
        root.update()
        time.sleep(5)
        screen.clear()
        root.quit()


    def play_round(self):
        '''Runs through entire round'''
        print()
        print(f"Round {self.r}:\nNew prompts have been sent, submit your songs!")
        self.get_submissions()
        self.wait_for_submissions()
        clear_output(wait=True)

        for battle in self.battles:
            self.battle(battle)
            time.sleep(10)
            clear_output(wait=False)
        
        self.screen.clear()
        self.screen.showScores(self.players)
        root.update_idletasks()
        root.update()
        
        


    def battle(self, battle):
        '''plays both tracks provided by players and then prompts voting'''
        player1, player2, prompt = battle
        # print("The prompt is:")
        # print(prompt)
        # time.sleep(5)
        # print("playing first submission: " + player1.song.name)
        self.screen.showSubmission(prompt, player1.track)
        player1.song.play(self.user_headers, device_id)
        time.sleep(1)
        self.screen.showSubmission(prompt, player2.track)
        player2.song.play(self.user_headers, device_id)
        print()
        print("VOTING TIME!")
        self.get_votes(battle)

        

    def get_votes(self, battle):
        '''prompts spectating players to vote on the tracks, prints the votes and the winner. 
        Also updates scores'''
        player1, player2, prompt = battle
        track1, track2 = (player1.song, player2.song)
        voters = list(set(self.players) - {player1, player2})
        print(f"Voters are {voters[0].name} and {voters[1].name}")
        for voter in voters:
            voter.vote(prompt, track1, track2)
        
        self.wait_for_votes(voters)
        results = [voter.voted_for for voter in voters]
        player1.votes = results.count(1)
        player1.score += player1.votes * 100
        player2.votes = results.count(2)
        player2.score += player2.votes * 100
        # print(f"{track1.name} recieved {player1.votes} votes")
        # print(f"{track2.name} recieved {player2.votes} votes")
        # print()
        self.screen.clear()
        self.screen.showWinner(player1, player2)
        player1.votes, player2.votes = (0,0)

#each session should have its own player instance
class PLAYER:
    '''player controller class'''
    def __init__(self, name, user_headers, user_params):
        self.page_type = "wait"
        self.name = name
        self.score = 0
        self.votes = 0
        self.voted_for = None
        self.song_ready = False
        self.voted = False
        self.song = TRACK("6rKCY6f6sJ6gyLjbrFTTs0",'Did not submit enjoy white noise','')
        self.user_headers = user_headers
        self.user_params = user_params
        self.data = {"name" : self.name, "wait_reason" : "submissions to be sent out"}
        self.tracks = []
        self.page = "wait.html"
    
    def wait(self, reason):
        self.data["wait_reason"] = reason
        self.page = "wait.html"
        self.page_type = "wait"
        


    def submit(self, prompt):
        self.song_ready = False
        self.page_type = "search"
        self.data["prompt"] = prompt
        self.page = 'prompt.html'

        # '''allows the player to submit a song to their battle'''
        # #clear_output(wait=True)
        # print(f"Pass the computer to {self.name}")
        # input(f"Press ENTER to begin submissin:")

        # print(f'{self.name} your prompt is: \n{prompt}')
        # time.sleep(.5)
        # search = input(f'What song are you thinking {self.name}?')
        # self.search(search)
        # self.song_ready = True

    def vote(self, prompt, track1, track2):
        '''allows player to vote on the winner of the beat battle'''
        #return input(f"{self.name} which better fit?\n (1) {track1.name}\n (2) {track2.name}")
        self.voted = False
        self.data["prompt"] = prompt
        self.data["choice1"] = track1.name
        self.data["choice2"] = track2.name
        self.page = "get_vote.html"
        self.page_type = "vote"

    def search(self, search):
        '''allows player to search a phrase and recieve the top five tracks to choose from'''

        self.user_params["limit"] = 5
        self.user_params["market"] = "US"
        self.user_params["q"] = search
        self.user_params["type"] = "track"

        result = requests.get(f"https://api.spotify.com/v1/search", params=self.user_params, headers=self.user_headers)
        assert result.status_code == 200, f"Response code was {result.status_code}: {result.reason}. Not 200"
        self.tracks = result.json()['tracks']['items']
        #print(self.tracks)
        #print("Search Results:")
        songs = []
        for i in range(5):
            songs.append(f"({i+1}) {self.tracks[i]['name']} by {', '.join([artist['name'] for artist in self.tracks[i]['artists']])}")
        self.data["tracks"] = songs
        self.page = "search_result.html"
        self.page_type = "search"
        return

class BOT:
    #bot player that will fill in when there are odd numbers of players
    pass

class TRACK:
    '''class to represent a spotify track/submissions from user'''
    def __init__(self,id, name, artists,start_time = 5):
        #print("track has been initialized")
        self.id = id
        self.start_time = start_time
        self.user_params = {"uri":"spotify:track:" + id}
        self.name = name + ' ' +', '.join([artist['name'] for artist in artists])
        self.play_time = 10 # CHANGE TO 30 or higher for actual game

    def get_image(self):
        '''returns the track cover url'''
        #return("WERE WORKING ON IT")
        image_url = requests.get(f"https://api.spotify.com/v1/tracks/{self.id}", params=user_params, headers=user_headers)
        assert image_url.status_code == 200, f"Response code was {image_url.status_code}: {image_url.reason}. Not 200"
        return image_url.json()["album"]["images"][0]["url"]

    def play(self, user_headers, device_id):
        '''plays 60 seconds of track starting at start_time'''
        self.user_params['device_id'] = device_id,
        self.user_params ["position_ms"] = self.start_time * 1000
        
        #add to queue
        add_queue = requests.post(f"https://api.spotify.com/v1/me/player/queue?", params=self.user_params, headers=user_headers)
        assert add_queue.status_code == 204, f"Response code was {add_queue.status_code}: {add_queue.reason}. Not 204"

        next = requests.post(f"https://api.spotify.com/v1/me/player/next", params=self.user_params, headers=user_headers)
        assert next.status_code == 204, f"Response code was {next.status_code}: {next.reason}. Not 204"

        # play = requests.put(f"https://api.spotify.com/v1/me/player/play", params=user_params, headers=user_headers)
        # assert play.status_code == 204

        if bool(self.start_time):
            skip = requests.put(f"https://api.spotify.com/v1/me/player/seek", params=self.user_params, headers=user_headers)
            #print(skip)
            assert skip.status_code == 204, f"Response code was {skip.status_code}: {skip.reason}. Not 204"
        

        time.sleep(self.play_time) #let song play

        pause = requests.put(f"https://api.spotify.com/v1/me/player/pause", params=self.user_params, headers=user_headers)
        assert pause.status_code == 204, f"Response code was {pause.status_code}: {pause.reason}. Not 204"
        
  