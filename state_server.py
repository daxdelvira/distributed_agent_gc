import sys
from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory log of states (could also be persisted or dumped periodically)
state_history = []

@app.route('/update_state', methods=['POST'])
def update_state():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    state_history.append(data)
    return jsonify({"status": "ok", "received": data}), 200

@app.route('/get_states', methods=['GET'])
def get_states():
    return jsonify(state_history), 200

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(host='127.0.0.1', port=port)
    app.run(host='127.0.0.1', port=5000) #Switch this up based on ports available on program launch
