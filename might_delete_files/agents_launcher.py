import multiprocessing
import os
import psutil
import subprocess
import time

AGENT_SCRIPTS = [
    ("run_host.py", 0),
    ("run_ui.py", 1),
    ("run_writer_agent.py", 2),
    ("run_editor_agent.py", 3),
    ("run_group_chat_manager.py", 4),
]

def launch_agent(script_name: str, core_id: int):
    process = psutil.Process()
    process.cpu_affinity([core_id])  # Pin this process to one core
    print(f"Launching {script_name} on CPU core {core_id}...")
    subprocess.run(["python3", script_name])

if __name__ == "__main__":
    processes = []

    for script, core in AGENT_SCRIPTS:
        p = multiprocessing.Process(target=launch_agent, args=(script, core))
        p.start()
        time.sleep(2)  # Stagger start time slightly to avoid race conditions
        processes.append(p)

    for p in processes:
        p.join()
    print("All agents launched successfully.")