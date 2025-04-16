import json
import time
import requests
from typing import Dict, Any

#Get the json from the returned string
def extract_valid_json(text: str) -> Dict[str, Any] | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None

#Make sure all the keys in the candidate dict are allowed
def validate_keys(candidate: Dict[str, Any], allowed_keys: set) -> bool:
    return all(k in allowed_keys for k in candidate)



def apply_state_update(shared_state, updates: Dict[str, Any]):
    shared_state.update(updates)
    print(f"✅ Updated state with: {updates}")

def send_state_update(agent_id, state, state_server_url):
    payload = {
        "agent_id": agent_id,
        "timestamp": time.time(),
        "state": state
    }

    try:
        response = requests.post(state_server_url, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to send state update: {e}")