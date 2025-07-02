from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import Flask, request
from flask_cors import CORS

USERS: dict[str, str] = {}
"""
Map of user session IDS to usernames
"""

AUDICONFIGS: dict[str, dict[str, str | int]] = {}
"""
Map of user session IDS to audio configurations
"""

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'some secret key'
CORS(app,resources={r"/*":{"origins":"*"}})
socketio = SocketIO(app,cors_allowed_origins="*")


@socketio.on('join')
def handle_join(username: str):
    if not username:
        username = "Anonymous"
    
    USERS.update({request.sid: username})  # Store username by session ID
    join_room(username)  # Each user gets their own "room"
    emit("join::ACK", username, room=request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    username = USERS.pop(request.sid, "Anonymous")
    emit("message", f"{username} left the chat", broadcast=True)


@socketio.on('audio::config')
def handle_audio_config(config: dict[str, int]):
    session_id = request.sid
    AUDICONFIGS.update({session_id: config})
    emit('audio::config::ACK', AUDICONFIGS[session_id], room=session_id)
    print(f"Audio configuration for {USERS.get(session_id, 'Unknown')} updated: {AUDICONFIGS[session_id]}")

