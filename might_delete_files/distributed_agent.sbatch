#!/bin/bash
#SBATCH --job-name=distributed_agents
#SBATCH --account=gts-apadmanabh3
#SBATCH -q embers
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:L40S:4
#SBATCH --time=02:20:00
#SBATCH --output=groupchat_%j.out

export HOST_ADDRESS="localhost:50051"

#Launch vLLM with 2 GPUs, isolated from the agent GPUs
echo "Starting Qwen-14B-Instruct on vLLM with 2 GPUs"
nohup taskset -c 0-11 \
CUDA_VISIBLE_DEVICES=0,1 \
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-14B-Instruct \
    --tensor-parallel-size 2 \
    --dtype=half \

until curl -s http://localhost:8000/v1/models | grep -q '"id"'; do
  sleep 20
  echo "  ...still waiting for vLLM..."
done

echo "Qwen LLM API is online!"

# Launch the distributed agents

# Launch the gRPC host
echo "Launching Host Runtime"
nohup python run_host.py > logs/host.log 2>&1 &
sleep 2

# Launch writer agent (uses CPU core 0)
echo "Launching Writer Agent"
nohup taskset -c 0 python run_writer_agent.py > logs/writer.log 2>&1 &
sleep 1

# Launch editor agent (uses CPU core 1)
echo "Launching Editor Agent"
nohup taskset -c 1 python run_editor_agent.py > logs/editor.log 2>&1 &
sleep 1

# Launch group chat manager (uses CPU core 2)
echo "Launching Group Chat Manager"
nohup taskset -c 2 python run_group_chat_manager.py > logs/manager.log 2>&1 &
sleep 1

# Launch UI agent (uses CPU core 3)
echo "Launching UI Agent"
nohup taskset -c 3 python run_ui.py > logs/ui.log 2>&1 &
sleep 1
