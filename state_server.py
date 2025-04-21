from flask import Flask, request, jsonify
import time
import os
import psutil
import atexit
import csv
import sys
import signal
import threading
from datetime import datetime
from state_server_experiment_logger import StateServerLogger

logger = StateServerLogger()

def handle_shutdown_signal(signum, frame):
    print(f"[State Server] Caught signal {signum}. Exporting metrics and cleaning up.")
    logger.export_all()
    cleanup()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown_signal)   # Ctrl+C
signal.signal(signal.SIGTERM, handle_shutdown_signal)  # kill or termination


app = Flask(__name__)
state_lock = threading.Lock()
state_history = []

# Timestamped filenames
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

@app.route('/update_state', methods=['POST'])
def update_state():
    start_time = time.perf_counter()
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON received"}), 400

    with state_lock:
        state_history.append(data)

    logger.log_request_metrics(start_time)

    return jsonify({"status": "ok"}), 200

@app.route('/get_states', methods=['GET'])
def get_states():
    return jsonify(state_history), 200

@app.route('/get_state', methods=['GET'])
def get_state():
    with state_lock:
        current_state = state_history[-1] if state_history else {}
    return jsonify(current_state)

# Cleanup function to run on exit
def cleanup():
    print("Cleaning up server state...")
    state_history.clear()

atexit.register(cleanup)

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(host='127.0.0.1', port=port)
