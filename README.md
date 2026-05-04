# Structural Validation of Generated Protein Backbones

This repository contains the final validation workflow for 100 generated protein backbones: 50 from La-Proteina and 50 from ReQFlow. The main deliverables are `validate.py`, `results.csv`, `analysis.pdf`, and the input structures under `generated_pdbs/`.

Bonus scripts and plots live in `bonus/`. The source repositories used to generate the structures are included in `la-proteina/` and `ReQFlow/`.

## Repository Contents

- `validate.py` - core validation script
- `results.csv` - validation output for the 100 generated structures
- `analysis.pdf` - one-page analysis summary
- `generated_pdbs/` - final PDB inputs used for validation
- `reduced_pdbs/` - hydrogen-added structures created when clashscore preprocessing succeeds
- `environment.yml` - conda environment for Linux/HPC
- `environment-macos.yml` - conda environment for macOS
- `bonus/` - optional enhanced validator, plots, and bonus documentation
- `la-proteina/` and `ReQFlow/` - source repositories used to generate the structures

## Setup

Create the validation environment with the file that matches your platform:

```bash
conda env create -f environment.yml
conda activate protein-validation
```

or on macOS:

```bash
conda env create -f environment-macos.yml
conda activate protein-validation
```

If you want clashscore output, `reduce` and `probe` must be available in the environment. If they are missing, Ramachandran validation still runs and clashscore is recorded as `NA`.

## Running Validation

From the repository root:

```bash
python validate.py generated_pdbs --out results.csv
```

Add `-v` for progress messages:

```bash
python validate.py generated_pdbs --out results.csv -v
```

The script parses each PDB file with CCTBX, computes Ramachandran favored/allowed/outlier counts and fractions, and attempts clashscore preprocessing when the required binaries are present. Validation errors are logged per structure, so one bad file does not stop the batch.

## Output Columns

`results.csv` includes these fields:

- `filename`
- `method`
- `n_residues`
- `rama_favored`
- `rama_allowed`
- `rama_outlier`
- `rama_favored_frac`
- `rama_allowed_frac`
- `rama_outlier_frac`
- `clashscore`
- `n_clashes`
- `clashscore_error`
- `error`

## Results Summary

All 100 structures validated successfully.

| Method | Mean Favored | Median Favored | Mean Outlier | Median Outlier | Mean Clashscore | N |
| --- | --- | --- | --- | --- | --- | --- |
| La-Proteina | 0.9944 | 0.9949 | 0.0002 | 0.0000 | 0.00 | 50 |
| ReQFlow | 0.9781 | 0.9798 | 0.0046 | 0.0051 | 0.00 | 50 |

Both methods produce clash-free structures in this dataset. La-Proteina is slightly more Ramachandran-favored and more consistent, while ReQFlow has a higher outlier rate but still remains structurally plausible.

## Notes

- The generated structures are stored in `generated_pdbs/laproteina/` and `generated_pdbs/reqflow/`.
- If clashscore preprocessing succeeds, hydrogen-added structures are written under `reduced_pdbs/`.
- For optional extensions and plots, see `bonus/README.md`.

