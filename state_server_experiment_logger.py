import os
import time
import csv
import psutil
import atexit
from datetime import datetime
from typing import List, Tuple

class StateServerLogger:
    def __init__(self, label: str = "state_server"):
        self.label = label
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Buffers
        self.latencies: List[Tuple[float, float]] = []
        self.memory_samples: List[Tuple[float, float]] = []

        # File paths
        self.latency_csv = f"logs/{label}_latency_{self.timestamp}.csv"
        self.memory_csv = f"logs/{label}_memory_{self.timestamp}.csv"

        atexit.register(self.export_all)

    def log_request_metrics(self, start_time: float):
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        timestamp = time.time()
        memory_mb = self._get_memory_mb()

        self.latencies.append((timestamp, latency_ms))
        self.memory_samples.append((timestamp, memory_mb))

    def export_all(self):
        os.makedirs("logs", exist_ok=True)

        with open(self.latency_csv, "w") as f:
            f.write("label,timestamp,latency_ms\n")
            for ts, latency in self.latencies:
                f.write(f"{self.label},{ts},{latency:.2f}\n")

        with open(self.memory_csv, "w") as f:
            f.write("label,timestamp,memory_mb\n")
            for ts, mem in self.memory_samples:
                f.write(f"{self.label},{ts},{mem:.2f}\n")

    def _get_memory_mb(self) -> float:
        proc = psutil.Process(os.getpid())
        return proc.memory_info().rss / (1024 * 1024)
