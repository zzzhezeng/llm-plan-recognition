#!/bin/bash
# CLARA grid benchmarks (clara.py) on one open model (UVA HPC).
#   sbatch --export=ALL,MODEL=Qwen/Qwen2.5-7B-Instruct,SET=pilot,SAMPLES=1 run_clara_hf.slurm
#   sbatch --export=ALL,MODEL=meta-llama/Meta-Llama-3-8B-Instruct,SET=pilot,SAMPLES=1 run_clara_hf.slurm
# Runs resume, so a job that hits the time limit can simply be resubmitted.
#SBATCH --job-name=clara-hf
#SBATCH --account=takolab
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
# Not V100 (the torch cu128 build has no sm_70 kernels) and not B200 (Qwen2.5 in bfloat16
# writes garbled text there: 28/40 unparseable answers vs 0/40 on A100 and RTX PRO 6000).
#SBATCH --constraint=a100|a40|a6000|rtxpro6000
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
STORE=/standard/takolab/ykm5ee
cd "$STORE/llm-plan-recognition"
module load miniforge
source "$STORE/envs/nextaction/bin/activate"
export HF_HUB_CACHE="$STORE/hf_cache/hub" TRANSFORMERS_VERBOSITY=error HF_HUB_DISABLE_PROGRESS_BARS=1
MODEL=${MODEL:-Qwen/Qwen2.5-7B-Instruct}
SET=${SET:-pilot}
SAMPLES=${SAMPLES:-1}
VARIANT=${VARIANT:-same}
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv

python -u -W ignore clara.py run --model "hf:$MODEL" --set "$SET" --samples "$SAMPLES" \
  --variant "$VARIANT" --workers 1 --dtype bfloat16
python -u -W ignore clara.py score > /dev/null
