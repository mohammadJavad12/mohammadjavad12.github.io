from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime
from pathlib import Path
import json
import os

app = Flask(__name__,template_folder='Templates')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

users = {}
MESSAGE_FILE = Path("messages.json")


# --- Message file helpers ---
def load_messages(limit=50):
    if not MESSAGE_FILE.exists():
        return []
    try:
        with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
            messages = json.load(f)
            return messages[-limit:]
    except Exception:
        return []

def save_message(msg):
    messages = []
    if MESSAGE_FILE.exists():
        try:
            with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
                messages = json.load(f)
        except Exception:
            pass
    messages.append(msg)
    with open(MESSAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f)


# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')


# --- Socket Events ---
@socketio.on('join')
def handle_join(data):
    username = data.get('username', 'Anonymous')
    users[request.sid] = username

    emit('system', f"{username} has joined the chat.", broadcast=True)
    emit('user_list', list(users.values()), broadcast=True)

    # Send previous messages
    for msg in load_messages():
        emit('message', msg, room=request.sid)


@socketio.on('message')
def handle_message(data):
    username = users.get(request.sid, 'Unknown')
    msg_data = {
        'from': username,
        'content': data,
        'timestamp': datetime.utcnow().isoformat()
    }

    save_message(msg_data)
    emit('message', msg_data, broadcast=True)


@socketio.on('disconnect')
def handle_disconnect():
    username = users.pop(request.sid, 'Unknown')
    emit('system', f"{username} has left the chat.", broadcast=True)
    emit('user_list', list(users.values()), broadcast=True)


# --- Run ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port,allow_unsafe_werkzeug=True)
