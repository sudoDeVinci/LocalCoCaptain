from src.server.app import USERS, socketio, app


if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000)
