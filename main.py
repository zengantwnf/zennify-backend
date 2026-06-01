from flask import Flask, jsonify, request
from flask_cors import CORS
import urllib.request
import urllib.parse
import json
import re

app = Flask(__name__)
CORS(app)

INVIDIOUS_INSTANCES = [
    "https://invidious.fdn.fr",
    "https://inv.nadeko.net", 
    "https://invidious.nerdvpn.de",
    "https://yt.drgnz.club"
]

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())

def search_invidious(query, limit=20):
    for instance in INVIDIOUS_INSTANCES:
        try:
            url = f"{instance}/api/v1/search?q={urllib.parse.quote(query)}&type=video&fields=videoId,title,author,lengthSeconds,videoThumbnails"
            data = fetch_json(url)
            tracks = []
            for v in data[:limit]:
                thumb = ""
                for t in v.get("videoThumbnails", []):
                    if t.get("quality") in ["medium", "high", "maxres"]:
                        thumb = t.get("url", "")
                        break
                if not thumb and v.get("videoThumbnails"):
                    thumb = v["videoThumbnails"][0].get("url", "")
                tracks.append({
                    "id": v.get("videoId"),
                    "title": v.get("title"),
                    "artist": v.get("author", "").replace(" - Topic", ""),
                    "duration": v.get("lengthSeconds", 0),
                    "thumbnail": thumb
                })
            return tracks
        except:
            continue
    return []

def get_stream_invidious(video_id):
    for instance in INVIDIOUS_INSTANCES:
        try:
            url = f"{instance}/api/v1/videos/{video_id}?fields=adaptiveFormats,formatStreams"
            data = fetch_json(url)
            # Try adaptive formats (audio only)
            for f in data.get("adaptiveFormats", []):
                if "audio" in f.get("type", "") and "opus" in f.get("type", ""):
                    return f.get("url")
            for f in data.get("adaptiveFormats", []):
                if "audio" in f.get("type", ""):
                    return f.get("url")
            # Fallback to format streams
            for f in data.get("formatStreams", []):
                return f.get("url")
        except:
            continue
    return None

@app.route('/')
def index():
    return jsonify({"status": "ZenNify Backend Running!", "version": "2.0"})

@app.route('/search')
def search():
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 20))
    if not query:
        return jsonify({'error': 'Query required'}), 400
    try:
        tracks = search_invidious(query, limit)
        return jsonify({'results': tracks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stream/<video_id>')
def stream(video_id):
    if not re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
        return jsonify({'error': 'Invalid video ID'}), 400
    try:
        url = get_stream_invidious(video_id)
        if url:
            return jsonify({'url': url})
        return jsonify({'error': 'Stream not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/trending')
def trending():
    try:
        tracks = search_invidious('top hits 2024', 20)
        return jsonify({'results': tracks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
