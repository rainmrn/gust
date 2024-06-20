import mutagen
import requests
import os
import setuptools
from base64 import b64encode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

path = './' # path to the music files
all_items = os.listdir(path)
audio_items = [
    mutagen.File(item, easy=True) 
    for item in all_items 
    if os.path.isfile(os.path.join(path, item)) and mutagen.File(item) != None
]

def get_access_token():
    # Spotify Client ID and Secret environment variables
    spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
    spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

    # Spotify Authoization using Client Credentials
    auth_url = "https://accounts.spotify.com/api/token"
    auth_headers = {'Authorization': f'Basic {b64encode(f'{spotify_client_id}:{spotify_client_secret}'.encode()).decode('utf-8')}'}
    auth_data = {'grant_type': 'client_credentials'}

    # Getting the access token for Spotify's API
    auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data)
    return auth_response.json().get('access_token')

def build_query(audio):
    if "title" in audio.tags and "artist" in audio.tags:
        # add album to query if it's available
        if "album" in audio.tags:
            query = f"https://api.spotify.com/v1/search?q={audio.tags["title"]}+-+{audio.tags["artist"]}+-+{audio.tags["album"]}&type=track" 
        # else use title and artist only
        else:
            query = f"https://api.spotify.com/v1/search?q={audio.tags["title"]}+-+{audio.tags["artist"]}&type=track" 
    # use filename for query as a last resort
    else:
        query = f"https://api.spotify.com/v1/search?q={audio.filename}&type=track"
    return query

def fetch_tracks(query, headers, only_first=False, limit=5):
    if only_first == True:
        limit = 1

    response = requests.get(query + f"&limit={limit}", headers=headers)
    data = response.json()

    if only_first == True:
        return data['tracks']['items'][0]
    return data["tracks"]["items"]

def get_total_tracks(track, headers):
    album_query = track['album']['href']
    response = requests.get(album_query, headers=headers)
    data = response.json()

    total_discs = data['tracks']['items'][-1]['disc_number']

    disc_num = track['disc_number']

    i = 0
    current_disc = data['tracks']['items'][i]['disc_number']
    while current_disc != disc_num:
        i += 1
        current_disc = data['tracks']['items'][i]['disc_number']
    
    total_tracks = 0
    while True:
        total_tracks += 1
        current_disc = data['tracks']['items'][i]['disc_number']
        if current_disc != disc_num or i >= len(data['tracks']['items']) - 1:
            break
        i += 1

    if total_discs != 1:
        total_tracks -= 1
    
    return total_tracks

def get_total_discs(track, headers):
    album_query = track['album']['href']
    response = requests.get(album_query, headers=headers)
    data = response.json()

    return data['tracks']['items'][-1]['disc_number']
    



def display_results(results):
    if isinstance(results, list):
        for i, result in enumerate(results):
            title = result['name']
            artists = []
            for artist in result['artists']:
                artists.append(artist['name'])
            
            album = result['album']['name']
            print(f"{i+1}. {title} by {', '.join(artists)} in album {album}")
    else:
        title = results['name']
        artists = []
        for artist in results['artists']:
            artists.append(artist['name'])
        
        album = results['album']['name']
        print(f"{title} by {', '.join(artists)} in album {album}")


# def main():
access_token = get_access_token()
fetch_headers = {'Authorization': f'Bearer {access_token}'}

auto_tag = input("Apply tags automatically? (choosing the first result) [Y/n]: ")
year_only = input("Use only the year for the album release date? [Y/n]: ")

if auto_tag.lower() in ['y', 'yes', '']:
    print("Applying tags automatically...")

    for audio in audio_items:

        print(f"Processing: {audio.filename}")

        query = build_query(audio)

        track = fetch_tracks(query, fetch_headers, only_first=True)

        print(f"title       : {track['name']}")
        print(f"album       : {track['album']['name']}")
        if year_only.lower() in ['y', 'yes', '']:
            print(f"date        : {track['album']['release_date'][:4]}")
        else:
            print(f"date        : {track['album']['release_date']}")
            
        if len(track['album']['artists']) > 1:
            albumartist = "Various Artists"
        else:
            albumartist = track['album']['artists'][0]['name']
        print(f"album artist: {albumartist}")

        total_tracks = get_total_tracks(track, fetch_headers)
        total_discs = get_total_discs(track, fetch_headers)

        print(f"track number: {track['track_number']}")  
        print(f"total tracks: {total_tracks}")
        print(f"disc number : {track['disc_number']}")  
        print(f"total discs : {total_discs}\n")
    
else:
    print("Manual tag selection...")

    for audio in audio_items:

        print(f"Processing: {audio.filename}")

        if "title" in audio.tags and "artist" in audio.tags:
            query = f"https://api.spotify.com/v1/search?q={audio.tags["title"]}+-+{audio.tags["artist"]}&type=track" 
            # add album to query if it's available
            if "album" in audio.tags:
                query = f"https://api.spotify.com/v1/search?q={audio.tags["title"]}+-+{audio.tags["artist"]}+-+{audio.tags["album"]}&type=track" 
        else:
            # use filename to search as a last resort
            query = f"https://api.spotify.com/v1/search?q={audio.filename}&type=track"

        tracks = fetch_tracks(query)

        print("Results:")
        # for track in tracks:

        display_results(tracks)
        print()

# if "__name__" == "__main__":
#     main()


    # title = tracks[0]['name']
    # print(f"track: {title}")

    # artists = []
    # for artist in tracks[0]['artists']:
    #     artists.append(artist['name'])
    # print(f"artists: {artists}")

    # album = tracks[0]['album']['name']
    # print(f"album: {album}")

    # if tracks[0]['album']['artists'].length > 1:
    #     albumartist = "Various Artists"
    # else:
    #     albumartist = tracks[0]['album']['artists'][0]
    # print(f"album artist: {albumartist}\n")
    
        

# tag = {
#     "artist": "Something",
#     "album": "Another Thing"
# }

# audio.tags['artist'] = "Something"
# audio.tags['albumartist'] = "Another Thing"
# audio.tags['album'] = "Best Album"
# audio.save()
# print(audio.tags)