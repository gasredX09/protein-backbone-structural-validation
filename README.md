# Structural Validation of Generated Protein Backbones

## Overview

This repository provides a reproducible pipeline for validating generated protein backbones using CCTBX-based structural analysis. The validation workflow analyzes 100 protein structures (50 from La-Proteina and 50 from ReQFlow) and produces:

- `validate.py` - validation script (CCTBX Ramachandran + optional MolProbity clashscore)
- `results.csv` - per-structure quality metrics (Ramachandran + clashscore)
- `analysis.pdf` - one-page summary with figures and statistics table
- `generated_pdbs/` - precomputed input structures (100 backbones at length ~200)
- `bonus/` - optional bonus scripts and outputs (enhanced validator, summaries, and plots)

This repository does **not** vendor the full La-Proteina or ReQFlow upstream codebases. Instead, it includes generated structures and validation artifacts. Use the official upstream repositories for model code and checkpoints:

- La-Proteina: https://github.com/NVIDIA-Digital-Bio/la-proteina
- ReQFlow: https://github.com/AngxiaoYue/ReQFlow

## Repository Structure

- `validate.py` - validation script (CCTBX Ramachandran + optional MolProbity clashscore)
- `results.csv` - validation output for all 100 structures
- `analysis.pdf` - one-page summary with Ramachandran figures and statistics
- `generated_pdbs/` - 100 final structures (50 La-Proteina + 50 ReQFlow)
- `environment.yml` - conda environment for Linux/HPC
- `environment-macos.yml` - conda environment for macOS
- `bonus/` - all bonus work (enhanced validation, summaries, plots, logs)

## Environment Setup

### Linux/HPC (Recommended for full reproducibility)

Create the validation environment with:

```bash
conda env create -f environment.yml
conda activate protein-validation
```

This environment includes all packages for CCTBX-based analysis and MolProbity preprocessing (`reduce` and `probe`).

### macOS / arm64 (with clashscore support)

Ramachandran metrics work out of the box. Clashscore requires manual installation of `reduce` and `probe`.

#### Build reduce and probe from source

Build manually:

**Step 1: Build probe**

```bash
git clone https://github.com/rlabduke/probe.git /tmp/probe_build
cd /tmp/probe_build
make clean && make
```

**Step 2: Build reduce**

```bash
git clone https://github.com/rlabduke/reduce.git /tmp/reduce_build
cd /tmp/reduce_build
make clean && make
```

**Step 3: Install into conda environment**

```bash
conda activate protein-validation
cp /tmp/probe_build/probe $CONDA_PREFIX/bin/
cp /tmp/reduce_build/reduce_src/reduce $CONDA_PREFIX/bin/
cp /tmp/reduce_build/reduce_wwPDB_het_dict.txt $CONDA_PREFIX/bin/
```

**Step 4: Create symlink for molprobity.reduce**

```bash
ln -s $(which reduce) $(dirname $(which reduce))/molprobity.reduce
```

**Step 5: Configure het dictionary**

```bash
export REDUCE_HET_DICT="$CONDA_PREFIX/bin/reduce_wwPDB_het_dict.txt"
```

Add to `~/.zshrc` or `~/.bashrc` for persistence.

**Step 6: Verify installation**

```bash
which reduce && reduce -version
which probe && probe -version
```

**Step 7: Run validation with clashscore**

```bash
python validate.py generated_pdbs --out results.csv -v
```

## Input Structures (Precomputed)

The generated structures are already included in the repository under `generated_pdbs/`:

- `generated_pdbs/laproteina/` - 50 La-Proteina PDBs
- `generated_pdbs/reqflow/` - 50 ReQFlow PDBs

Each set contains approximately 200-residue backbones with filenames:

- `laproteina_001.pdb` through `laproteina_050.pdb`
- `reqflow_001.pdb` through `reqflow_050.pdb`

(Note: Structures are parsed as 198 residues by CCTBX. This reflects terminal residue handling in the PDB representation rather than a true change in backbone length.)

## Structure Generation (Commands Used)

The following commands were used to generate the 100 input structures:

### La-Proteina (50 structures)

Upstream repository: https://github.com/NVIDIA-Digital-Bio/la-proteina (commit used: `cde5de3ead6e4d76f367da6dc5174be9913ef6ca`)

```bash
cd la-proteina
python proteinfoundation/generate.py --config_name inference_ucond_notri
```

Configuration: Unconditional sampling, length 200, 50 samples.  
Checkpoints: Placed in `./checkpoints_laproteina/` (not included in repo; see `./checkpoints_laproteina/instructions.txt`).

### ReQFlow (50 structures)

Upstream repository: https://github.com/AngxiaoYue/ReQFlow (commit used: `2c93df98b655bc39848b50ad8e5b5138feee6878`)

```bash
cd ReQFlow
python -W ignore experiments/inference_se3_flows.py -cn inference_unconditional
```

Configuration: Edit `configs/inference_unconditional.yaml` to set sample lengths to 200 and `samples_per_length: 50`.  
Checkpoints: Expected under `ReQFlow/ckpts/` (not included in repo).

## Bonus Work

All bonus deliverables are collected in `bonus/`, including:

- `bonus/validate_bonus.py` - enhanced validator with robust error handling and optional clashscore skipping
- `bonus/generate_plots.py` - automatic generation of analysis figures
- `bonus/summary_by_method.csv` - per-method aggregate statistics
- `bonus/plots/` - generated bonus figures
- `bonus/logs/` - validation error logs

## Running Validation

Run validation from the repository root with the exact command below:

```bash
python validate.py generated_pdbs --out results.csv
```

To see progress messages, add `-v`:

```bash
python validate.py generated_pdbs --out results.csv -v
```

Validation performs the following steps for each structure:

