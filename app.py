from flask import Flask, request, url_for, session, redirect, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import sys
import pandas as pd
import math
import matplotlib
import matplotlib.pyplot as plt 
matplotlib.use('Agg')
import seaborn as sns 
from io import BytesIO
import base64
from wordcloud import WordCloud
import matplotlib.cm
import matplotlib.colors
import secrets


app = Flask(__name__)

clientID = '65d88f8d3c8d409da1893e3caa0c833f'
clientSecret = 'eb61ba04ff4f4ea3a921b8ed6c66b521'

app.secret_key = "abcdefg"
app.config['Session_Cookie_Name'] = "Ajai's Cookie"
TOKEN_INFO = "token_info"

@app.route('/home')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
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
        return(str(round(ms/60000, 2)))
        
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
                f.write(name+', '+artist+', '+str(popularity)+', '+msToMin(length)+', '+release[:4]+', '
                        +added[:7]+'\n')
                
            start += 1
            if (len((items['items'])) < 50):
                break       

        f.close()       
        
    allPlaylistSongs()
    df = pd.read_csv('songs.csv', encoding="ISO-8859-1")

    top_10_artists = df['Artist'].value_counts().nlargest(10)
    bottom_10_artists = df['Artist'].value_counts().nsmallest(10)
    top_10_pop = df.nlargest(10, 'Popularity')
    top_10_length = df.nlargest(10, 'Length')
    
    sns.set(style="whitegrid")
    ax = sns.histplot( data=df, x='Popularity', color="lightgreen", alpha=1.0)
    plt.xlabel('Popularity')
    plt.ylabel('Count')
    plt.title('Sample Seaborn Plot')

    fig = plt.gcf()
    fig.patch.set_facecolor('none')
    fig.patch.set_alpha(0.0)

    # Access the Axes and set its background color to be transparent
    ax.patch.set_facecolor('none')
    ax.patch.set_alpha(0.0)
    ax.set_title('Popularity of all Songs', color='white', fontsize=16)
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')

    # Save the Seaborn plot to a BytesIO object
    popularity_hist_buf = BytesIO()
    plt.savefig(popularity_hist_buf, format='png', bbox_inches="tight")
    popularity_hist_buf.seek(0)
    popularity_hist_base64 = base64.b64encode(popularity_hist_buf.read()).decode('utf-8')
    plt.clf()

    ax = sns.histplot(df[df['Artist'].isin(top_10_artists.index)], x='Artist', color="lightgreen", alpha=1.0)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    plt.xlabel('Artists')
    plt.ylabel('Count')
    plt.title('Top Artist Seaborn Plot')

    fig = plt.gcf()
    fig.patch.set_facecolor('none')
    fig.patch.set_alpha(0.0)

    # Access the Axes and set its background color to be transparent
    ax.patch.set_facecolor('none')
    ax.patch.set_alpha(0.0)
    ax.set_title('Song Distribution of Top 10 Artists', color='white', fontsize=16)
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')

    artists_buf = BytesIO()
    plt.savefig(artists_buf, format='png', bbox_inches="tight")
    artists_buf.seek(0)
    artists_base64 = base64.b64encode(artists_buf.read()).decode('utf-8')
    plt.clf()

    ax = sns.histplot(df[df['Artist'].isin(bottom_10_artists.index)], x='Artist', color="lightgreen", alpha=1.0)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    plt.xlabel('Artists')
    plt.ylabel('Count')
    plt.title('Bottom Artist Seaborn Plot')

    fig = plt.gcf()
    fig.patch.set_facecolor('none')
    fig.patch.set_alpha(0.0)

    # Access the Axes and set its background color to be transparent
    ax.patch.set_facecolor('none')
    ax.patch.set_alpha(0.0)
    ax.set_title('Song Distribution of Bottom 10 Artists', color='white', fontsize=16)
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')

    bot_artists_buf = BytesIO()
    plt.savefig(bot_artists_buf, format='png', bbox_inches="tight")
    bot_artists_buf.seek(0)
    bot_artists_base64 = base64.b64encode(bot_artists_buf.read()).decode('utf-8')
    plt.clf()

    ax = sns.histplot(data=df, x='Release', color="lightgreen", alpha=1.0)
    plt.xlabel('Years')
    plt.ylabel('Count')
    plt.title('Release Seaborn Plot')
    
    fig = plt.gcf()
    fig.patch.set_facecolor('none')
    fig.patch.set_alpha(0.0)

    # Access the Axes and set its background color to be transparent
    ax.patch.set_facecolor('none')
    ax.patch.set_alpha(0.0)
    ax.set_title('Distribution of All Song Release Dates', color='white', fontsize=16)
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')

    release_date_buf = BytesIO()
    plt.savefig(release_date_buf, format='png', bbox_inches='tight')
    release_date_buf.seek(0)
    release_date_base64 = base64.b64encode(release_date_buf.read()).decode('utf-8')
    plt.clf()

    ax = sns.scatterplot(data=df, x='Length', y='Popularity', color="lightgreen", alpha=1.0)
    plt.xlabel('Song Length')
    plt.ylabel('Popularity')
    plt.title('Length vs Popularity Seaborn Plot')
    
    fig = plt.gcf()
    fig.patch.set_facecolor('none')
    fig.patch.set_alpha(0.0)

    # Access the Axes and set its background color to be transparent
    ax.patch.set_facecolor('none')
    ax.patch.set_alpha(0.0)
    ax.set_title('Song length vs Popularity', color='white', fontsize=16)
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')

    length_v_pop_buf = BytesIO()
    plt.savefig(length_v_pop_buf, format='png', bbox_inches='tight')
    length_v_pop_buf.seek(0)
    length_v_pop_base64 = base64.b64encode(length_v_pop_buf.read()).decode('utf-8')
    plt.clf()

    ax = sns.barplot(data=df[df['Artist'].isin(top_10_artists.index)], x='Artist', y='Length')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    plt.xlabel('Artist')
    plt.ylabel('Song Length')
    plt.title('Length vs Artist Seaborn Plot')

    fig = plt.gcf()
    fig.patch.set_facecolor('none')
    fig.patch.set_alpha(0.0)

    # Access the Axes and set its background color to be transparent
    ax.patch.set_facecolor('none')
    ax.patch.set_alpha(0.0)
    ax.set_title('Average Song Lengths of Top 10 Artists', color='white', fontsize=16)
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    
    artist_len_buf = BytesIO()
    plt.savefig(artist_len_buf, format='png', bbox_inches='tight')
    artist_len_buf.seek(0)
    artist_len_base64 = base64.b64encode(artist_len_buf.read()).decode('utf-8')
    plt.clf()

    ax = sns.histplot(data=df, x="Date_Added", color="lightgreen", alpha=1.0)
    plt.xlabel('Date Added')
    plt.ylabel('Count')
    plt.title('How Many Songs Added Per Month')

    fig = plt.gcf()
    fig.patch.set_facecolor('none')
    fig.patch.set_alpha(0.0)

    # Access the Axes and set its background color to be transparent
    ax.patch.set_facecolor('none')
    ax.patch.set_alpha(0.0)
    ax.set_title('Distribution of Dates - Songs Added', color='white', fontsize=16)
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    
    songs_added_buf = BytesIO()
    plt.savefig(songs_added_buf, format='png', bbox_inches="tight")
    songs_added_buf.seek(0)
    songs_added_base64 = base64.b64encode(songs_added_buf.read()).decode('utf-8')
    plt.clf()

    
    ax = sns.barplot(data=top_10_pop, x='Popularity', y='Name')
    plt.xlabel('Popularity')
    plt.ylabel('Song Name')
    plt.title('Top 10 Most Popular Songs')

    fig = plt.gcf()
    fig.patch.set_facecolor('none')
    fig.patch.set_alpha(0.0)

    # Access the Axes and set its background color to be transparent
    ax.patch.set_facecolor('none')
    ax.patch.set_alpha(0.0)
    ax.set_title('Top 10 Most Popular Artists', color='white', fontsize=16)
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    
    song_pop_buf = BytesIO()
    plt.savefig(song_pop_buf, format='png', bbox_inches="tight")
    song_pop_buf.seek(0)
    song_pop_base64 = base64.b64encode(song_pop_buf.read()).decode('utf-8')
    plt.clf()

    sns.set(style="whitegrid")
    ax = sns.barplot(data=top_10_length, x='Name', y='Length')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    plt.xlabel('Song Name')
    plt.ylabel('Length')
    plt.title('Top 10 Longest Songs')

    fig = plt.gcf()
    fig.patch.set_facecolor('none')
    fig.patch.set_alpha(0.0)

    # Access the Axes and set its background color to be transparent
    ax.patch.set_facecolor('none')
    ax.patch.set_alpha(0.0)
    ax.set_title('Top 10 Longest Songs', color='white', fontsize=16)
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')

    song_len_buf = BytesIO()
    plt.savefig(song_len_buf, format='png', bbox_inches="tight")
    song_len_buf.seek(0)
    song_len_base64 = base64.b64encode(song_len_buf.read()).decode('utf-8')
    plt.clf()

    
    return render_template('data.html', popularity_hist_base64=popularity_hist_base64 ,artists_base64=artists_base64, 
                           release_date_base64=release_date_base64, length_v_pop_base64=length_v_pop_base64,
                           artist_len_base64=artist_len_base64, songs_added_base64=songs_added_base64, song_pop_base64=song_pop_base64,
                           bot_artists_base64=bot_artists_base64, song_len_base64=song_len_base64,)
    
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise Exception("Token not found in session")
    now = int(time.time())
    is_expired = token_info['expires_at'] - now <60
    if (is_expired):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session[TOKEN_INFO] = token_info
    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(
            client_id='65d88f8d3c8d409da1893e3caa0c833f',
            client_secret='eb61ba04ff4f4ea3a921b8ed6c66b521',
            redirect_uri=url_for('redirectPage', _external=True),
            scope = "user-library-read playlist-read-private playlist-read-collaborative")



