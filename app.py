from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String
from werkzeug.security import generate_password_hash, check_password_hash
from youtubesearchpython import VideosSearch, ChannelsSearch, PlaylistsSearch, Video, ResultMode
import smtplib
import io
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from moviepy.editor import VideoFileClip
import base64

app = Flask(__name__)
app.secret_key = 'ilyaas2012'

# Configuration for the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.bmxyjwxajvbbglhewpqr:gamma-tube-@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# User model for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)  # Consistent usage of db.Column

    def __repr__(self):
        return f'<User {self.username}>'


# Watch history model for the database
class WatchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)  # Store the username instead of user_id
    video_id = db.Column(db.String(255), nullable=False)  # Store the video ID
    video_name = db.Column(db.String(255), nullable=False)  # Store the video name
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())  # When the video was watched

    def __repr__(self):
        return f'<WatchHistory username={self.username}, video_id={self.video_id}, video_name={self.video_name}, timestamp={self.timestamp}>'

# Playlist model for the database
class Playlist(db.Model):
    id = db.Column(db.String(10), primary_key=True)  # Randomly generated ID
    name = db.Column(db.String(100), nullable=False)
    owner_username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    videos = db.relationship('PlaylistEntry', backref='playlist', cascade='all, delete-orphan')

# PlaylistEntry model for storing videos in a playlist
class PlaylistEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.String(10), db.ForeignKey('playlist.id'), nullable=False)
    video_id = db.Column(db.String(255), nullable=False)
    video_thumbnail = db.Column(db.String(255), nullable=False)


# Initialize the database (create tables)
with app.app_context():
    db.create_all()


def send_signup_email(to_email, username):
    # 
    sender_email = "Gamma.scratch@gmail.com"
    password = "wsnp cgax tjic ecxv"

    # Email content
    subject = "Account Created for GammaTube"
    message = f"Hello {username}, your account for GammaTube has been created. Login here: https://gammatube.koyeb.app/login"

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    # Setup the SMTP server (using Gmail's SMTP server)
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise


@app.route('/')
def index():
    print("Index route accessed")
    return render_template('index.html')


@app.route('/search')
def search_page():
    query = request.args.get('query', '')
    print(f"Search page accessed with query: '{query}'")

    def upload_thumbnail_to_github(thumbnail_url, video_id):
        token = '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'  # Replace with your actual token
        repo = 'Gamma7113131/Convery.GammaTube'
        path = f'static/{video_id}.jpg'
        url = f'https://api.github.com/repos/{repo}/contents/{path}'

        print(f"Downloading thumbnail from: {thumbnail_url}")
        response = requests.get(thumbnail_url)
        
        if response.status_code != 200:
            print(f"Failed to download thumbnail from {thumbnail_url}. Response: {response.status_code}")
            return False

        thumbnail_data = base64.b64encode(response.content).decode('utf-8')  # Convert image to base64 for upload

        print(f"Checking if thumbnail exists for video_id: {video_id}")
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }

        # Check if the file already exists
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # File exists, we need to update it
            existing_file = response.json()
            sha = existing_file['sha']  # Get the SHA of the existing file for update
            print(f"Thumbnail already exists for video_id: {video_id}. Updating upload.")

            data = {
                'message': 'Update thumbnail',
                'content': thumbnail_data,
                'sha': sha,  # Include SHA for the existing file
                'branch': 'main',  # Specify the branch if necessary
                'committer': {  # Add committer info
                    'name': 'Gamma',  # Replace with your name
                    'email': 'gametron2012@yahoo.com'  # Replace with your email
                }
            }

            response = requests.put(url, headers=headers, json=data)
        else:
            # File does not exist, create a new one
            print(f"Thumbnail not found for video_id: {video_id}. Attempting upload.")
            data = {
                'message': 'Upload thumbnail',
                'content': thumbnail_data,
                'branch': 'main',  # Specify the branch if necessary
                'committer': {  # Add committer info
                    'name': 'Gamma',  # Replace with your name
                    'email': 'gametron2012@yahoo.com'  # Replace with your email
                }
            }

            response = requests.put(url, headers=headers, json=data)

        if response.status_code in (201, 200):
            print(f"Successfully uploaded thumbnail for video_id: {video_id}")
            return True
        else:
            print(f"Failed to upload thumbnail for video_id: {video_id}. Response: {response.status_code}, {response.text}")
            return False

    if query:
        try:
            print(f"Performing search for query: {query}")
            search = VideosSearch(query, limit=20)  # Assume VideosSearch is defined
            results = search.result()

            videos = []
            for item in results['result']:
                title = item['title']
                video_id = item['id']
                video_url = 'https://www.youtube.com/watch?v=' + video_id

                # Get the original thumbnail URL
                thumbnail_url = item['thumbnails'][0]['url'] if item['thumbnails'] else 'https://via.placeholder.com/120x90'
                print(f"Video title: {title}, ID: {video_id}, Original thumbnail: {thumbnail_url}")

                # Attempt to upload the original thumbnail to GitHub
                uploaded = upload_thumbnail_to_github(thumbnail_url, video_id)

                if uploaded:
                    # Construct the GitHub URL for the uploaded thumbnail
                    github_thumbnail_url = f"https://raw.githubusercontent.com/Gamma7113131/Convery.GammaTube/main/static/{video_id}.jpg"
                    thumbnail = github_thumbnail_url
                else:
                    print(f"Failed to upload thumbnail for video_id: {video_id}. Using original thumbnail instead.")
                    thumbnail = thumbnail_url  # Fallback to the original thumbnail

                videos.append({'title': title, 'src': video_url, 'thumbnail': thumbnail})

            print(f"Search completed with {len(videos)} results.")
            return render_template('search.html', videos=videos, query=query)
        except Exception as e:
            print(f"Error during search: {e}")
            return render_template('search.html', error='An error occurred during the search')
    else:
        print("No query provided, returning error.")
        return render_template('search.html', error='No query provided')

