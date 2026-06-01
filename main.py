from flask import Flask, jsonify, request
from flask_cors import CORS
import urllib.request
import urllib.parse
import json
import re

app = Flask(__name__)
CORS(app)

def fetch_json(url, data=None, headers={}):
    default_headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
    }
    default_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=default_headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def search_youtube_music(query, limit=20):
    # Use YouTube oEmbed + search scraping via a public API
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={urllib.parse.quote(query)}&type=video&videoCategoryId=10&maxResults={limit}&key=AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY"
        data = fetch_json(url)
        tracks = []
        for item in data.get("items", []):
            vid_id = item["id"]["videoId"]
            snippet = item["snippet"]
            tracks.append({
                "id": vid_id,
                "title": snippet.get("title"),
                "artist": snippet.get("channelTitle", "").replace(" - Topic", ""),
                "duration": 0,
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", "")
            })
        return tracks
    except:
        pass
    
    # Fallback: Use iTunes search
    try:
        url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&entity=song&limit={limit}&media=music"
        data = fetch_json(url)
        tracks = []
        for t in data.get("results", []):
            tracks.append({
                "id": t.get("trackId", ""),
                "title": t.get("trackName"),
                "artist": t.get("artistName"),
                "duration": int(t.get("trackTimeMillis", 0) / 1000),
                "thumbnail": t.get("artworkUrl100", "").replace("100x100", "300x300"),
                "previewUrl": t.get("previewUrl", ""),
                "useItunes": True
            })
        return tracks
    except Exception as e:
        return []

def get_stream_cobalt(video_id):
    try:
        url = "https://api.cobalt.tools/api/json"
        payload = json.dumps({
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "vCodec": "h264",
            "vQuality": "720",
            "aFormat": "mp3",
            "isAudioOnly": True
        }).encode()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = fetch_json(url, data=payload, headers=headers)
        if data.get("status") in ["stream", "redirect", "tunnel"]:
            return data.get("url")
    except:
        pass
    return None

@app.route('/')
def index():
    return jsonify({"status": "ZenNify Backend Running!", "version": "4.0"})

@app.route('/search')
def search():
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 20))
    if not query:
        return jsonify({'error': 'Query required'}), 400
    try:
        tracks = search_youtube_music(query, limit)
        return jsonify({'results': tracks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stream/<video_id>')
def stream(video_id):
    if not re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
        return jsonify({'error': 'Invalid video ID'}), 400
    try:
        url = get_stream_cobalt(video_id)
        if url:
            return jsonify({'url': url})
        return jsonify({'error': 'Stream not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/trending')
def trending():
    try:
        tracks = search_youtube_music('top hits 2024', 20)
        return jsonify({'results': tracks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
