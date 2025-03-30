#!/bin/bash
#SBATCH --job-name=llm_agents
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --gres=gpu:8
#SBATCH --time=02:20:00
#SBATCH --output=agent_%j.out
