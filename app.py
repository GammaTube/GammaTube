from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import requests
from bs4 import BeautifulSoup
from youtubesearchpython import VideosSearch, ChannelsSearch, PlaylistsSearch
import os
import re

app = Flask(__name__)
app.secret_key = 'ilyaas2012'  # Required for session management and flashing messages

# Configuration for the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database model for the user accounts
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Initialize the database (create tables)
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    print("Index route accessed")
    return render_template('index.html')

@app.route('/search')
def search_page():
    query = request.args.get('query', '')
    print(f"Search page accessed with query: {query}")
    if query:
        try:
            search = VideosSearch(query, limit=20)
            results = search.result()

            videos = []
            for item in results['result']:
                title = item['title']
                video_url = 'https://www.youtube.com/watch?v=' + item['id']
                thumbnail = item['thumbnails'][0]['url'] if item['thumbnails'] else 'https://via.placeholder.com/120x90'

                videos.append({'title': title, 'src': video_url, 'thumbnail': thumbnail})

            return render_template('search.html', videos=videos, query=query)
        except Exception as e:
            print(f"Error during search: {e}")
            return render_template('search.html', error='An error occurred during the search')
    else:
        return render_template('search.html', error='No query provided')

@app.route('/api/search')
def search():
    query = request.args.get('query', '')
    print(f"API search accessed with query: {query}")
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        search = VideosSearch(query, limit=15)
        results = search.result()

        videos = []
        for item in results['result']:
            title = item['title']
            video_url = 'https://www.youtube.com/watch?v=' + item['id']
            thumbnail = item['thumbnails'][0]['url'] if item['thumbnails'] else 'https://via.placeholder.com/120x90'

            videos.append({'title': title, 'src': video_url, 'thumbnail': thumbnail})

        return jsonify(videos)
    except Exception as e:
        print(f"Error during search: {e}")
        return jsonify({'error': 'An error occurred during the search'}), 500

# New API route for channel search
@app.route('/api/channel_search')
def channel_search():
    query = request.args.get('query', '')
    print(f"Channel search accessed with query: {query}")
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        channel_search = ChannelsSearch(query, limit=10, region='US')
        results = channel_search.result()

        channels = []
        for item in results['result']:
            title = item['title']
            channel_id = item['id']
            channel_url = 'https://www.youtube.com/channel/' + channel_id
            thumbnail = item['thumbnails'][0]['url'] if item['thumbnails'] else 'https://via.placeholder.com/120x90'

            channels.append({'title': title, 'url': channel_url, 'thumbnail': thumbnail})

        return jsonify(channels)
    except Exception as e:
        print(f"Error during channel search: {e}")
        return jsonify({'error': 'An error occurred during the channel search'}), 500

# New API route for playlist search
@app.route('/api/playlist_search')
def playlist_search():
    query = request.args.get('query', '')
    print(f"Playlist search accessed with query: {query}")
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        playlist_search = PlaylistsSearch(query, limit=10)
        results = playlist_search.result()

        playlists = []
        for item in results['result']:
            title = item.get('title', 'No title')
            thumbnail = item['thumbnails'][0]['url'] if item.get('thumbnails') else 'https://via.placeholder.com/120x90'
            playlist_url = 'https://www.youtube.com/playlist?list=' + item['id']

            playlist_id = playlist_url.split('=')[1]
            video_count = item.get('videoCount', 'Unknown')

            playlists.append({
                'title': title,
                'playlistId': playlist_id,
                'url': playlist_url,
                'thumbnail': thumbnail,
                'videoCount': video_count
            })

        return jsonify(playlists)
    except Exception as e:
        print(f"Error during playlist search: {e}")
        return jsonify({'error': 'An error occurred during the playlist search'}), 500

@app.route('/channel/<channel_name>')
def channel_page(channel_name):
    print(f"Channel page accessed for channel: {channel_name}")
    try:
        # Construct the YouTube channel URL based on the channel name
        channel_url = f'https://www.youtube.com/c/{channel_name}'  # This assumes the channel has a custom URL based on name

        # Fetch the HTML content of the channel page
        response = requests.get(channel_url)
        
        # If request is unsuccessful, return an error
        if response.status_code != 200:
            print(f"Failed to fetch channel page: Status code {response.status_code}")
            return render_template('channels.html', error='Failed to access the channel page')

        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Attempt to extract the channel title, thumbnail, and subscriber count
        channel_title = soup.find('meta', {'property': 'og:title'})['content'] if soup.find('meta', {'property': 'og:title'}) else 'Unknown Channel'
        thumbnail = soup.find('meta', {'property': 'og:image'})['content'] if soup.find('meta', {'property': 'og:image'}) else 'https://via.placeholder.com/120x90'
        
        # The subscriber count may not be directly available in meta tags; it might require more parsing
        # This is a basic example and might not always work due to YouTube’s dynamic HTML structure
        subscriber_tag = soup.find('span', {'class': 'yt-subscription-button-subscriber-count-branded-horizontal'})
        subscribers = subscriber_tag.text if subscriber_tag else 'N/A'

        # For description, we might not have it directly available, so using a placeholder
        description = 'Description not available via scraping.'

        # Render the channel page with the fetched details
        return render_template('channels.html', 
                               channel_name=channel_title, 
                               channel_url=channel_url, 
                               thumbnail=thumbnail, 
                               subscribers=subscribers,
                               description=description)

    except Exception as e:
        print(f"Error fetching channel page: {e}")
        return render_template('channels.html', error='An error occurred while fetching the channel')

@app.route('/watch')
def watch():
    video_id = request.args.get('v')
    print(f"Watch route accessed with video_id: {video_id}")
    return render_template('watch.html', video_id=video_id)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!', 'error')
            return redirect(url_for('signup'))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('Signup successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/playlist')
def playlist():
    playlist_id = request.args.get('id')
    print(f"Playlist route accessed with playlist_id: {playlist_id}")
    if not playlist_id:
        return "No playlist ID provided", 400

    return render_template('playlist.html', playlist_id=playlist_id)

if __name__ == '__main__':
    app.run(debug=True)
