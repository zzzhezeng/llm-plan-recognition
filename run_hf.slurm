#!/bin/bash
# All three next-action estimators on one open model (UVA HPC).
#   sbatch --export=ALL,MODEL=meta-llama/Meta-Llama-3-8B-Instruct run_hf.slurm
#SBATCH --job-name=nextaction
#SBATCH --account=takolab
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
# V100 nodes: the torch cu128 build has no sm_70 kernels.
#SBATCH --exclude=udc-an33-37,udc-an33-38
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
STORE=/standard/takolab/ykm5ee
cd "$STORE/llm-plan-recognition"
module load miniforge
source "$STORE/envs/nextaction/bin/activate"
# Weights go to research storage; the login token stays in ~/.cache/huggingface/token.
export HF_HUB_CACHE="$STORE/hf_cache/hub" TRANSFORMERS_VERBOSITY=error HF_HUB_DISABLE_PROGRESS_BARS=1
MODEL=${MODEL:-meta-llama/Meta-Llama-3-8B-Instruct}
EXTRA=${EXTRA:-}
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv

# ESTIMATORS="nexttoken-preamble" runs just that one.
ESTIMATORS=${ESTIMATORS:-nexttoken nexttoken-preamble verbalized sampling}
COMMON="--model hf:$MODEL --workers 1 --dtype bfloat16 $EXTRA"
for E in $ESTIMATORS; do
  case $E in
    verbalized) python -u -W ignore nextaction.py run --estimator $E --samples 3 --max-tokens 768 $COMMON ;;
    sampling)   python -u -W ignore nextaction.py run --estimator $E --samples 10 --max-tokens 768 $COMMON ;;
    *)          python -u -W ignore nextaction.py run --estimator $E $COMMON ;;
  esac
done
python -u -W ignore nextaction.py score
