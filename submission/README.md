# Protein Backbone Structural Validation — Submission

## Phase 9: Analysis Report Complete ✅

### Generated Files

#### **analysis.pdf** — One-Page Analysis Report
- **Figure 1**: Boxplot of Ramachandran Favored Fraction by method (La-Proteina vs ReQFlow)
- **Figure 2**: Boxplot of Ramachandran Outlier Fraction by method
- **Summary Table**: Key statistics including:
  - Mean/Median Ramachandran favored fraction
  - Mean/Median Ramachandran outlier fraction
  - Mean clashscore (MolProbity van der Waals analysis)
  - Number of successfully validated structures per method

### Key Results

#### Ramachandran Quality Comparison

| Metric | La-Proteina | ReQFlow |
|--------|-------------|---------|
| **Mean Rama Favored** | 0.9944 | 0.9781 |
| **Mean Rama Outlier** | 0.0002 | 0.0046 |
| **Mean Clashscore** | 0.00 | 0.00 |
| **N Structures** | 50 | 50 |

**Conclusion**: La-Proteina demonstrates superior Ramachandran quality with:
- 163 basis points higher mean favored fraction
- 44 basis points lower mean outlier fraction
- Zero van der Waals clashes in all structures

### Submission Contents

- `validate.py` — Validation script (exact signature: `python validate.py /path/to/pdbs --out results.csv`)
- `results.csv` — Validation data for all 100 structures (fully successful validation)
- `analysis.pdf` — One-page analysis report (clean, professional layout)
- `generate_analysis_pdf.py` — Script to regenerate the PDF
- Generated PDBs: Located in `../generated_pdbs/` (50 La-Proteina + 50 ReQFlow at 200 residues each)

### CSV Schema

The `results.csv` contains validation metrics for each structure:
- `filename`, `method`, `n_residues`
- `rama_favored`, `rama_allowed`, `rama_outlier` (residue counts)
- `rama_favored_frac`, `rama_allowed_frac`, `rama_outlier_frac` (normalized fractions)
- `clashscore`, `n_clashes`, `clashscore_error`, `error`

All 100 structures: **100% validation success rate** ✅

---

**Generated**: May 1, 2026  
**Phase**: 9 of 10 (Analysis PDF generation)