@app.route('/api/search')
def api_search():
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
            playlist_id = item['id']
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


@app.route('/watch')
def watch():
    video_id = request.args.get('v')
    if not video_id:
        print("No video ID provided, redirecting to homepage")
        return redirect(url_for('index'))

    print(f"Watch route accessed with video_id: {video_id}")
    
    # Check if user is logged in by verifying 'username' in session
    username = session.get('username')
    video_name = 'Unknown'

    try:
        video_url = f'https://www.youtube.com/watch?v={video_id}'
        videoInfo = Video.getInfo(video_url, mode=ResultMode.json)

        # Debug: Print the entire videoInfo response
        print(f"Video Info Retrieved: {videoInfo}")

        video_name = videoInfo.get('title') or 'Unknown Title'  # Handle NoneType
    except Exception as e:
        print(f"Failed to fetch video information for video_id '{video_id}': {e}")

    # Store watch history only if the user is logged in
    if username:
        new_history_entry = WatchHistory(username=username, video_id=video_id, video_name=video_name)
        db.session.add(new_history_entry)
        db.session.commit()

    return render_template('watch.html', video_id=video_id, video_name=video_name)

@app.route('/signup', methods=['GET', 'POST'])
def signup():    
    if request.method == 'POST':
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        email_address = data.get('email')

        if not username or not password or not email_address:
            return jsonify(success=False, message='Username, password, and email are required!'), 400

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify(success=False, message='Username already exists!'), 400

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password, email=email_address)

        db.session.add(new_user)
        db.session.commit()

        try:
            send_signup_email(email_address, username)
        except Exception as e:
            return jsonify(success=False, message=f'Signup successful, but failed to send email: {str(e)}'), 500

        return jsonify(success=True, message='Signup successful! You can now log in.'), 201

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Get the 'redirect' parameter from the URL query string if present
    redirect_url = request.args.get('redirect', url_for('index'))  # Default to the homepage if not provided

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Retrieve the user from the database
        user = User.query.filter_by(username=username).first()

        # Check if the user exists and the password matches
        if user and check_password_hash(user.password_hash, password):
            # Store the username in the session to indicate the user is logged in
            session['username'] = username
            flash('Login successful!', 'success')
            # Redirect to the specified URL or fallback to the homepage
            return redirect(redirect_url)
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for('login', redirect=redirect_url))

    return render_template('login.html')

@app.route('/playlist')
def playlist():
    playlist_id = request.args.get('id')
    print(f"Playlist route accessed with playlist_id: {playlist_id}")
    if not playlist_id:
        return "No playlist ID provided", 400

    return render_template('playlist.html', playlist_id=playlist_id)


@app.route('/watch_history')
def watch_history():
    # Check if the user is logged in by checking the session
    if 'username' not in session:
        print("User not logged in, redirecting to login page")
        # Redirect to login with a 'redirect' parameter to come back to '/watch_history' after login
        return redirect(url_for('login', redirect=url_for('watch_history')))

    username = session['username']  # Retrieve the username from the session
    
    # Query the watch history using the username
    history = WatchHistory.query.filter_by(username=username).order_by(WatchHistory.timestamp.desc()).all()
    print(f"Watch history accessed for user: {username}")

    if history:
        return render_template('watch_history.html', history=history)
    else:
        return render_template('watch_history.html', error="No watch history found.")

