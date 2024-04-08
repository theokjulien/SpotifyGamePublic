#import tkinter as tk
from tkinter import *
from PIL import Image, ImageTk
from urllib.request import urlopen
from io import BytesIO
import time

 #_______________________________main object to be used in other code________________________#
class GameFrame(Frame):
    def __init__(self, parent = None):
        '''Class that manages the game screen in the spotify game'''
        self.parent = parent
        self.frame = LabelFrame(parent)
        self.players = []
        self.waiting_room = None
        self.timer = None
    
    def resize(self):
        self.frame.config(width=700, height=400)

    def showSubmission(self, prompt, track):
        url = track.get_image()
        showsong = ShowSong(prompt, url, self.frame)
        self.frame.pack()
    
    def showScores(self, players):
        '''ranks the players by scores and displays the standings'''
        scores = Scores(players, self.frame)
        self.frame.pack()

    def waitForSubmissions(self):
        self.resize()
        self.timer = GetSubmissions("Waiting for Submissions: ", self.frame)
        self.frame.pack()

    def waitForVotes(self):
        self.resize()
        self.timer = GetSubmissions("Waiting for Votes: ", self.frame)
        self.frame.pack()
    
    def updateTimer(self):
        self.timer.update_clock()
        self.frame.pack()

    def addPlayer(self, player_name):
        '''addPlayers as they join the game lobby (only use while Lobby is active)'''
        self.waiting_room.add_player(player_name)
        self.frame.pack()
        
    def lobby(self, game_code):
        '''Page that displays the game code and all players currently in the lobby'''
        self.waiting_room = JoinGame(game_code, self.frame)
        self.frame.pack()

    def clear(self):
        '''Clears the game frame'''
        for widget in self.frame.winfo_children():
            widget.destroy()



# Skeletal player object for testing purposes
class testPlayer:
    def __init__(self, name, score):
        self.name = name
        self.score = score

class testTrack:
    def __init__(self, track_url):
        self.track_url = track_url

    def get_image(self):
        return self.track_url

#____________________________________TKINTER HELPER CLASSES_________________________________#
class Scores(Frame):
    
    def __init__(self,players,parent=None):
        '''Takes in a list of players and displays there scores'''
        self.parent = parent
        self.label = Label(parent, text="Player Scores")
        self.label.grid(row=0,column=0)
        scores = {player: player.score for player in players}
        scores = sorted(scores.keys(), reverse= True, key = lambda x:scores[x])
        for i, player in enumerate(scores):
            playerLabel = Label(parent, text = player.name)
            scoreLabel = Label(parent, text = str(player.score))
            playerLabel.grid(row = i+1, column = 0)
            scoreLabel.grid(row = i+1, column = 1)

class ShowSong(Frame):

    def __init__(self, prompt: str, url: str, parent = None) -> None:
        '''Takes in a prompt and the image of the track submission'''
        self.parent = parent
        self.label = Label(parent, text="The prompt was: " + prompt)
        self.label.pack()
        u = urlopen(url)
        raw_data = u.read()
        u.close()
        photo = ImageTk.PhotoImage(data=raw_data)

        label = Label(parent, image=photo)
        label.image = photo
        label.pack()

class GetSubmissions(Frame):

    def __init__(self, wait_message, parent = None, wait_time = 60) -> None:
        '''Takes in a wait message, a parent (default= None), and a wait_time (default = 60).
        Creates a frame with the message and the time left until submissions close.'''
        Frame.__init__(self, parent)
        self.wait_message = wait_message
        self.wait_time = wait_time
        self.start_time = time.time()
        self.parent = parent
        self.label = Label(parent, text="", font=("Helvetica", 30))
        self.label.place(x=50,y=80)
        self.update_clock()

    def update_clock(self):
        time_left = str(self.wait_time - int(time.time() - self.start_time))
        self.label.configure(text=self.wait_message + f'{time_left} seconds left')
        self.after(1000, self.update_clock)

class JoinGame(Frame):

    def __init__(self, game_code, parent = None):
        self.parent = parent
        self.title = Label(parent, text = "Spotify Beat Battles", font=("Helvetica", 70), fg = "light green")
        self.title.pack()
        self.label = Label(parent, text = "Game Code: " + game_code, font=("Helvetica", 30))
        self.label.pack()
        self.players = Label(parent, text = "Players in Lobby: ", font=("Helvetica", 18))
        self.players.pack()

    def add_player(self, player_name):
        player = Label(self.parent, text = player_name)
        player.pack()

class ShowWinner(Frame):

    def __init__(self, player1, player2, parent = None):
        self.player1, self.player2 = (player1, player2)
        self.parent = parent
        self.title = Label(parent, text = "VOTES ARE IN!", font=("Helvetica", 70), fg = "light green")
        self.title.pack()
        self.label = Label(parent, text = self.resultText(), font=("Helvetica", 30))
        self.label.pack()
    
    def resultText(self):
        if self.player1.votes == self.player2.votes:
            return f"{self.player1.name} and {self.player2.name} tied!"
        elif self.player1.votes > self.player2.votes:
            return f"{self.player1.name} won with {self.player1.song.name}!"
        else:
            return f"{self.player2.name} won with {self.player2.song.name}!"

#FOR TESTING
'''
import traceback
#______________________Testing Loop______________________#
main_root = Tk()
main_root.geometry("750x270")
main_root.title("Spotify Game Window")
main_screen = GameFrame(main_root)
players = [testPlayer("Player" + str(i + 1), i*100) for i in range(8)]
try:
    while True:

        # ____how to use .addPlayer()___
        a = input("What would you like to do: ")
        if a == "add player":
            name = input("Player name? ")
            main_screen.addPlayer(name)

        # ____how to use .lobby()____
        elif a == "lobby":
            main_screen.clear()
            main_screen.lobby("XXXX")

        # ____how to use .waitForVotes()_____
        elif a == "wait for votes":
            main_screen.clear()
            # make the call:
            main_screen.waitForVotes()
            # make a while loop and update the root and call .updateTimer()
            start = time.time()
            while time.time() - start < 60:
                main_screen.updateTimer()
                main_root.update_idletasks()
                main_root.update()
        
        # ____how to use .waitForSubmissions()_____
        elif a == "wait for submissions":
            main_screen.clear()
            # make the call:
            main_screen.waitForSubmissions()
            # make a while loop and update the root and call .updateTimer()
            start = time.time()
            while time.time() - start < 60:
                main_screen.updateTimer()
                main_root.update_idletasks()
                main_root.update()
        
        # ____how to use .showScores()_____
        elif a == "show scores":
            main_screen.clear()
            main_screen.showScores(players)

        # ____how to use .showSubmission()_____
        elif a == "show submission":
            main_screen.clear()
            prompt = input("what is the prompt?")
            track = testTrack("https://upload.wikimedia.org/wikipedia/en/thumb/a/a3/Phineas_and_Ferb_Soundtrack.jpg/220px-Phineas_and_Ferb_Soundtrack.jpg")
            main_screen.showSubmission(prompt, track)
        
        # ____how to use .clear()_____
        elif a == "clear":
            main_screen.clear()
        
        elif a == "quit":
            main_root.quit()
            break

        main_root.update_idletasks()
        main_root.update()

        #brief while loop for testing purposes
        # start = time.time()
        # while time.time() - start < 20:
        #     main_root.update_idletasks()
        #     main_root.update()

except Exception as e: # nice quit to not get ghost windows when an error is given
    main_root.destroy()
    print(traceback.format_exc())

'''