1. **Parse structure:** Read PDB file with CCTBX
2. **Ramachandran analysis:** Compute favored/allowed/outlier counts and fractions using CCTBX phi/psi geometry
3. **Optional clashscore (if reduce + probe available):**
   - Clashscore requires explicit hydrogen placement; `reduce` adds hydrogens and optimizes orientations (for example Asn/Gln/His flips), while `probe` computes steric overlaps.
   - Strip hydrogens: `reduce -quiet -trim -allalt input.pdb > trimmed.pdb`
   - Rebuild hydrogens: `reduce -quiet -build trimmed.pdb > reduced.pdb`
   - Compute clashscore on reduced structure
4. **Output:** Write one row per structure to `results.csv`

The validation script logs errors per structure and continues execution, so a single malformed PDB does not interrupt the full validation run.

## Output Format

`results.csv` contains the following columns:

- `filename` - input PDB filename
- `method` - `laproteina` or `reqflow`
- `n_residues` - residues analyzed by CCTBX
- `rama_favored` - favored Ramachandran residue count
- `rama_allowed` - allowed Ramachandran residue count
- `rama_outlier` - outlier Ramachandran residue count
- `rama_favored_frac` - favored fraction
- `rama_allowed_frac` - allowed fraction
- `rama_outlier_frac` - outlier fraction
- `clashscore` - clashscore value, or `NA` if unavailable
- `n_clashes` - clash count used for clashscore, or `NA`
- `clashscore_error` - reason clashscore was unavailable, if any
- `error` - validation error, if any

If clashscore preprocessing succeeds, reduced structures are written to:

- `reduced_pdbs/laproteina/`
- `reduced_pdbs/reqflow/`

## Results Summary

All 100 structures validated successfully on Linux/HPC. Ramachandran analysis and clashscore were computed for the main run (see `results.csv`).

Key summary:

- 100 total structures processed
- 50 La-Proteina and 50 ReQFlow structures
- All structures analyzed as 198 residues (parsed length from PDB format)
- 0 validation failures
- Ramachandran analysis: 100/100 successful
- Clashscore: computed for the main run (mean values shown below)

Method-level Ramachandran summary (main run):

| Method | Mean Rama Favored | Median Rama Favored | Mean Rama Outlier | Median Rama Outlier | Mean Clashscore | N Successful |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| La-Proteina | 0.9944 | 0.9949 | 0.0002 | 0.0000 | 0.00 | 50 |
| ReQFlow | 0.9781 | 0.9798 | 0.0046 | 0.0051 | 0.00 | 50 |

La-Proteina shows slightly higher-quality Ramachandran metrics in this sample compared to ReQFlow, with a higher mean favored fraction and lower mean outlier fraction. Both methods produce largely physically plausible backbones (>97% favored on average), though ReQFlow exhibits greater variability.

For bonus analyses (alternate runs, skip-clashscore, or additional summaries), see `bonus/summary_by_method.csv` and `bonus/README.md`.

## Known Issues & Quirks

- **Clashscore availability:** Requires both `reduce` and `probe` binaries. If either is missing, clashscore columns show `NA`.
- **reduce het dictionary:** On some systems, `reduce` requires the `REDUCE_HET_DICT` environment variable. This is typically configured automatically in conda-based Linux environments, but may require manual configuration on macOS.
- **molprobity.reduce symlink:** The clashscore module internally expects `molprobity.reduce`; create a symlink if building from source.
- **reduce exit codes:** May exit with code 255 even when output is valid; script ignores exit code if output file exists.
- **Hydrogen preprocessing:** Reduced PDBs (with added hydrogens) are stored only when clashscore preprocessing succeeds.
- **Idempotency:** The repository includes generated outputs; rerunning the pipeline will overwrite `results.csv`.

## Quick Reproducibility

### Linux/HPC (full clashscore reproducibility)

```bash
conda env create -f environment.yml
conda activate protein-validation
python validate.py generated_pdbs --out results.csv -v
```

### macOS / arm64 (with manual reduce/probe build)

```bash
conda env create -f environment-macos.yml
conda activate protein-validation

# Build reduce and probe (see "macOS / arm64" section for detailed instructions)
git clone https://github.com/rlabduke/probe.git /tmp/probe_build && cd /tmp/probe_build && make
git clone https://github.com/rlabduke/reduce.git /tmp/reduce_build && cd /tmp/reduce_build && make

# Install binaries
cp /tmp/probe_build/probe $CONDA_PREFIX/bin/
cp /tmp/reduce_build/reduce_src/reduce $CONDA_PREFIX/bin/
cp /tmp/reduce_build/reduce_wwPDB_het_dict.txt $CONDA_PREFIX/bin/
ln -s $(which reduce) $(dirname $(which reduce))/molprobity.reduce

# Set environment and validate
export REDUCE_HET_DICT="$CONDA_PREFIX/bin/reduce_wwPDB_het_dict.txt"
python validate.py generated_pdbs --out results.csv -v
```

## Dependency Verification

Before running validation, verify required packages:

```bash
python - <<'PY'
import iotbx.pdb
from mmtbx.validation import ramalyze
print("✓ CCTBX Ramachandran analysis available")
PY
```

For clashscore support, verify binaries:

```bash
which reduce && reduce -version
which probe && probe -version
```

## Reproducibility Notes

Both platforms reproduce **Ramachandran metrics identically**. Clashscore is available when `reduce` and `probe` are correctly installed:
- **Linux/HPC:** via conda automatically
- **macOS:** via manual source build (see instructions above)

The input directory is expected to contain 100 PDB files, 50 per method.

The workflow is reproducible from:
- Checked-in PDB structures in `generated_pdbs/`
- Validation script `validate.py` with CCTBX API calls
- Platform-appropriate environment specification

