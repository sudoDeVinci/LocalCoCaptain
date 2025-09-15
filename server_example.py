from server.app import USERS, socketio, app
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)