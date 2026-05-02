# Setup Notes for La-Proteina and ReQFlow

Date: 2026-04-30
Environment: Bridges-2 login node, Linux
Conda envs used: `ml`, `laproteina_env`, `reqflow-env`

## La-Proteina
Repository path: la-proteina/
Commit hash (HEAD): cde5de3ead6e4d76f367da6dc5174be9913ef6ca

Install instructions followed (from `la-proteina/README.md`):
- Create env (recommended using mamba): `mamba env create -f environment.yaml`
- Activate: `mamba activate laproteina_env`
- Install specific PyTorch and dependencies:
  - `pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118`
  - `pip install torch_geometric torch_scatter torch_sparse torch_cluster torch_spline_conv pyg-lib -f https://data.pyg.org/whl/torch-2.1.0+cu118.html`
  - Remove incompatible optional binaries if needed on Bridges-2: `pyg-lib`, `pyarrow`

Sampling command (unconditional):
- `python proteinfoundation/generate.py --config_name inference_ucond_notri`
Notes:
- Checkpoints must be placed in `./checkpoints_laproteina/` (none present in repo, only `instructions.txt`).
- Current published outputs were generated with length 200 and 50 samples.
- Published canonical outputs live in `protein-backbone-structural-validation/generated_pdbs/laproteina/` as `laproteina_001.pdb` to `laproteina_050.pdb`.

## ReQFlow
Repository path: ReQFlow/
Commit hash (HEAD): 2c93df98b655bc39848b50ad8e5b5138feee6878

Install instructions followed (from `ReQFlow/README.md`):
- `conda env create -f reqflow-env.yml`
- `conda activate reqflow-env`
- `pip install torch-scatter -f https://data.pyg.org/whl/torch-2.0.0+cu117.html`
- `pip install --upgrade deepspeed`
- `pip install -e .` (from repo root)

Sampling command (unconditional):
- `python -W ignore experiments/inference_se3_flows.py -cn inference_unconditional`
Notes:
- Edit `configs/inference_unconditional.yaml` to set sample lengths and `samples_per_length: 50`.
- Model checkpoints expected under `ReQFlow/ckpts/` (not present).

## Actions taken / commands run locally
- Verified CCTBX and binaries in `ml` / project envs:
  - `conda activate ml`
  - `conda activate laproteina_env`
  - `conda activate reqflow-env`
  - `python -c "import iotbx.pdb; from mmtbx.validation import ramalyze; from mmtbx.validation.clashscore import clashscore; import pandas,numpy,matplotlib; print('All imports OK')"` -> All imports OK
  - `which reduce`
  - `which probe`
  - `reduce -version` -> `reduce.3.16.111118`
  - `probe -version` -> `probe.2.13.110909`

- Validation environment setup and verification:
  - `conda create -n protein-validation python=3.10 -y`
  - `conda install -n protein-validation -c conda-forge cctbx-base pandas numpy matplotlib tqdm -y`
  - `conda install -n protein-validation -c speleo3 reduce probe -y`
  - `conda activate protein-validation`
  - `python -c "import iotbx.pdb; from mmtbx.validation import ramalyze; from mmtbx.validation.clashscore import clashscore; import pandas, matplotlib, numpy; print('All imports OK')"`
  - `which reduce`, `reduce -version`, `which probe`, `probe -version`
  - Validation run: `python validate.py generated_pdbs --out submission/results.csv -v`
  - Output confirmed at `submission/results.csv` with 100/100 successful validations.
  - Optional clashscore path succeeded for all 100 structures using `reduce -quiet -trim -allalt` followed by `reduce -quiet -build` and `probe -SUMMARY`.
  - `molprobity.reduce` symlink created in `/ocean/projects/med260003p/aguda1/conda_envs/protein-validation/bin/`.

- Verified La-Proteina repo-root import after environment repair:
  - `cd /ocean/projects/med260003p/aguda1/la-proteina && /ocean/projects/med260003p/aguda1/conda_envs/laproteina_env/bin/python -c "import proteinfoundation.generate; print('generate import ok')"`

## Issues / Notes
- The La-Proteina publish step completed successfully, but the underlying generation save routine can fail on reruns if the output directory already exists.
- On Bridges-2, some prebuilt PyG / optional binaries are not compatible with the system glibc; use the cleaned `laproteina_env` setup rather than the earlier `torch 2.7` stack.
- ReQFlow still needs its Phase 4.2 generation run and publication of canonical outputs in `generated_pdbs/reqflow/`.

## Next steps proposed
1. Write `submission/analysis.pdf` from `submission/results.csv`.
2. Package the submission directory for final handoff.

