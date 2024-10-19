from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from youtubesearchpython import VideosSearch, ChannelsSearch, PlaylistsSearch

app = Flask(__name__)
app.secret_key = 'ilyaas2012'  # Required for session management and flashing messages

# Configuration for the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounts.db'  # Update with your DB URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# User model for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

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
    print(f"Watch route accessed with video_id: {video_id}")
    return render_template('watch.html', video_id=video_id)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Expecting JSON data in the request
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify(success=False, message='Username and password are required!'), 400

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify(success=False, message='Username already exists!'), 400

        # Hash the password before storing it
        hashed_password = generate_password_hash(password, method='sha256')

        # Create a new user and add it to the database
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return jsonify(success=True, message='Signup successful! You can now log in.'), 201

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Retrieve the user from the database
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            flash('Login successful!', 'success')
            return redirect(url_for('index'))  # Redirect to the main page or wherever you'd like
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
    db.create_all()  # Create database tables
    app.run(debug=True)
