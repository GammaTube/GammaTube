from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String
from werkzeug.security import generate_password_hash, check_password_hash
from youtubesearchpython import VideosSearch, ChannelsSearch, PlaylistsSearch, Video, ResultMode
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
    # Check if the user is logged in by checking the session
    if 'username' not in session:
        print("User not logged in, redirecting to login page")
        return redirect(url_for('login'))
    
    print("Index route accessed")
    return render_template('index.html')


@app.route('/search')
def search_page():
    # Check if the user is logged in by checking the session
    if 'username' not in session:
        print("User not logged in, redirecting to login page")
        return redirect(url_for('login'))
        
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
    # Check if the user is logged in by checking the session
    if 'username' not in session:
        print("User not logged in, redirecting to login page")
        return redirect(url_for('login'))
    
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
    # Check if the user is logged in by checking the session
    if 'username' not in session:
        print("User not logged in, redirecting to login page")
        return redirect(url_for('login'))
    
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
    # Check if the user is logged in by checking the session
    if 'username' not in session:
        print("User not logged in, redirecting to login page")
        return redirect(url_for('login'))
    
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
    # Check if the user is logged in by checking the session
    if 'username' not in session:
        print("User not logged in, redirecting to login page")
        return redirect(url_for('login'))
    
    video_id = request.args.get('v')
    print(f"Watch route accessed with video_id: {video_id}")
    
    # Retrieve the username from the session
    username = session['username']
    
    # Fetch video name using the video ID
    try:
        video = Video.get(f'https://www.youtube.com/watch?v={video_id}', mode=ResultMode.json)
        video_name = video['title']
        print(f"Fetched video name: {video_name}")
    except Exception as e:
        print(f"Failed to fetch video name: {e}")
        video_name = 'Unknown'  # Default value if fetching fails
    
    # Log the video in watch history with the video name
    new_history_entry = WatchHistory(username=username, video_id=video_id, video_name=video_name)
    db.session.add(new_history_entry)
    db.session.commit()
    
    return render_template('watch.html', video_id=video_id)


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
            return redirect(url_for('index'))  # Redirect to the main page or wherever you'd like
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/playlist')
def playlist():
     # Check if the user is logged in by checking the session
    if 'username' not in session:
        print("User not logged in, redirecting to login page")
        return redirect(url_for('login'))
    
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
        return redirect(url_for('login'))
    
    username = session['username']  # Retrieve the username from the session
    
    # Query the watch history using the username instead of user_id
    history = WatchHistory.query.filter_by(username=username).order_by(WatchHistory.timestamp.desc()).all()
    print(f"Watch history accessed for user: {username}")

    if history:
        return render_template('watch_history.html', history=history)
    else:
        return render_template('watch_history.html', error="No watch history found.")


if __name__ == '__main__':
    db.create_all()  # Create database tables
    app.run(debug=True)
