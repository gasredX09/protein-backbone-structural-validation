# Bonus Features

This directory contains optional enhancements to the core validation pipeline. The bonus work focuses on robustness, error handling, and advanced analysis features.

## Included Bonus Features

### 1. Enhanced Validator with Graceful Clashscore Fallback

**File:** `validate_bonus.py`

A production-ready validator that extends the core `validate.py` with:

- **Ramachandran-only default**: Always computes CCTBX-based Ramachandran metrics
- **Automatic clashscore attempt**: Tries reduce + probe when available, gracefully falls back to NA when unavailable
- **Structured error logging**: Logs validation failures to `logs/validation_errors.txt` with timestamps and error context
- **Flexible CLI options**:
  - `--skip-clashscore`: Disable clashscore computation entirely
  - `--flat-search`: Search only top-level directory (recursive is default)
  - `--reduced-dir`: Customize output directory for hydrogen-added structures
  - `--log-file`: Customize error log location

**Usage:**

```bash
# Full validation with clashscore (if available)
python bonus/validate_bonus.py generated_pdbs --out bonus/results.csv

# Ramachandran-only (no clashscore preprocessing)
python bonus/validate_bonus.py generated_pdbs --out bonus/results.csv --skip-clashscore

# Search from current directory with verbose output (recursive by default)
python bonus/validate_bonus.py . --out bonus/results.csv -v
```

### 2. Automatic Per-Method Summary Statistics

**Integrated in:** `validate_bonus.py`

Automatically generates method-level aggregate statistics:

- **Output**: `summary_by_method.csv` (default: `bonus/summary_by_method.csv`)
- **Metrics**:
  - `n_total`: Total structures per method
  - `n_successful`: Validation successes (no errors)
  - `mean_rama_favored`: Mean favored fraction
  - `median_rama_favored`: Median favored fraction
  - `mean_rama_outlier`: Mean outlier fraction
  - `median_rama_outlier`: Median outlier fraction
  - `mean_clashscore`: Mean clashscore (NA if unavailable)

**CLI option:**

```bash
python bonus/validate_bonus.py generated_pdbs --out results.csv --summary-out my_summary.csv
```

### 3. Automatic Plot Generation

**File:** `generate_plots.py`

Generates publication-quality visualizations from validation results:

- **Figure 1: Ramachandran by Method**
  - Side-by-side boxplots of favored and outlier fractions
  - Color-coded by method for easy comparison
  - File: `ramachandran_by_method.png`

- **Figure 2: Distributions**
  - 2×2 grid of histograms (favored/outlier for each method)
  - Shows frequency distribution of Ramachandran metrics
  - File: `distributions.png`

- **Figure 3: Summary Table**
  - Publication-ready table rendering of summary statistics
  - File: `summary_table.png`

**Usage:**

```bash
# Generate plots from existing results
python bonus/generate_plots.py

# Custom input/output paths
python bonus/generate_plots.py \
  --results my_results.csv \
  --summary my_summary.csv \
  --output-dir my_plots/
```

**Output directory:** `bonus/plots/` (customizable)

## Complete Bonus Workflow

Here's how to use all bonus features together:

```bash
# Step 1: Run enhanced validation with automatic summary
python bonus/validate_bonus.py generated_pdbs \
  --out bonus/results.csv \
  --summary-out bonus/summary.csv \
  -v

# Step 2: Generate plots from results
python bonus/generate_plots.py \
  --results bonus/results.csv \
  --summary bonus/summary.csv \
  --output-dir bonus/plots

# Now you have:
# - bonus/results.csv (per-structure metrics)
# - bonus/summary.csv (per-method aggregate stats)
# - bonus/logs/validation_errors.txt (error log)
# - bonus/plots/*.png (publication-ready figures)
# - bonus/reduced_pdbs/ (hydrogen-preprocessed structures from clashscore)
```

## Data Files Generated

After running the bonus validator and plot generator, you'll have:

```
bonus/
├── validate_bonus.py              # Main enhanced validator script
├── generate_plots.py              # Plot generation script
├── results_bonus.csv              # Per-structure validation metrics (100 rows)
├── summary_by_method.csv          # Per-method summary statistics
├── logs/
│   └── validation_errors.txt      # Structured error log (timestamped)
├── plots/
│   ├── ramachandran_by_method.png # Boxplots by method
│   ├── distributions.png          # Histograms of metrics
│   └── summary_table.png          # Summary statistics table
└── reduced_pdbs/
    ├── laproteina/               # Hydrogen-added La-Proteina PDBs (if clashscore enabled)
    └── reqflow/                  # Hydrogen-added ReQFlow PDBs (if clashscore enabled)
```

## Key Enhancements Over Core Validator

| Feature | Core `validate.py` | Bonus `validate_bonus.py` |
| --- | --- | --- |
| Ramachandran | ✓ | ✓ |
| Clashscore | Optional | Automatic with graceful fallback |
| Error logging | None | Structured, timestamped |
| Per-method summary | None | ✓ Automatic |
| Recursive search | ✓ Default | ✓ Default (use `--flat-search` to disable) |
| Skip clashscore | None | ✓ `--skip-clashscore` |
| Plot generation | None | ✓ Separate script |

## Example Output

**summary_by_method.csv:**
```
method,n_total,n_successful,mean_rama_favored,median_rama_favored,mean_rama_outlier,median_rama_outlier,mean_clashscore
laproteina,50,50,0.9944,0.9949,0.0002,0.0,NA
reqflow,50,50,0.9781,0.9798,0.0046,0.0051,NA
```

**logs/validation_errors.txt (if any errors occur):**
```
[2026-05-04T06:18:30] stage=clashscore file=generated_pdbs/laproteina/laproteina_001.pdb
  probe not found
```

## Performance Notes

- **Ramachandran-only mode** (`--skip-clashscore`): ~2–5 seconds per structure
- **With clashscore** (reduce + probe): ~10–15 seconds per structure
- **Plot generation**: ~2–5 seconds for all three figures

## Troubleshooting

### "probe not found" errors

If you see clashscore failures with "probe not found", either:
- Ensure `reduce` and `probe` are installed in your conda environment
- Use `--skip-clashscore` to disable clashscore and run Ramachandran-only
- Check that `reduce` and `probe` are in your PATH: `which reduce && which probe`

### Plot generation fails

If plot generation fails, ensure pandas and matplotlib are installed:
```bash
conda install -c conda-forge pandas matplotlib
```

### No reduced PDBs generated

Reduced PDBs are only saved when clashscore preprocessing succeeds. If `reduce` is not found, reduced structures won't be written to disk. Use `--skip-clashscore` to confirm Ramachandran metrics still work.

## Integration with Core Pipeline

The bonus scripts are independent of the core pipeline. You can:

1. Use the core `validate.py` for the required submission
2. Run `validate_bonus.py` in parallel for enhanced analysis
3. Generate plots from either validator's output using `generate_plots.py`

All bonus work writes to the `bonus/` directory and does not modify the core submission structure.
