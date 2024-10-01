from flask import Flask, render_template, jsonify, request
from youtubesearchpython import VideosSearch, PlaylistsSearch

app = Flask(__name__)

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
            # Search for both videos and playlists
            video_search = VideosSearch(query, limit=10)
            playlist_search = PlaylistsSearch(query, limit=10)

            video_results = video_search.result()
            playlist_results = playlist_search.result()

            items = []

            # Add video results
            for item in video_results['result']:
                title = item['title']
                video_url = 'https://www.youtube.com/watch?v=' + item['id']
                thumbnail = item['thumbnails'][0]['url'] if item['thumbnails'] else 'https://via.placeholder.com/120x90'
                
                items.append({
                    'type': 'video',
                    'title': title,
                    'src': video_url,
                    'thumbnail': thumbnail
                })

            # Add playlist results
            for item in playlist_results['result']:
                title = item['title']
                playlist_url = 'https://www.youtube.com/playlist?list=' + item['id']
                thumbnail = item['thumbnails'][0]['url'] if item['thumbnails'] else 'https://via.placeholder.com/120x90'
                
                items.append({
                    'type': 'playlist',
                    'title': title,
                    'src': playlist_url,
                    'thumbnail': thumbnail
                })

            return render_template('search.html', items=items, query=query)

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
        # Search for both videos and playlists
        video_search = VideosSearch(query, limit=10)
        playlist_search = PlaylistsSearch(query, limit=10)

        video_results = video_search.result()
        playlist_results = playlist_search.result()

        items = []

        # Add video results
        for item in video_results['result']:
            title = item['title']
            video_url = 'https://www.youtube.com/watch?v=' + item['id']
            thumbnail = item['thumbnails'][0]['url'] if item['thumbnails'] else 'https://via.placeholder.com/120x90'
            
            items.append({
                'type': 'video',
                'title': title,
                'src': video_url,
                'thumbnail': thumbnail
            })

        # Add playlist results
        for item in playlist_results['result']:
            title = item['title']
            playlist_url = 'https://www.youtube.com/playlist?list=' + item['id']
            thumbnail = item['thumbnails'][0]['url'] if item['thumbnails'] else 'https://via.placeholder.com/120x90'
            
            items.append({
                'type': 'playlist',
                'title': title,
                'src': playlist_url,
                'thumbnail': thumbnail
            })

        return jsonify(items)

    except Exception as e:
        print(f"Error during search: {e}")
        return jsonify({'error': 'An error occurred during the search'}), 500

@app.route('/watch')
def watch():
    video_id = request.args.get('v')
    print(f"Watch route accessed with video_id: {video_id}")
    return render_template('watch.html', video_id=video_id)

if __name__ == '__main__':
    app.run(debug=True)
