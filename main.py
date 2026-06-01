from flask import Flask, jsonify, request
from flask_cors import CORS
import urllib.request
import urllib.parse
import json
import re

app = Flask(__name__)
CORS(app)

PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://piped-api.garudalinux.org",
    "https://api.piped.projectsegfau.lt",
    "https://pipedapi.in.projectsegfau.lt"
]

def fetch_json(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json'
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def search_piped(query, limit=20):
    for instance in PIPED_INSTANCES:
        try:
            url = f"{instance}/search?q={urllib.parse.quote(query)}&filter=music_songs"
            data = fetch_json(url)
            tracks = []
            for v in data.get("items", [])[:limit]:
                tracks.append({
                    "id": v.get("url", "").replace("/watch?v=", ""),
                    "title": v.get("title"),
                    "artist": v.get("uploaderName", "").replace(" - Topic", ""),
                    "duration": v.get("duration", 0),
                    "thumbnail": v.get("thumbnail", "")
                })
            if tracks:
                return tracks
        except:
            continue
    return []

def get_stream_piped(video_id):
    for instance in PIPED_INSTANCES:
        try:
            url = f"{instance}/streams/{video_id}"
            data = fetch_json(url)
            # Get best audio stream
            for s in data.get("audioStreams", []):
                if s.get("mimeType", "").startswith("audio/"):
                    return s.get("url")
        except:
            continue
    return None

@app.route('/')
def index():
    return jsonify({"status": "ZenNify Backend Running!", "version": "3.0"})

@app.route('/search')
def search():
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 20))
    if not query:
        return jsonify({'error': 'Query required'}), 400
    try:
        tracks = search_piped(query, limit)
        return jsonify({'results': tracks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stream/<video_id>')
def stream(video_id):
    if not re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
        return jsonify({'error': 'Invalid video ID'}), 400
    try:
        url = get_stream_piped(video_id)
        if url:
            return jsonify({'url': url})
        return jsonify({'error': 'Stream not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/trending')
def trending():
    try:
        tracks = search_piped('top hits 2024', 20)
        return jsonify({'results': tracks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
