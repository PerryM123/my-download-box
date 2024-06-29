import asyncio
import socketio
from aiohttp import web
import uvicorn

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=[
    # TODO: dotenvにできるか確認
    'http://localhost:3000'
    # TODO: works for localhost but not ip host???
    # 'http://192.168.1.8:3000'
])
app = web.Application()

# Global
counter = 0
sidList = []

async def emit_numbers():
    global counter
    while True:
        counter += 1
        print(f"Counter: {counter}") 
        print(sidList)
        await sio.emit('number', counter)
        print("============")
        await asyncio.sleep(1)

@sio.event
async def connect(sid, environ):
    sio.start_background_task(emit_numbers)
    print(f"Client connected: {sid}")
    sidList.append(sid)
    # TODO: もしかしていらないかも ー＞ await sio.emit('number', counter, room=sid)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    global sidList
    sidList = [user for user in sidList if user != sid]

# Main
if __name__ == '__main__':
    app = socketio.ASGIApp(sio, app)
    uvicorn.run(app, host='127.0.0.1', port=5000)
