from flask import Flask, request, url_for, session, redirect, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import sys
import pandas as pd
import math
import matplotlib.pyplot as plt 
import seaborn as sns 
from io import BytesIO
import base64


app = Flask(__name__)

clientID = '65d88f8d3c8d409da1893e3caa0c833f'
clientSecret = 'eb61ba04ff4f4ea3a921b8ed6c66b521'

app.secret_key = "abcdefg"
app.config['Session_Cookie_Name'] = "Ajai's Cookie"
TOKEN_INFO = "token_info"

@app.route('/')
def login():
    sp_oauth =  create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirectPage():
    sp_oauth =  create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('homePage', _external=True))

@app.route('/homePage')
def homePage():
    return(render_template('index.html'))

@app.route('/critiquePage')
def critiquePage():
    try:
        token_info = get_token()
    except:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(auth=token_info['access_token'])

    current_playlists = sp.current_user_playlists()['items']
    playlists = []
    for playlist in current_playlists:
        playlists.append(playlist['id'])

    popularity_scores = []
    artists = []
    def getPopularity():
        start=0
        while True:
            items= sp.current_user_saved_tracks(limit=50, offset=start*50)
            for song in items['items']:
                popularity = song['track']['popularity']
                artist = song['track']['artists'][0]['name']
                if artist in artists:
                    None
                else:
                    artists.append(artist)

                if popularity == 0 or popularity == 1:
                    None
                else:
                    popularity_scores.append(popularity)

            start += 1
            if (len((items['items'])) < 50):
                break

    global_artists = []
    def getArtists(playlist_id):
        start=0
        while True:
            items= sp.playlist_items(playlist_id, limit=100, offset=start*50)
            for song in items['items']:
                artist = song['track']['artists'][0]['name']
                global_artists.append(artist)
            start += 1
            if (len((items['items'])) < 100):
                break

    def compare_intersect(x, y):
        return frozenset(x).intersection(y)
    
 
    getPopularity()
    getArtists('spotify:playlist:6UeSakyzhiEt4NB3UAd6NQ')

    avg_pop = round(sum(popularity_scores) / len(popularity_scores))
    same_artists = len(compare_intersect(artists, global_artists))
    num_artists = len(artists)

    return(render_template('critique.html', **locals()))







@app.route('/getTracks')
def getTracks():
    try:
        token_info = get_token()
    except:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    current_playlists = sp.current_user_playlists()['items']
    playlists = []
    for playlist in current_playlists:
        playlists.append(playlist['id'])

    def msToMin(ms):
        ms/60000
        minutes= math.floor(ms/60000)
        seconds = round(60*((ms/60000)-minutes))
        return(str(minutes)+'min '+str(seconds)+'sec')
        
    song_uris=[]
    #Use this: https://medium.com/analytics-vidhya/your-top-100-songs-2020-in-python-and-plotly-2e803d7e2990

    def allPlaylistSongs():

        f = open('songs.csv', 'r+')
        f.truncate(0)

        filename = 'songs.csv'
        f = open(filename, 'a', encoding="utf-8")
        headers = 'Name,Artist,Popularity,Length,Release,Date_Added\n'
        f.write(headers)

        start=0
        while True:
            items= sp.current_user_saved_tracks(limit=50, offset=start*50)
            for song in items['items']:
                name = song['track']['name']
                name = name.replace(",", "")
                artist = song['track']['artists'][0]['name']
                popularity = song['track']['popularity']
                length = song['track']['duration_ms']
                release = song['track']['album']['release_date']
                added = song['added_at']
                #maybe add followers
                f.write(name+', '+artist+', '+str(popularity)+', '+msToMin(length)+', '+release[:4]+', '+added+'\n')
                
            start += 1
            if (len((items['items'])) < 50):
                break       

        f.close()       
        
    allPlaylistSongs()
    df = pd.read_csv('songs.csv', encoding="ISO-8859-1")

    sns.histplot( data=df, x='Popularity')
    plt.xlabel('Popularity')
    plt.ylabel('Count')
    plt.title('Sample Seaborn Plot')

    # Save the Seaborn plot to a BytesIO object
    popularity_hist_buf = BytesIO()
    plt.savefig(popularity_hist_buf, format='png')
    popularity_hist_buf.seek(0)
    popularity_hist_base64 = base64.b64encode(popularity_hist_buf.read()).decode('utf-8')
    plt.clf()

    top_10_artists = df['Artist'].value_counts().nlargest(10)
    sns.histplot(df[df['Artist'].isin(top_10_artists.index)], x='Artist')
    plt.xlabel('Artists')
    plt.ylabel('Count')
    plt.title('Artist Seaborn Plot')

    artists_buf = BytesIO()
    plt.savefig(artists_buf, format='png')
    artists_buf.seek(0)
    artists_base64 = base64.b64encode(artists_buf.read()).decode('utf-8')
    plt.clf()

    sns.histplot(data=df, x='Release')
    plt.xlabel('Years')
    plt.ylabel('Count')
    plt.title('Release Seaborn Plot')
    
    release_date_buf = BytesIO()
    plt.savefig(release_date_buf, format='png')
    release_date_buf.seek(0)
    release_date_base64 = base64.b64encode(release_date_buf.read()).decode('utf-8')
    plt.clf()

    
    return render_template('data.html', popularity_hist_base64=popularity_hist_base64 ,artists_base64=artists_base64, 
                           release_date_base64=release_date_base64)
    
    
    
    
    
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise "exception"
    now = int(time.time())
    is_expired = token_info['expires_at'] - now <60
    if (is_expired):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(
            client_id='65d88f8d3c8d409da1893e3caa0c833f',
            client_secret='eb61ba04ff4f4ea3a921b8ed6c66b521',
            redirect_uri=url_for('redirectPage', _external=True),
            scope = "user-library-read playlist-read-private playlist-read-collaborative")


'''
@app.route('/getGenres')
    #genres = []
def getGenres(playlist_id):
        start = 0
        while True:
        items= sp.playlist_items(playlist_id, limit=100, offset=start*50)
        for song in items['items']:

            artist_id= song['track']['artists'][0]['id']
            artist = sp.artist(artist_id)
            genre= artist['genres']
            try:
                genres.append(str(genre[0]))
            except:
                None

        start += 1
        if (len((items['items'])) < 100):
            break
'''