#!/bin/bash
# Goal recognition (bench.py) on one open model (UVA HPC).
#   sbatch --export=ALL,MODEL=Qwen/Qwen2.5-7B-Instruct run_bench_hf.slurm
#   sbatch --export=ALL,MODEL=meta-llama/Meta-Llama-3-8B-Instruct run_bench_hf.slurm
#SBATCH --job-name=bench
#SBATCH --account=takolab
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
# V100 nodes: the torch cu128 build has no sm_70 kernels.
#SBATCH --exclude=udc-an33-37,udc-an33-38
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
STORE=/standard/takolab/ykm5ee
cd "$STORE/llm-plan-recognition"
module load miniforge
source "$STORE/envs/nextaction/bin/activate"
export HF_HUB_CACHE="$STORE/hf_cache/hub" TRANSFORMERS_VERBOSITY=error HF_HUB_DISABLE_PROGRESS_BARS=1
MODEL=${MODEL:-Qwen/Qwen2.5-7B-Instruct}
SAMPLES=${SAMPLES:-3}
EXTRA=${EXTRA:-}
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv

python -u -W ignore bench.py run --model "hf:$MODEL" --samples "$SAMPLES" --workers 1 --dtype bfloat16 $EXTRA
python -u -W ignore bench.py score
