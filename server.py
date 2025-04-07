import flask
from flask import request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import requests
app = flask.Flask(__name__)
CORS(app, origins=["http://localhost:5173"])  # Specify your frontend URL
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:5173"])

@app.route('/prompt_response', methods=['POST'])
def prompt_response():
    data = request.json
    print(f"Received data: {data}")

    socketio.emit('prompt_response', data)

    return jsonify({"status": "success", "data": data})



if __name__ == '__main__':
    socketio.run(app, port=8000, host="0.0.0.0", debug=True)
