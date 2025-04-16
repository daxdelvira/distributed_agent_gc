import subprocess
import time
import os
import argparse
import json
import socket
from unified_state import UnifiedState
from unified_state_config import ONE_VAR_STATE, FIVE_VAR_STATE, TEN_VAR_STATE, FIFTY_VAR_STATE, HUNDRED_VAR_STATE # Ensure this is defined in unified_state.py
from multiprocessing import Process, Queue
from state_server import state_server


#-------------------------------
# Argument parsing
#-------------------------------
def parse_args():
    parser = argparse.ArgumentParse()
    parser.add_argument("--state-vars", type=str, default="1", choices=[1, 5, 10, 50, 100], help="Number of state variables to use (1, 5, 10, 50, 100)")
    parser.add_argument("--experiment", type=str, default="none", choices=["llm-latency", "per-agent-memory", "central-log-memory", "state-update-comms"], help="Experiment to run")
    return parser.parse_args()

args = parse_args()
print(f"Running experiment: {args.experiment} with {args.state_vars} state variables")

# ------------------------------------------
# Create unified state w/ith selected schema
# ------------------------------------------

state_map = {
    1: ONE_VAR_STATE,
    5: FIVE_VAR_STATE,
    10: TEN_VAR_STATE,
    50: FIFTY_VAR_STATE,
    100: HUNDRED_VAR_STATE,
}
selected_state = state_map[args.state_vars]
unified_state = UnifiedState(schema=selected_state)

# Create log directory if not exists
os.makedirs("logs", exist_ok=True)

# Track all launched processes
processes = []

def run_command(command, log_file, env=None, cores=None):
    cmd = command
    if cores is not None:
        cmd = ["taskset", "-c", cores] + command
    with open(log_file, "w") as out:
        proc = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, env=env)
    return proc

# ---------------------------
# Launch vLLM (GPUs 0,1)
# ---------------------------

print("Starting Qwen-14B-Instruct on vLLM with GPUs 0,1...")

vllm_env = os.environ.copy()
vllm_env["CUDA_VISIBLE_DEVICES"] = "0,1"

processes.append(run_command(
    [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", "Qwen/Qwen2.5-14B-Instruct",
        "--tensor-parallel-size", "2",
        "--dtype", "half"
    ],
    "logs/vllm.log",
    env=vllm_env,
    cores="5-15"
))

# Wait for vLLM API to be ready
print("Waiting for vLLM to become available...")
ready = False
for i in range(30):
    try:
        out = subprocess.check_output(["curl", "-s", "http://localhost:8000/v1/models"])
        if b'"id"' in out:
            ready = True
            break
    except subprocess.CalledProcessError:
        pass
    print("  ...still waiting for vLLM...")
    time.sleep(10)

if ready:
    print("Qwen LLM API is online!")
else:
    print("Failed to detect vLLM API. Continuing anyway...")

# ---------------------------
# Find a free TCP port
# ---------------------------
def get_free_tcp_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]
    
# ---------------------------
# Launch HTTP-based State Server
# ---------------------------
print("Starting HTTP State Server...")

server_port = get_free_tcp_port()
server_addr = f"http://127.0.0.1:{server_port}"

processes.append(run_command(
    ["taskset", "-c", "4", "python", "state_server_http.py", str(server_port)],
    "logs/state_server.log"
))
time.sleep(2)

#---------------------------
# Create experiment config
#---------------------------
experiment_config = {
    "experiment": args.experiment,
    "state_vars": selected_state,
    "state_server_url": server_addr,
    "timestamp": time.strftime("%Y-%m-%d_%H-%M")
}
with open("experiment_config.json", "w") as f:
    json.dump(experiment_config, f, indent=4)

# ---------------------------
# Launch the Agents
# ---------------------------

print("Launching Host Runtime")
processes.append(run_command(["python", "run_host.py", "--config"], "logs/host.log"))
time.sleep(2)

print("Launching Writer Agent")
processes.append(run_command(["python", "run_writer_agent.py", "--config", "experiment_config.json"], "logs/writer.log", cores="0"))
time.sleep(1)

print("Launching Editor Agent")
processes.append(run_command(["python", "run_editor_agent.py", "--config", "experiment_config.json"], "logs/editor.log", cores="1"))
time.sleep(1)

print("Launching Group Chat Manager")
processes.append(run_command(["python", "run_group_chat_manager.py", "--config", "experiment_config.json"], "logs/manager.log", cores="2"))
time.sleep(1)

print("Launching UI Agent")
processes.append(run_command(["python", "run_ui.py"], "logs/ui.log", cores="3"))
time.sleep(1)

print("All agents launched. Waiting for them to finish...")

# Wait for all processes to complete
for proc in processes:
    proc.wait()

print("All agents have exited.")
