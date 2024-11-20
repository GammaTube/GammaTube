from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String
from werkzeug.security import generate_password_hash, check_password_hash
from youtubesearchpython import VideosSearch, ChannelsSearch, PlaylistsSearch, Video, ResultMode
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_login import login_required
import random
import string
import os
import requests
from bs4 import BeautifulSoup
from datetime import timedelta  # Import timedelta for session expiration

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Configuration for permanent sessions
app.config['SESSION_PERMANENT'] = True  # Make the session permanent
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)  # Session lifetime of 365 days

# Configuration for the database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
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

# Settings model for the database
class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False, unique=True)
    dark_mode = db.Column(db.Boolean, default=False)  # Example setting: Dark mode preference
    email_notifications = db.Column(db.Boolean, default=True)  # Example setting: Email notifications
    default_language = db.Column(db.String(10), default='en')  # Example setting: Default language

    def __repr__(self):
        return f'<UserSettings username={self.username}, dark_mode={self.dark_mode}, email_notifications={self.email_notifications}, default_language={self.default_language}>'

# Subscription model
class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f"<Subscription {self.username}, {self.email}>"

# Initialize the database (create tables)
with app.app_context():
    db.create_all()


def send_signup_email(to_email, username):
    # 
    sender_email = "Gamma.scratch@gmail.com"
    password = os.getenv('PASSWORD')

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
        
def get_youtube_title(video_id):
    # Construct the API URL
    url = f"https://api4gammatube.pythonanywhere.com/Video_title/{video_id}"
    try:
        # Send an HTTP GET request to the API
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code != 200:
            print("Error: Unable to access video data from the API")
            return None

        # Parse the JSON response
        data = response.json()
        
        # Check if 'title' is in the response
        if 'title' in data:
            title = data['title']
            print(f"Video accessed with Title: {title}")
            return title
        else:
            print("Error: Title not found in the response")
            return None
        
    except Exception as e:
        print(f"An error occurred: {e}")
    return None

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


@app.route('/api/playlist_search', methods=['GET'])
def playlist_search():
    # Get the search query from the request arguments
    query = request.args.get('query', '').strip()
    print(f"Playlist search accessed with query: {query}")
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        # Call the external API
        external_api_url = 'https://api4gammatube.pythonanywhere.com/search_playlists/'
        response = requests.get(f"{external_api_url}", params={'query': query})
        
        if response.status_code == 200:
            results = response.json()
            
            playlists = []
            for item in results.get('playlists', []):  # Assuming API returns playlists in 'playlists' key
                title = item.get('title', 'No title')
                thumbnail = item['thumbnail'] if item.get('thumbnail') else 'https://via.placeholder.com/120x90'
                playlist_url = item.get('url', 'https://www.youtube.com/')
                playlist_id = item.get('playlistId', 'Unknown')
                video_count = item.get('videoCount', 'Unknown')

                playlists.append({
                    'title': title,
                    'playlistId': playlist_id,
                    'url': playlist_url,
                    'thumbnail': thumbnail,
                    'videoCount': video_count
                })
            
            return jsonify(playlists)
        else:
            # Handle non-200 responses from the external API
            return jsonify({'error': f"External API returned status code {response.status_code}"}), response.status_code
    except Exception as e:
        # Log the exception and return a general error message
        print(f"Error during playlist search: {e}")
        return jsonify({'error': 'An error occurred during the playlist search'}), 500


@app.route('/watch')
def watch():
    video_id = request.args.get('v')
    if not video_id:
        print("No video ID provided, redirecting to homepage")
        return redirect(url_for('index'))

    print(f"Watch route accessed with video_id: {video_id}")
    
    username = session.get('username')
    video_name = get_youtube_title(video_id) or 'Unknown Title'  # Use the new function here

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
    # Get the 'redirect' parameter and ensure it's a valid relative URL
    redirect_url = request.args.get('redirect', None)
    if not redirect_url or not redirect_url.startswith('/'):
        redirect_url = url_for('index')  # Default to homepage if invalid or not provided

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
            # Redirect to the validated redirect URL or homepage
            return redirect(redirect_url)
        else:
            flash('Invalid username or password!', 'error')
            # Retain the redirect parameter in the query string for the login page
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

@app.route('/62fc699e34ef49ef9a7d5b94a1f7bea3.txt')
def indexnow_verification():
    # Read the content of the file and return it in the response
    with open("62fc699e34ef49ef9a7d5b94a1f7bea3.txt", "r") as file:
        content = file.read()
    return Response(content, mimetype="text/plain")

@app.route('/settings', methods=['GET', 'POST'])
def user_settings():
    # Check if the user is logged in
    if 'username' not in session:
        flash('You need to log in to access settings.', 'error')
        return redirect(url_for('login', redirect=url_for('user_settings')))

    username = session['username']

    # Retrieve the user's settings from the database
    user_settings = UserSettings.query.filter_by(username=username).first()

    if request.method == 'POST':
        # Parse the form data
        dark_mode = request.form.get('dark_mode') == 'on'
        email_notifications = request.form.get('email_notifications') == 'on'
        default_language = request.form.get('default_language', 'en')

        if not user_settings:
            # Create a new settings record if none exists
            user_settings = UserSettings(username=username, dark_mode=dark_mode, email_notifications=email_notifications, default_language=default_language)
            db.session.add(user_settings)
        else:
            # Update the existing settings record
            user_settings.dark_mode = dark_mode
            user_settings.email_notifications = email_notifications
            user_settings.default_language = default_language

        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('user_settings'))

    # Render the settings page with the current settings
    return render_template('settings.html', settings=user_settings)

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    # Check if the user is logged in
    if 'username' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    username = session['username']
    user_settings = UserSettings.query.filter_by(username=username).first()

    if request.method == 'POST':
        data = request.get_json()

        dark_mode = data.get('dark_mode', False)
        email_notifications = data.get('email_notifications', True)
        default_language = data.get('default_language', 'en')

        if not user_settings:
            # Create new settings if they don't exist
            user_settings = UserSettings(username=username, dark_mode=dark_mode, email_notifications=email_notifications, default_language=default_language)
            db.session.add(user_settings)
        else:
            # Update existing settings
            user_settings.dark_mode = dark_mode
            user_settings.email_notifications = email_notifications
            user_settings.default_language = default_language

        db.session.commit()
        return jsonify({'success': True, 'message': 'Settings updated successfully'})

    # If it's a GET request, return the user's settings
    if user_settings:
        return jsonify({
            'dark_mode': user_settings.dark_mode,
            'email_notifications': user_settings.email_notifications,
            'default_language': user_settings.default_language,
        })
    else:
        return jsonify({'dark_mode': False, 'email_notifications': True, 'default_language': 'en'})

@app.route('/fetch_language', methods=['GET'])
def fetch_language():
    # Check if the user is logged in
    if 'username' not in session:
        return jsonify({'error': 'User not logged in'}), 403

    username = session['username']
    user_settings = UserSettings.query.filter_by(username=username).first()

    # If user settings don't exist, return a default value
    if user_settings:
        return jsonify({'default_language': user_settings.default_language})
    else:
        # Default to 'en' if no settings are found
        return jsonify({'default_language': 'en'})

@app.route('/subscribe', methods=['GET'])
def subscribe_page():
    return render_template('subscribe.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    db.create_all()  # Create database tables
    app.run(debug=True)
