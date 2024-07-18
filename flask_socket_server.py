import os
from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
from urllib.parse import urlparse
import re

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
def add_url(message):
    global thread
    global download_urls
    
    download_urls.append(message)
    emit('updateUrls', download_urls, broadcast=True)

    if thread is None or not thread.is_alive():
        print("Starting a new thread.")
        thread = socketio.start_background_task(download_file, message)
    else:
        print(f"Thread is still alive: {thread.is_alive()}")

def get_filename_from_cd(content_disposition):
    if not content_disposition:
        return None
    filename = re.findall('filename=(.+)', content_disposition)
    if filename:
        return filename[0].strip('"')
    return None

def download_youtube_video(url):
    print(f"download_youtube_video: url: {url}")
    # TODO

def download_file(url):
    print(f"download_file: url: {url}")
    global download_progress
    # TODO: Download the first element in the list. If done, pop first element and continue on until the list is 0
    global download_urls

    response = requests.get(url, stream=True)
    total_length = int(response.headers.get('content-length'))

    if total_length is None:
        emit('downloadProgress', {'percentage': 0})
        return
    
    filename = None
    content_disposition = response.headers.get('content-disposition')
    if content_disposition:
        filename = get_filename_from_cd(content_disposition)
    if not filename:
        parsed_url = urlparse(url)
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
    socketio.run(app, host='192.168.1.8', port=443, debug=True, ssl_context=('./certs/server.crt', './certs/server.key'))




