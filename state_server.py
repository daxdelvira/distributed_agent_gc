from flask import Flask, request, jsonify
import time
import os
import psutil
import atexit
import csv
import threading
from datetime import datetime

app = Flask(__name__)
state_lock = threading.Lock()
state_history = []

# Timestamped filenames
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LATENCY_CSV = f"logs/server_latency_{timestamp}.csv"
MEMORY_CSV = f"logs/server_memory_{timestamp}.csv"

# Create CSV files
latency_log = open(LATENCY_CSV, "w", newline="")
latency_writer = csv.writer(latency_log)
latency_writer.writerow(["timestamp", "latency_ms"])

memory_log = open(MEMORY_CSV, "w", newline="")
memory_writer = csv.writer(memory_log)
memory_writer.writerow(["timestamp", "memory_mb"])

# Memory utility
def get_memory_mb():
    proc = psutil.Process(os.getpid())
    return proc.memory_info().rss / (1024 * 1024)

@app.route('/update_state', methods=['POST'])
def update_state():
    start_time = time.perf_counter()
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON received"}), 400

    with state_lock:
        state_history.append(data)

    latency_ms = (time.perf_counter() - start_time) * 1000
    current_time = time.time()
    memory_mb = get_memory_mb()

    # Log latency and memory
    latency_writer.writerow([current_time, f"{latency_ms:.2f}"])
    memory_writer.writerow([current_time, f"{memory_mb:.2f}"])

    # Flush files to make them viewable during runtime
    latency_log.flush()
    memory_log.flush()

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
    latency_log.close()
    memory_log.close()
    state_history.clear()

atexit.register(cleanup)

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(host='127.0.0.1', port=port)
