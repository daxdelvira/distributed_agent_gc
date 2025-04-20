import os
import time
import json
import atexit
import asyncio
import csv
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import psutil
import requests

from _tracking_utils import LLMTimeTracker, StateCommLatencyTracker, SingleAgentMemorySampler
from experiment_context import ExperimentContext

class AgentExperimentLogger:
    def __init__(self, experiment: ExperimentContext, agent_label: Optional[str] = None):
        self.experiment = experiment
        self.agent_label = agent_label or "unknown"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Metric buffers
        self.llm_metrics: List[Dict] = []
        self.state_update_latencies: List[Tuple[float, float]] = []
        self.memory_sampler: Optional[SingleAgentMemorySampler] = None

        # Log file paths
        self.llm_csv = f"logs/{self.agent_label}_llm_metrics_{self.timestamp}.csv"
        self.comm_csv = f"logs/{self.agent_label}_comm_latency_{self.timestamp}.csv"
        self.memory_csv = f"logs/{self.agent_label}_memory_{self.timestamp}.csv"

        atexit.register(self.export_all)

    def track_llm(self, function_name: str):
        if self.experiment.llm_latency:
            return LLMTimeTracker(self.llm_metrics, self.agent_label, function_name)
        return _null_context()

    def track_comm_latency(self):
        if self.experiment.state_update_comms:
            return StateCommLatencyTracker(self.state_update_latencies, self.agent_label)
        return _null_context()

    async def track_memory(self):
        if self.experiment.per_agent_memory:
            print("[AgentExperimentLogger] Starting memory sampling...")
            self.memory_sampler = SingleAgentMemorySampler()
            await self.memory_sampler.__aenter__()
        return self

    async def stop_memory(self):
        if self.memory_sampler:
            await self.memory_sampler.__aexit__(None, None, None)

    def export_all(self):
        os.makedirs("logs", exist_ok=True)
        print(f"Exporting memory? {self.memory_sampler is not None}")

        # Export LLM metrics
        if self.experiment.llm_latency:
            with open(self.llm_csv, "w") as f:
                f.write("agent,function,thread_id,duration_sec\n")
                for row in self.llm_metrics:
                    f.write(f"{row['agent']},{row['function']},{row['thread_id']},{row['duration_sec']:.4f}\n")

        # Export comm latencies
        if self.experiment.state_update_comms:
            with open(self.comm_csv, "w") as f:
                f.write("agent,timestamp,latency_ms\n")
                for ts, lat in self.state_update_latencies:
                    f.write(f"{self.agent_label},{ts},{lat:.2f}\n")

        # Export memory samples
        if self.experiment.per_agent_memory and self.memory_sampler:
            self.memory_sampler.export_to_csv(filename=self.memory_csv, agent_label=self.agent_label)


class _null_context:
    def __enter__(self): pass
    def __exit__(self, *args): pass
