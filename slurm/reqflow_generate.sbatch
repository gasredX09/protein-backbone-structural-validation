#!/bin/bash
#SBATCH --job-name=reqflow200
#SBATCH --account=med260003p
#SBATCH --partition=GPU-shared
#SBATCH --qos=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-gpu=8
#SBATCH --time=12:00:00
#SBATCH --output=/ocean/projects/med260003p/aguda1/protein-backbone-structural-validation/logs/reqflow_%j.out
#SBATCH --error=/ocean/projects/med260003p/aguda1/protein-backbone-structural-validation/logs/reqflow_%j.err

set -eo pipefail

cd /ocean/projects/med260003p/aguda1/ReQFlow
export LD_LIBRARY_PATH=/ocean/projects/med260003p/aguda1/conda_envs/reqflow-env/lib:${LD_LIBRARY_PATH:-}
export PYTHONNOUSERSITE=1
export DATA_PATH=/ocean/projects/med260003p/aguda1/ReQFlow
# Use /ocean for torch cache to avoid home directory quota issues
export TORCH_HOME=/ocean/projects/med260003p/aguda1/torch_cache
mkdir -p $TORCH_HOME

# Run ReQFlow unconditional sampler (configured via configs/inference_unconditional.yaml)
# Run as a module so package imports (e.g., `experiments`) resolve correctly.
/ocean/projects/med260003p/aguda1/conda_envs/reqflow-env/bin/python -m experiments.inference_se3_flows
