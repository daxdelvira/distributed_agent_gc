import time
import tracemalloc
import threading
import psutil
import os
import asyncio
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

class MemorySampler:
    def __init__(self, sample_interval: float = 5.0):
        self.process = psutil.Process(os.getpid())
        self.sample_interval = sample_interval
        self.samples = []
        self.running = False

    async def start_sampling(self):
        self.running = True
        while self.running:
            rss = self.process.memory_info().rss / (1024 * 1024)  # MB
            timestamp = time.time()
            self.samples.append((timestamp, rss))
            await asyncio.sleep(self.sample_interval)

    def stop(self):
        self.running = False

    def average_rss(self):
        if not self.samples:
            return 0.0
        return sum(rss for _, rss in self.samples) / len(self.samples)

    def export_to_csv(self, filename="memory_trace.csv", agent_label="unknown"):
        with open(filename, "w") as f:
            f.write("agent,timestamp,rss_mb\n")
            for t, rss in self.samples:
                f.write(f"{agent_label},{t},{rss:.2f}\n")