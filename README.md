# Structural Validation of Generated Protein Backbones

## Overview

This repository contains a complete workflow for generating and validating 100 protein backbone structures:

- 50 structures from La-Proteina
- 50 structures from ReQFlow

The final deliverables are:

- `validate.py` for validation
- `results.csv` with per-structure quality metrics
- `analysis.pdf` with a compact summary of the results
- `generated_pdbs/` containing the finalized PDB files

## Repository Structure

- `validate.py` - thin wrapper that forwards to `submission/validate.py`
- `submission/` - validation script, CSV output, analysis PDF, and submission notes
- `generated_pdbs/` - final generated structures grouped by method
- `reduced_pdbs/` - hydrogen-added structures saved during clashscore preprocessing
- `la-proteina/` - La-Proteina source tree and checkpoints
- `ReQFlow/` - ReQFlow source tree and checkpoint files
- `environment.yml` - conda environment specification for Linux/HPC (includes reduce and probe)
- `environment-macos.yml` - conda environment specification for macOS (clashscore-free)
- `setup_notes.md` - setup and generation notes

## Environment Setup

### Linux/HPC (Recommended for full reproducibility)

Create the validation environment with:

```bash
conda env create -f environment.yml
conda activate protein-validation
```

This environment includes all packages for CCTBX-based analysis and MolProbity preprocessing (`reduce` and `probe`).

### macOS / Other platforms

On macOS and other non-Linux platforms, `probe` and `reduce` binaries are not available. Use the macOS-compatible environment instead:

```bash
conda env create -f environment-macos.yml
conda activate protein-validation
```

**Note:** On non-Linux platforms, clashscore computation will not be available, and the clashscore columns in `results.csv` will show `NA`. Ramachandran metrics will still be computed successfully.

## Generating Structures

The generated structures are already included in the repository under `generated_pdbs/`:

- `generated_pdbs/laproteina/` - 50 La-Proteina PDBs
- `generated_pdbs/reqflow/` - 50 ReQFlow PDBs

Each set contains length-200 backbones with filenames:

- `laproteina_001.pdb` through `laproteina_050.pdb`
- `reqflow_001.pdb` through `reqflow_050.pdb`

## Running Validation

Run validation from the repository root with the exact command below:

```bash
python validate.py generated_pdbs --out results.csv
```

To see progress messages, add `-v`:

```bash
python validate.py generated_pdbs --out results.csv -v
```

Validation does the following for each structure:

1. Reads the PDB file with CCTBX
2. Computes Ramachandran counts and fractions
3. Attempts optional clashscore computation after `reduce` and `probe` preprocessing
4. Writes one row per structure to `results.csv`

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

All 100 structures validated successfully.

Key summary:

- 100 total structures processed
- 50 La-Proteina and 50 ReQFlow structures
- All structures were 198 residues in the validation output
- 0 validation failures
- Clashscore computed successfully for all 100 structures
- 0 clashscore failures

Method-level Ramachandran summary:

| Method | Mean Rama Favored | Median Rama Favored | Mean Rama Outlier | Median Rama Outlier | Mean Clashscore | N Successful |
| --- | --- | --- | --- | --- | --- | --- |
| La-Proteina | 0.9944 | 0.9950 | 0.0002 | 0.0000 | 0.00 | 50 |
| ReQFlow | 0.9781 | 0.9899 | 0.0046 | 0.0000 | 0.00 | 50 |

La-Proteina performed better in this sample, with a higher favored fraction and a lower outlier fraction than ReQFlow.

## Known Issues

- **Platform limitation:** `reduce` and `probe` are only available on Linux. On macOS and other platforms, use `environment-macos.yml` for clashscore-free validation.
- Clashscore requires `reduce` and `probe`. If either binary is missing, the clashscore columns will remain `NA`.
- Reduced PDBs are stored only when clashscore preprocessing succeeds.
- The repository includes generated outputs and validation artifacts; rerunning the pipeline will overwrite `results.csv`.

## Reproducibility Notes

### Full reproducibility (Linux/HPC)

For complete reproducibility including clashscore metrics, use a Linux environment:

```bash
conda env create -f environment.yml
conda activate protein-validation
python validate.py generated_pdbs --out results.csv
```

### Partial reproducibility (macOS / other platforms)

Ramachandran metrics can be computed on any platform. Clashscore will not be available:

```bash
conda env create -f environment-macos.yml
conda activate protein-validation
python validate.py generated_pdbs --out results.csv
```

The workflow is reproducible for Ramachandran analysis from the checked-in PDBs, validation script, and appropriate environment specification. Full reproducibility including clashscore requires a Linux environment with `reduce` and `probe` installed.

