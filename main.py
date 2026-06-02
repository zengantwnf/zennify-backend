from flask import Flask, jsonify, request
from flask_cors import CORS
import yt_dlp
import re
import os

app = Flask(__name__)
CORS(app)

COOKIES_FILE = os.path.join(os.path.dirname(__file__), 'cookies.txt')

def search_youtube(query, limit=20):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'default_search': 'ytsearch',
        'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
        tracks = []
        for entry in result.get('entries', []):
            tracks.append({
                'id': entry.get('id'),
                'title': entry.get('title'),
                'artist': entry.get('uploader', '').replace(' - Topic', ''),
                'duration': entry.get('duration', 0),
                'thumbnail': f"https://img.youtube.com/vi/{entry.get('id')}/hqdefault.jpg",
            })
        return tracks

def get_audio_url(video_id):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'worstaudio/worst',  # Get any available audio
        'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            # Try to get audio only format first
            formats = info.get('formats', [])
            
            # Priority: audio only formats
            for f in formats:
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('url'):
                    return f.get('url')
            
            # Fallback: any format with audio
            for f in formats:
                if f.get('acodec') != 'none' and f.get('url'):
                    return f.get('url')
            
            # Last resort: direct URL
            if info.get('url'):
                return info.get('url')
                
    except Exception as e:
        # Try with different format
        try:
            ydl_opts['format'] = 'best'
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                return info.get('url')
        except:
            pass
    return None

@app.route('/')
def index():
    return jsonify({
        'status': 'ZenNify Backend Running!', 
        'version': '7.0',
        'cookies': os.path.exists(COOKIES_FILE)
    })

@app.route('/search')
def search():
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 20))
    if not query:
        return jsonify({'error': 'Query required'}), 400
    try:
        tracks = search_youtube(query, limit)
        return jsonify({'results': tracks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stream/<video_id>')
def stream(video_id):
    if not re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
        return jsonify({'error': 'Invalid video ID'}), 400
    try:
        url = get_audio_url(video_id)
        if url:
            return jsonify({'url': url})
        return jsonify({'error': 'Stream not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/trending')
def trending():
    try:
        tracks = search_youtube('top hits 2024', 20)
        return jsonify({'results': tracks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

