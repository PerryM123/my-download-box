from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import time

app = Flask(__name__, static_folder='static', static_url_path='/')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app, supports_credentials=True, responses={r"/*": {"origins": "*"}})

# global 
counter = 0
downloadUrls = []
thread = None

@socketio.on('connect')
def handle_connect():
    print('handle_connect')
    global downloadUrls
    emit('updateUrls', downloadUrls, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    print('handle_disconnect')

@socketio.on('message')
def handle_message(message):
    emit('message', f'{request.sid} => {message}', broadcast=True)

@socketio.on('addUrl')
def add_url(message):
    global thread
    global downloadUrls
    
    downloadUrls.append(message)
    emit('updateUrls', downloadUrls, broadcast=True)

    if thread is None or not thread.is_alive():
        print("Starting a new thread.")
        thread = socketio.start_background_task(emit_numbers)
    else:
        print(f"Thread is still alive: {thread.is_alive()}")

def emit_numbers():
    global counter
    counter = 0
    print(f"emit_numbers: counter: {counter}")
    while counter < 100:
        counter += 1
        socketio.emit('number', counter)
        print(f"Counter: {counter}") 
        print("============")
        time.sleep(0.1)

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)

