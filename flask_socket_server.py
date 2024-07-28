import os
from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
from urllib.parse import urlparse
import re
from yt_dlp import YoutubeDL

app = Flask(__name__, static_folder='static', static_url_path='/')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app, supports_credentials=True, responses={r"/*": {"origins": "*"}})

# global 
download_progress = 0
download_urls = []
thread = None

@socketio.on('connect')
def handle_connect():
    print('handle_connect')
    global download_urls
    emit('updateUrls', download_urls, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    print('handle_disconnect')

@socketio.on('message')
def handle_message(message):
    emit('message', f'{request.sid} => {message}', broadcast=True)

@socketio.on('addUrl')
def add_url(downloadUrl):
    global thread
    global download_urls
    
    download_urls.append(downloadUrl)
    emit('updateUrls', download_urls, broadcast=True)

    if thread is None or not thread.is_alive():
        print("Starting a new thread.")
        # TODO: 以下だと３つのthreadが走ってしまうので修正必須
        if ".m3u8" in downloadUrl:
            thread = socketio.start_background_task(download_m3u8_video, downloadUrl)
            print("This is m3u8")
        elif "youtube.com" in downloadUrl:
            print("This is youtube")
            thread = socketio.start_background_task(download_youtube_video, downloadUrl)
        else:
            print("This is other")
            thread = socketio.start_background_task(download_file, downloadUrl)
    else:
        print(f"Thread is still alive: {thread.is_alive()}")

def get_filename_from_cd(content_disposition):
    if not content_disposition:
        return None
    filename = re.findall('filename=(.+)', content_disposition)
    if filename:
        return filename[0].strip('"')
    return None

def ytdlp_hook(d):
    if d['status'] == 'finished':
        file_tuple = os.path.split(os.path.abspath(d['filename']))
        print("Done downloading {}".format(file_tuple[1]))
    if d['status'] == 'downloading':
        total_bytes = 0
        if 'total_bytes' in d:
            total_bytes = d['total_bytes']
        elif 'total_bytes_estimate' in d:
            total_bytes = d['total_bytes_estimate']
        percentage = float('%.2f'%((d["downloaded_bytes"] / (total_bytes or 0)) * 100))
        socketio.emit(
            'downloadProgress', 
            {
                'estimated_time': d['_eta_str'],
                'download_speed': d['_speed_str'],
                'percentage': percentage,
                'total_bytes': d['_total_bytes_str'],
                'total_bytes_estimate': d['_total_bytes_estimate_str'],
                'downloaded_bytes': d['_downloaded_bytes_str'],
                'elapsed_time': d['_elapsed_str'],
                'default_template': d['_default_template'],
                'title': d['info_dict']['title'],
            }
        )

def download_youtube_video(url):
    print(f"download_youtube_video: url: {url}")
    ydl_opts = {
        # TODO: quicktimeでも再生できるフォーマットは調査必須
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',  # Ensure high quality MP4
        'outtmpl': os.path.join('downloads', '%(title)s.%(ext)s'),
        'progress_hooks': [ytdlp_hook]
    }
    URLS = [url]
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download(URLS)

def download_m3u8_video(url):
    print(f"download_m3u8_video: url: {url}")
    # TODO: headerのrefererとuser_agentを追加

def download_file(downloadUrl):
    print(f"download_file: url: {downloadUrl}")
    global download_progress
    # TODO: Download the first element in the list. If done, pop first element and continue on until the list is 0
    global download_urls

    response = requests.get(downloadUrl, stream=True)
    total_length = int(response.headers.get('content-length'))

    if total_length is None:
        emit('downloadProgress', {'percentage': 0})
        return
    
    filename = None
    content_disposition = response.headers.get('content-disposition')
    if content_disposition:
        filename = get_filename_from_cd(content_disposition)
    if not filename:
        parsed_url = urlparse(downloadUrl)
        filename = os.path.basename(parsed_url.path)
    downloaded = 0
    chunk_size = 1024  # 1 KB
    file_path = f'./downloads/{filename}'

    # Check if file already exists
    if os.path.exists(file_path):
        socketio.emit('alreadyDownloaded', {'file_path': file_path})
        return

    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                progress = int((downloaded / total_length) * 100)
                if progress != download_progress:
                    download_progress = progress
                    socketio.emit('downloadProgress', {'percentage': progress})
    socketio.emit('downloadComplete', {'file_path': file_path})

if __name__ == '__main__':
    # TODO: host名をenvから読み込むように修正必須
    socketio.run(app, host='192.168.1.8', port=3001, debug=True)




