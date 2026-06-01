from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
import urllib.request
import urllib.parse
import json
import re

app = Flask(__name__)
CORS(app)

def fetch_json(url, data=None, headers={}):
    default_headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
    default_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=default_headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def search_tracks(query, limit=20):
    # iTunes search (reliable, no auth needed)
    try:
        url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&entity=song&limit={limit}&media=music"
        data = fetch_json(url)
        tracks = []
        for t in data.get("results", []):
            tracks.append({
                "id": str(t.get("trackId", "")),
                "title": t.get("trackName"),
                "artist": t.get("artistName"),
                "duration": int(t.get("trackTimeMillis", 0) / 1000),
                "thumbnail": t.get("artworkUrl100", "").replace("100x100bb", "300x300bb"),
                "previewUrl": t.get("previewUrl", ""),
                "useItunes": True
            })
        return tracks
    except Exception as e:
        return []

def get_stream_url(video_id):
    # Try multiple Piped instances
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://piped-api.garudalinux.org", 
        "https://api.piped.projectsegfau.lt",
        "https://pipedapi.in.projectsegfau.lt",
        "https://watchapi.whatever.social"
    ]
    
    for instance in instances:
        try:
            data = fetch_json(f"{instance}/streams/{video_id}")
            streams = data.get("audioStreams", [])
            # Sort by bitrate, get best
            streams.sort(key=lambda x: x.get("bitrate", 0), reverse=True)
            for s in streams:
                if s.get("url"):
                    return s["url"]
        except:
            continue
    
    return None

@app.route('/')
def index():
    return jsonify({"status": "ZenNify Backend Running!", "version": "5.0"})

@app.route('/search')
def search():
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 20))
    if not query:
        return jsonify({'error': 'Query required'}), 400
    tracks = search_tracks(query, limit)
    return jsonify({'results': tracks})

@app.route('/stream/<video_id>')
def stream(video_id):
    if not re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
        return jsonify({'error': 'Invalid video ID'}), 400
    url = get_stream_url(video_id)
    if url:
        return jsonify({'url': url})
    return jsonify({'error': 'Stream not found'}), 404

@app.route('/preview/<track_id>')
def preview(track_id):
    # Get iTunes preview URL
    try:
        data = fetch_json(f"https://itunes.apple.com/lookup?id={track_id}")
        result = data.get("results", [{}])[0]
        preview_url = result.get("previewUrl", "")
        if preview_url:
            return jsonify({'url': preview_url})
    except:
        pass
    return jsonify({'error': 'Preview not found'}), 404

@app.route('/trending')
def trending():
    try:
        data = fetch_json("https://itunes.apple.com/us/rss/topsongs/limit=20/json")
        entries = data.get("feed", {}).get("entry", [])
        tracks = []
        for e in entries:
            track_id = e.get("id", {}).get("attributes", {}).get("im:id", "")
            tracks.append({
                "id": track_id,
                "title": e.get("im:name", {}).get("label", ""),
                "artist": e.get("im:artist", {}).get("label", ""),
                "duration": 0,
                "thumbnail": e.get("im:image", [{}])[-1].get("label", ""),
                "useItunes": True
            })
        return jsonify({'results': tracks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
