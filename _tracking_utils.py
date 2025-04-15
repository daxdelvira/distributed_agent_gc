import time
import tracemalloc
import threading
from typing import List, Dict

export_metrics: List[Dict] = []

class TimeAndMemoryTracker:
    def __init__(self, agent_label: str, function_name: str):
        self.agent_label = agent_label
        self.function_name = function_name
        self.thread_id = threading.get_ident()

    def __enter__(self):
        self.start_time = time.perf_counter()
        tracemalloc.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end_time = time.perf_counter()
        duration = end_time - self.start_time

        metric = {
            "agent": self.agent_label,
            "function": self.function_name,
            "thread_id": self.thread_id,
            "duration_sec": duration,
            "peak_memory_bytes": peak,
        }
        export_metrics.append(metric)