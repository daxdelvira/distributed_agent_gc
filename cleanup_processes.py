import os
import signal
import subprocess
import time

# Keywords to look for in running agent processes
AGENT_KEYWORDS = [
    "run_host.py",
    "run_writer_agent.py",
    "run_editor_agent.py",
    "run_group_chat_manager.py",
    "run_ui.py",
    "openai.api_server",  # vLLM server
]

# Unix socket paths or temp files (modify as needed for your setup)
SOCKET_PATHS = [
    "/tmp/autogen_host_runtime.sock",
    "/tmp/editor_agent.sock",
    "/tmp/host.sock",
]

def kill_matching_processes():
    print("🛑 Killing agent-related processes...")
    try:
        # Use `ps` to find candidate processes
        ps_output = subprocess.check_output(["ps", "aux"], text=True)

        for line in ps_output.splitlines():
            if any(keyword in line for keyword in AGENT_KEYWORDS):
                pid = int(line.split()[1])
                print(f"  → Killing PID {pid}: {line.strip()}")
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)  # give it a moment
    except Exception as e:
        print(f"Error during process kill: {e}")

def remove_sockets():
    print("🧹 Removing socket/temp files...")
    for path in SOCKET_PATHS:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"  → Removed {path}")
            except Exception as e:
                print(f"  ! Failed to remove {path}: {e}")

def clear_logs():
    # Uncomment if you want to clear logs between runs
    # print("🗑️  Clearing log files...")
    # for filename in os.listdir("logs"):
    #     path = os.path.join("logs", filename)
    #     os.remove(path)
    #     print(f"  → Deleted {path}")
    pass

if __name__ == "__main__":
    kill_matching_processes()
    remove_sockets()
    clear_logs()
    print("✅ Cleanup complete.")
