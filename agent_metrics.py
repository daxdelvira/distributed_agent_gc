# agent_metrics.py
import time
import atexit
import psutil
import socket
import os
from datetime import datetime

_process = psutil.Process()
_start_time = time.time()

def init_metrics(agent_name: str, log_dir: str = "logs"):
    os.makedirs(log_dir, exist_ok=True)
    hostname = socket.gethostname()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _metrics_file = os.path.join(log_dir, f"{agent_name}_metrics_{timestamp}.txt")

    def log_metrics():
        end_time = time.time()
        cpu = _process.cpu_times()
        mem = _process.memory_info().rss / (1024 * 1024)  # MB
        with open(_metrics_file, "w") as f:
            f.write(f"Agent: {agent_name}\n")
            f.write(f"Host: {hostname}\n")
            f.write(f"Start Time: {datetime.fromtimestamp(_start_time)}\n")
            f.write(f"End Time: {datetime.fromtimestamp(end_time)}\n")
            f.write(f"Wall-clock Duration: {end_time - _start_time:.2f} seconds\n")
            f.write(f"User CPU Time: {cpu.user:.2f} seconds\n")
            f.write(f"System CPU Time: {cpu.system:.2f} seconds\n")
            f.write(f"Peak Memory (RSS): {mem:.2f} MB\n")

    atexit.register(log_metrics)
    print(f"Metrics logging initialized for agent '{agent_name}'. Logs will be saved to '{_metrics_file}'.")