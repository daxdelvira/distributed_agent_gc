class ExperimentContext:
    def __init__(self, mode: str):
        self.mode = mode
        self.llm_latency = mode == "llm-latency"
        self.per_agent_memory = mode == "per-agent-memory"
        self.central_log_memory = mode == "central-log-memory"
        self.state_update_comms = mode == "state-update-comms"