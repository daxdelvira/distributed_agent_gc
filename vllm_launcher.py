# vllm_launcher.py
import subprocess
import os

# Adjust these as needed
CUDA_DEVICES = "0,1,2,3"
CORES = "5-15"
MODEL_NAME = "Qwen/Qwen2.5-14B-Instruct"
LOG_FILE = "logs/vllm_new_setup.log"

os.makedirs("logs", exist_ok=True)

command = [
    "taskset", "-c", CORES,
    "python", "-m", "vllm.entrypoints.openai.api_server",
    "--model", MODEL_NAME,
    "--tensor-parallel-size", "4",
    "--dtype", "half"
]

env = os.environ.copy()
env["CUDA_VISIBLE_DEVICES"] = CUDA_DEVICES

print(f"Launching vLLM on GPUs {CUDA_DEVICES} with CPU cores {CORES}")
with open(LOG_FILE, "w") as out:
    subprocess.Popen(command, stdout=out, stderr=subprocess.STDOUT, env=env)

print(f"vLLM started. Logs at: {LOG_FILE}")