@app.route('/getGenres')
   
def getGenres():
    try:
        token_info = get_token()
    except:
        print("user not logged in")
        return redirect("/")
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    def msToMin(ms):
        return(str(round(ms/60000, 2)))
    
    start = 0
    def allPlaylistGenres():
        f = open('genres.csv', 'r+')
        f.truncate(0)

        filename = 'genres.csv'
        f = open(filename, 'a', encoding="utf-8")
        headers = 'Genre,Popularity,Length,Release\n'
        f.write(headers)
        
        start = 0

        while True:
            items = sp.current_user_saved_tracks(limit=50, offset=start*50)
            for song in items['items']:
                artist_id= song['track']['artists'][0]['id']
                artist = sp.artist(artist_id)
                try:
                    genre= artist['genres'][0]
                except:
                    None

                popularity = song['track']['popularity']
                length = song['track']['duration_ms']
                release = song['track']['album']['release_date']

                f.write(genre+','+str(popularity)+','+str(msToMin(length))+','+str(release[:4])+'\n')
            
            start += 1
            if (len((items['items'])) < 50):
                break

        f.close()      

    #allPlaylistGenres()
    df = pd.read_csv('genres.csv', encoding="ISO-8859-1")
    sns.set(style="whitegrid")

    genre_counts = df['Genre'].value_counts().nlargest(20)
    genre_10 = df['Genre'].value_counts().nlargest(10)

    plt.pie(genre_10, labels=genre_10.index, colors=sns.color_palette("Greens"), textprops={'color': 'white'})
    plt.title('Top 10 Genres')

    ax = plt.gca()

    # Set the color of the labels to white
    label_color = 'white'
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color(label_color)

    # Set the color of the ticks to white
    ax.tick_params(axis='x', colors=label_color)
    ax.tick_params(axis='y', colors=label_color)
    ax.set_title('Top 10 Genres', color='white', fontsize=16)
    fig = plt.gcf()
    fig.patch.set_facecolor('none')
    fig.patch.set_alpha(0.0)

    # Access the Axes and set its background color to be transparent

    
    genre_pie_buf = BytesIO()
    plt.savefig(genre_pie_buf, format='png')
    genre_pie_buf.seek(0)
    genre_pie_base64 = base64.b64encode(genre_pie_buf.read()).decode('utf-8')
    plt.clf()

    ax = sns.barplot(x=genre_counts.index, y=genre_counts.values)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    plt.title('Top 20 Genres')
    
    fig = plt.gcf()
    fig.patch.set_facecolor('none')
    fig.patch.set_alpha(0.0)

    # Access the Axes and set its background color to be transparent
    ax.patch.set_facecolor('none')
    ax.patch.set_alpha(0.0)
    ax.set_title('Top 20 genres', color='white', fontsize=16)
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')

    genre_hist_buf = BytesIO()
    plt.savefig(genre_hist_buf, format='png', bbox_inches = 'tight')
    genre_hist_buf.seek(0)
    genre_hist_base64 = base64.b64encode(genre_hist_buf.read()).decode('utf-8')
    plt.clf()

    genre_counts_all = df['Genre'].value_counts()
    ax = wordcloud = WordCloud(width=800, height=400, background_color=None).generate_from_frequencies(genre_counts_all)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Word Cloud of Genres')

    fig = plt.gcf()
    fig.patch.set_facecolor('none')
    fig.patch.set_alpha(0.0)

    # Access the Axes and set its background color to be transparent


    wordcloud_buf = BytesIO()
    plt.savefig(wordcloud_buf, format='png')
    wordcloud_buf.seek(0)
    wordcloud_base64 = base64.b64encode(wordcloud_buf.read()).decode('utf-8')
    plt.clf()

    top_genre = most_common_result = df['Genre'].value_counts().idxmax()
    
    return render_template('genre.html', **locals())
