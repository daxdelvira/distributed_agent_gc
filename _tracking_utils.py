import time
import tracemalloc
import threading
import psutil
import os
import asyncio
from typing import List, Dict



class LLMTimeTracker:
    def __init__(self, llm_call_duration_list: List[Dict], agent_label: str, function_name: str):
        self.agent_label = agent_label
        self.function_name = function_name
        self.thread_id = threading.get_ident()
        self.llm_call_duration_list = llm_call_duration_list

    def __enter__(self):
        self.start_time = time.perf_counter()
       
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        current, peak = tracemalloc.get_traced_memory()
        
        end_time = time.perf_counter()
        duration = end_time - self.start_time

        llm_call_duration = {
            "agent": self.agent_label,
            "function": self.function_name,
            "thread_id": self.thread_id,
            "duration_sec": duration,
        }
        self.llm_call_duration_list.append(llm_call_duration)

class StateCommLatencyTracker:
    def __init__(self, round_trip_latencies_list: List[Dict], agent_label: str):
        self.round_trip_latencies_list = round_trip_latencies_list
        self.agent_label = agent_label

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end = time.perf_counter()
        latency_ms = (end - self.start) * 1000
        self.round_trip_latencies_list.append((time.time(), latency_ms))

class StateRetrievalLatencyTracker:
    def __init__(self, latency_log: List[Dict], agent_label: str):
        self.latency_log = latency_log
        self.agent_label = agent_label

    def __enter__(self):
        self.start = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end = time.perf_counter()
        latency_ms = (end - self.start) * 1000
        self.latency_log.append({
            "agent": self.agent_label,
            "timestamp": time.time(),
            "latency_ms": latency_ms
        })

class SingleAgentMemorySampler:
    def __init__(self, sample_interval: float = 5.0):
        self.process = psutil.Process(os.getpid())
        self.sample_interval = sample_interval
        self.samples = []
        self.running = False
        self.agent_label = "unknown"
        self.task = None

    async def __aenter__(self):
        self.running = True
        self.task = asyncio.create_task(self._sample_loop())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.running = False
        if self.task:
            await self.task

    async def _sample_loop(self):
        while self.running:
            rss = self.process.memory_info().rss / (1024 * 1024)  # MB
            timestamp = time.time()
            self.samples.append((timestamp, rss))
            print(f"[Sampler] Memory at {rss:.2f} MB")
            await asyncio.sleep(self.sample_interval)

    def export_to_csv(self, filename="memory_trace.csv", agent_label="unknown"):
        with open(filename, "w") as f:
            f.write("agent,timestamp,rss_mb\n")
            for t, rss in self.samples:
                f.write(f"{agent_label},{t},{rss:.2f}\n")
