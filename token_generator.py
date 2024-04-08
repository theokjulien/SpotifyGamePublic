import requests
from urllib.parse import urlencode
import base64
import webbrowser
import os
import os.path

filename = "token.txt"
f = open(filename, "r", encoding='utf-8')  #gets last token
token = f.read()
f.close()

client_id = "Client Id"
client_secret = "Client Secrete"

auth_headers = {
    "client_id": client_id,
    "response_type": "code",
    "redirect_uri": "http://localhost:7777/callback",
    "scope": "user-library-read user-read-currently-playing user-read-playback-state user-read-playback-position app-remote-control streaming user-modify-playback-state"
    
}

def get_token(t):
    try:
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
        print(listening)
        device_id = listening.json()['device']['id']
        print(device_id)
        return token
    
    except:
        webbrowser.open("https://accounts.spotify.com/authorize?" + urlencode(auth_headers))
        raw_url = input("Paste in the Redirect Url: ")
        code = raw_url.split("code=")[-1]
        encoded_credentials = base64.b64encode(client_id.encode() + b':' + client_secret.encode()).decode("utf-8")
        token_headers = {
            "Authorization": "Basic " + encoded_credentials,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://localhost:7777/callback"
        }

        r = requests.post("https://accounts.spotify.com/api/token", data=token_data, headers=token_headers)

        return r.json()["access_token"] # returns token


def fetch_token():
    new_token = get_token(token)
    if new_token == token:
        return token
    else:
        f = open(filename, "w", encoding='utf-8')
        f.write(new_token)
        f.close()
        return new_token


