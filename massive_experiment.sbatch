#!/bin/bash
#SBATCH --account=gts-apadmanabh3
#SBATCH -q embers
#SBATCH --job-name=massive-overheads-data-collection
#SBATCH --mail-user=dax@gatech.edu
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --output=logs/vllm_experiment_%j.log
#SBATCH --error=logs/vllm_experiment_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:RTX_6000:4
#SBATCH --time=12:00:00
#SBATCH --exclusive

# Load environment
conda activate dummy_agent  # 🔁 Replace this with your actual conda environment name

# Configuration
PORT=8000  # 🔁 Replace if vLLM runs on a different port
HOST=localhost
STATE_VARS_LIST=(1 5 10 50 100)
EXPERIMENTS=("llm-latency" "per-agent-memory" "central-log-memory" "state-update-comms" "state-retrieval")

# Function to wait until vLLM is responsive
wait_for_vllm_ready() {
    echo "[$(date)] Waiting for vLLM to respond on port $PORT..."
    for i in {1..60}; do
        if curl -s "http://$HOST:$PORT" > /dev/null; then
            echo "[$(date)] vLLM is ready."
            return 0
        fi
        sleep 30
    done
    echo "[$(date)] Timeout: vLLM did not respond after 30 minutes."
    return 1
}

run_experiment() {
    STATE_VAR=$1
    EXPERIMENT_NAME=$2
    ITER=$3

    echo "[$(date)] Starting vLLM (State=$STATE_VAR, Experiment=$EXPERIMENT_NAME, Iteration=$ITER)..."
    python vllm_launcher.py &
    VLLM_PID=$!

    wait_for_vllm_ready || {
        echo "[$(date)] Failed to detect vLLM readiness. Killing..."
        kill -9 $VLLM_PID
        return 1
    }

    echo "[$(date)] Starting agents (State=$STATE_VAR, Experiment=$EXPERIMENT_NAME, Iteration=$ITER)..."
    python no_vllm_launcher.py --state-vars=$STATE_VAR --experiment=$EXPERIMENT_NAME &
    AGENT_PID=$!

    echo "[$(date)] Running for 10 minutes..."
    sleep 600

    echo "[$(date)] Stopping agents..."
    kill -SIGINT $AGENT_PID
    wait $AGENT_PID

    echo "[$(date)] Stopping vLLM..."
    kill -SIGINT $VLLM_PID
    wait $VLLM_PID

    echo "[$(date)] Finished: State=$STATE_VAR, Experiment=$EXPERIMENT_NAME, Iteration=$ITER"
    echo ""
}

# Nested loop over all combinations
for STATE_VAR in "${STATE_VARS_LIST[@]}"; do
    for EXPERIMENT_NAME in "${EXPERIMENTS[@]}"; do
        for ITER in {1..10}; do
            run_experiment $STATE_VAR $EXPERIMENT_NAME $ITER
            echo "[$(date)] Cooling down before next iteration..."
            sleep 15
        done
    done
done

echo "[$(date)] ✅ All experiments completed."