@app.route('/sitemap.xml')
def sitemap():
    try:
        return send_file('sitemap.xml', mimetype='application/xml')
    except Exception as e:
        return Response(f"Error serving sitemap: {e}", status=500)

@app.route('/logout')
def logout():
    # Remove 'username' from the session to log the user out
    session.pop('username', None)
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))  # Redirect to the homepage

@app.route('/my_playlist/create', methods=['POST'])
def create_playlist():
    if 'username' not in session:
        return jsonify(success=False, message='User not logged in'), 403
    
    username = session['username']
    data = request.get_json()
    playlist_name = data.get('name')

    if not playlist_name:
        return jsonify(success=False, message='Playlist name is required'), 400

    # Generate a unique random ID for the playlist
    while True:
        random_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        if not Playlist.query.get(random_id):
            break

    new_playlist = Playlist(id=random_id, name=playlist_name, owner_username=username)
    db.session.add(new_playlist)
    db.session.commit()

    return jsonify(success=True, message='Playlist created', playlist_id=random_id), 201

@app.route('/my_playlist/add_video', methods=['POST'])
def add_video_to_playlist():
    if 'username' not in session:
        return jsonify(success=False, message='User not logged in'), 403

    data = request.get_json()
    playlist_id = data.get('playlist_id')
    video_id = data.get('video_id')

    if not playlist_id or not video_id:
        return jsonify(success=False, message='Playlist ID and video ID are required'), 400

    # Validate playlist ownership
    playlist = Playlist.query.filter_by(id=playlist_id, owner_username=session['username']).first()
    if not playlist:
        return jsonify(success=False, message='Playlist not found or access denied'), 404

    video_thumbnail = f"https://i.ytimg.com/vi/{video_id}/hq720.jpg"

    new_entry = PlaylistEntry(playlist_id=playlist_id, video_id=video_id, video_thumbnail=video_thumbnail)
    db.session.add(new_entry)
    db.session.commit()

    return jsonify(success=True, message='Video added to playlist'), 200

@app.route('/my_playlist/<playlist_id>', methods=['GET'])
def get_playlist(playlist_id):
    if 'username' not in session:
        return jsonify(success=False, message='User not logged in'), 403

    playlist = Playlist.query.filter_by(id=playlist_id, owner_username=session['username']).first()
    if not playlist:
        return jsonify(success=False, message='Playlist not found or access denied'), 404

    videos = [{
        'video_id': entry.video_id,
        'video_thumbnail': entry.video_thumbnail
    } for entry in playlist.videos]

    return jsonify(success=True, playlist_name=playlist.name, videos=videos), 200

@app.route('/my_playlist/delete_video', methods=['DELETE'])
def delete_video_from_playlist():
    if 'username' not in session:
        return jsonify(success=False, message='User not logged in'), 403

    data = request.get_json()
    playlist_id = data.get('playlist_id')
    video_id = data.get('video_id')

    if not playlist_id or not video_id:
        return jsonify(success=False, message='Playlist ID and video ID are required'), 400

    # Validate playlist ownership
    playlist = Playlist.query.filter_by(id=playlist_id, owner_username=session['username']).first()
    if not playlist:
        return jsonify(success=False, message='Playlist not found or access denied'), 404

    entry = PlaylistEntry.query.filter_by(playlist_id=playlist_id, video_id=video_id).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
        return jsonify(success=True, message='Video removed from playlist'), 200
    else:
        return jsonify(success=False, message='Video not found in the playlist'), 404

@app.route('/my_playlist/delete', methods=['DELETE'])
def delete_playlist():
    if 'username' not in session:
        return jsonify(success=False, message='User not logged in'), 403

    data = request.get_json()
    playlist_id = data.get('playlist_id')

    if not playlist_id:
        return jsonify(success=False, message='Playlist ID is required'), 400

    # Validate playlist ownership
    playlist = Playlist.query.filter_by(id=playlist_id, owner_username=session['username']).first()
    if not playlist:
        return jsonify(success=False, message='Playlist not found or access denied'), 404

    db.session.delete(playlist)
    db.session.commit()

    return jsonify(success=True, message='Playlist deleted'), 200

if __name__ == '__main__':
    db.create_all()  # Create database tables
    app.run(debug=True)
