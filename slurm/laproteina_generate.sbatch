#!/bin/bash
#SBATCH --job-name=laprot200
#SBATCH --account=med260003p
#SBATCH --partition=GPU-shared
#SBATCH --qos=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-gpu=5
#SBATCH --time=12:00:00
#SBATCH --output=/ocean/projects/med260003p/aguda1/protein-backbone-structural-validation/logs/laproteina_%j.out
#SBATCH --error=/ocean/projects/med260003p/aguda1/protein-backbone-structural-validation/logs/laproteina_%j.err

set -eo pipefail

# Source bashrc to load cache redirects
source ~/.bashrc

cd /ocean/projects/med260003p/aguda1/la-proteina
export PYTHONNOUSERSITE=1
export DATA_PATH=/ocean/projects/med260003p/aguda1/la-proteina

# Run the unconditional sampler (configured for length 200, 50 samples)
/ocean/projects/med260003p/aguda1/conda_envs/laproteina_env/bin/python proteinfoundation/generate.py --config_name inference_ucond_notri
