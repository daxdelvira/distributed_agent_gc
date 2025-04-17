"""
We're going to create a shared memory object for the agents to update their state. We'll use locks so agents don't overwrite 
each other.
"""
from dataclasses import dataclass, field
from typing import Any, Dict
from multiprocessing import Lock, Manager
from unified_state_config import PREDEFINED_STATE  # Assuming this is defined elsewhere

class UnifiedState:
    def __init__(self, schema: Dict[str, Any]):
        self.manager = Manager()
        self.memory = self.manager.dict()
        self.lock = Lock()
        self.schema = schema
    
    def set(self, key: str, value: Any) -> None:
        with self.lock:
            if key in self.schema:
                self.memory[key] = value
            else:
                raise KeyError(f"Key '{key}' not in schema.")
    
    def get(self, key: str) -> Any:
        with self.lock:
            if key in self.memory:
                return self.memory[key]
            else:
                raise KeyError(f"Key '{key}' not found in memory.")
    

    def update(self, updates: Dict[str, Any]) -> None:
        with self.lock:
            for key, value in updates.items():
                if key in self.schema:
                    self.memory[key] = value
                else:
                    raise KeyError(f"Key '{key}' not in schema.")
                
shared_unified_state = UnifiedState(schema=PREDEFINED_STATE)  # Assuming PREDEFINED_STATE is defined elsewhere