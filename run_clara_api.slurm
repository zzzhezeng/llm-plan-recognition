#!/bin/bash
# CLARA grid benchmarks (clara.py) on API models (UVA HPC). No GPU needed. The API
# keys come from the submitting shell's environment, so source ~/.bashrc first.
#   sbatch --export=ALL,MODELS="gpt-6-luna gpt-5.4-mini jev-latest",SET=pilot,SAMPLES=1 run_clara_api.slurm
#SBATCH --job-name=clara-api
#SBATCH --account=takolab
#SBATCH --partition=standard
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=1-00:00:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
STORE=/standard/takolab/ykm5ee
cd "$STORE/llm-plan-recognition"
module load miniforge
source "$STORE/envs/nextaction/bin/activate"
MODELS=${MODELS:-gpt-6-luna}
SET=${SET:-pilot}
SAMPLES=${SAMPLES:-1}
VARIANT=${VARIANT:-same}
WORKERS=${WORKERS:-8}
MAX_USD=${MAX_USD:-50}

for model in $MODELS; do
  python -u -W ignore clara.py run --model "$model" --set "$SET" --samples "$SAMPLES" \
    --variant "$VARIANT" --workers "$WORKERS" --max-usd "$MAX_USD"
done
python -u -W ignore clara.py score > /dev/null
