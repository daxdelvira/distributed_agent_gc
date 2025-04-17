import time
import tracemalloc
import threading
import csv
import os
from typing import Callable, Dict, List
import matplotlib.pyplot as plt
import numpy as np
import functools

# Use Gruvbox dark theme style
plt.style.use("dark_background")

# Shared metrics list
agent_metrics: List[Dict] = []

def track_time_and_memory(get_label: Callable = lambda self: "unknown"):
    """
    Decorator to measure execution time and peak memory usage.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            thread_id = threading.get_ident()
            agent_label = get_label(self)

            start_time = time.perf_counter()
            tracemalloc.start()

            try:
                result = await func(self, *args, **kwargs)
            finally:
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                end_time = time.perf_counter()

                duration = end_time - start_time
                metric = {
                    "agent": agent_label,
                    "function": func.__name__,
                    "thread_id": thread_id,
                    "duration_sec": duration,
                    "peak_memory_bytes": peak,
                }
                agent_metrics.append(metric)

            return result
        return wrapper
    return decorator

def save_metrics_to_csv_and_cdfs(out_dir: str = "metrics"):
    """
    Saves one CSV and two CDF plots (duration, memory) per agent to a folder.
    """
    if not agent_metrics:
        print("[agent_metrics] No data to save.")
        return

    os.makedirs(out_dir, exist_ok=True)

    # Group by agent
    by_agent: Dict[str, List[Dict]] = {}
    for entry in agent_metrics:
        by_agent.setdefault(entry["agent"], []).append(entry)

    for agent, records in by_agent.items():
        # CSV
        csv_path = os.path.join(out_dir, f"metrics_{agent}.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        print(f"[agent_metrics] Saved CSV for {agent}: {csv_path}")

        # CDF: Duration
        durations = np.array([r["duration_sec"] for r in records])
        if len(durations) > 1:
            _plot_cdf(
                durations,
                xlabel="Duration (seconds)",
                title=f"Active Time CDF: {agent}",
                filename=os.path.join(out_dir, f"cdf_{agent}_duration.png"),
            )

        # CDF: Memory
        memories = np.array([r["peak_memory_bytes"] for r in records])
        if len(memories) > 1:
            _plot_cdf(
                memories,
                xlabel="Peak Memory (bytes)",
                title=f"Peak Memory CDF: {agent}",
                filename=os.path.join(out_dir, f"cdf_{agent}_memory.png"),
            )

def _plot_cdf(data: np.ndarray, xlabel: str, title: str, filename: str):
    data_sorted = np.sort(data)
    cdf = np.arange(1, len(data_sorted) + 1) / len(data_sorted)

    plt.figure(figsize=(8, 5))
    plt.plot(data_sorted, cdf, marker=".", linestyle="none")
    plt.xlabel(xlabel)
    plt.ylabel("Cumulative Probability")
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    print(f"[agent_metrics] Saved CDF plot: {filename}")
