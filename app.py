from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


users = {}

@app.route('/')
def index():
    return render_template('index.html')  # your frontend HTML file

@socketio.on('join')
def handle_join(data):
    username = data.get('username', 'Anonymous')
    users[request.sid] = username
    emit('system', f"{username} has joined the chat.", broadcast=True)
    emit('user_list', list(users.values()), broadcast=True)

@socketio.on('message')
def handle_message(data):
    username = users.get(request.sid, 'Unknown')
    msg_data = {
        'from': username,
        'content': data,
        'timestamp': datetime.utcnow().isoformat()
    }
    emit('message', msg_data, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    username = users.pop(request.sid, 'Unknown')
    emit('system', f"{username} has left the chat.", broadcast=True)
    emit('user_list', list(users.values()), broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
