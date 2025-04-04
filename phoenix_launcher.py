import subprocess
import time
import os

# Create log directory if not exists
os.makedirs("logs", exist_ok=True)

def run_command(command, log_file, env=None, cores=None):
    cmd = command
    if cores is not None:
        cmd = ["taskset", "-c", cores] + command
    with open(log_file, "w") as out:
        subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, env=env)

# ---------------------------
# Launch vLLM (GPUs 0,1)
# ---------------------------

print("Starting Qwen-14B-Instruct on vLLM with GPUs 0,1...")

vllm_env = os.environ.copy()
vllm_env["CUDA_VISIBLE_DEVICES"] = "0,1"

run_command(
    [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", "Qwen/Qwen2.5-14B-Instruct",
        "--tensor-parallel-size", "2",
        "--dtype", "half"
    ],
    "logs/vllm.log",
    env=vllm_env,
    cores="0-11"
)

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
# Launch the Agents
# ---------------------------

print("Launching Host Runtime")
run_command(["python", "run_host.py"], "logs/host.log")
time.sleep(2)

print("Launching Writer Agent")
run_command(["python", "run_writer_agent.py"], "logs/writer.log", cores="0")
time.sleep(1)

print("Launching Editor Agent")
run_command(["python", "run_editor_agent.py"], "logs/editor.log", cores="1")
time.sleep(1)

print("Launching Group Chat Manager")
run_command(["python", "run_group_chat_manager.py"], "logs/manager.log", cores="2")
time.sleep(1)

print("Launching UI Agent")
run_command(["python", "run_ui.py"], "logs/ui.log", cores="3")
time.sleep(1)

print("All agents launched.")
