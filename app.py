from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from youtubesearchpython import VideosSearch
import json
import os

app = Flask(__name__)
app.secret_key = 'ilyaas2012'  # Required for session management and flashing messages

# File to store account information
ACCOUNTS_FILE = 'accounts.json'


def load_accounts():
    """Load accounts from the JSON file."""
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    with open(ACCOUNTS_FILE, 'r') as f:
        return json.load(f)


def save_accounts(accounts):
    """Save accounts to the JSON file."""
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(accounts, f)


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
        
        accounts = load_accounts()

        if username in accounts:
            flash('Username already exists!', 'error')
            return redirect(url_for('signup'))

        # Save the account info
        accounts[username] = password
        save_accounts(accounts)
        
        flash('Signup successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        accounts = load_accounts()

        if username in accounts and accounts[username] == password:
            flash('Login successful!', 'success')
            return redirect(url_for('index'))  # Redirect to the main page or wherever you'd like
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)
