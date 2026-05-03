#!/usr/bin/env python
"""Validate protein backbone structures using CCTBX.

This script computes Ramachandran statistics for each PDB and optionally
computes MolProbity-style clashscore after preprocessing with reduce/probe.

Usage:
    python validate.py /path/to/pdb/directory --out results.csv
"""

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

from iotbx import pdb
from mmtbx.validation import ramalyze

REDUCE_BIN = shutil.which("reduce")
PROBE_BIN = shutil.which("probe")


def _count_atoms(pdb_path):
    atom_count = 0
    with open(pdb_path, "r") as handle:
        for line in handle:
            if line.startswith(("ATOM  ", "HETATM")):
                atom_count += 1
    return atom_count


def _run_command_to_file(command, output_path):
    with open(output_path, "w") as handle:
        completed = subprocess.run(
            command,
            stdout=handle,
            stderr=subprocess.PIPE,
            text=True,
        )
    output_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    return completed.returncode, completed.stderr, output_size


def _run_reduce_pipeline(input_pdb, work_dir):
    if not REDUCE_BIN:
        return None, "reduce not found"

    trimmed_path = os.path.join(work_dir, "trimmed.pdb")
    reduced_path = os.path.join(work_dir, "reduced.pdb")

    trim_rc, trim_stderr, trim_size = _run_command_to_file(
        [REDUCE_BIN, "-quiet", "-trim", "-allalt", input_pdb],
        trimmed_path,
    )
    if trim_size == 0:
        return None, f"reduce trim produced no output (rc={trim_rc})"

    build_rc, build_stderr, build_size = _run_command_to_file(
        [REDUCE_BIN, "-quiet", "-build", trimmed_path],
        reduced_path,
    )
    if build_size == 0:
        return None, f"reduce build produced no output (rc={build_rc})"

    # reduce can return non-zero even when it successfully writes a usable PDB.
    # We accept the file if stdout is non-empty and there is no fatal stderr text.
    if build_rc not in (0, 1, 255):
        return None, f"reduce build failed (rc={build_rc})"
    if build_stderr.strip() and "ERROR" in build_stderr.upper():
        return None, build_stderr.strip()

    return reduced_path, None


def _parse_probe_summary(summary_text):
    n_clashes = None
    for line in summary_text.splitlines():
        if line.lstrip().startswith(":SUM"):
            numbers = [int(value) for value in re.findall(r"-?\d+", line)]
            if len(numbers) >= 6:
                n_clashes = numbers[3]
                break
    return n_clashes


def _run_clashscore(reduced_pdb):
    if not PROBE_BIN:
        return "NA", "NA", "probe not found"

    probe_run = subprocess.run(
        [PROBE_BIN, "-SUMMARY", reduced_pdb],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    summary_text = probe_run.stdout
    n_clashes = _parse_probe_summary(summary_text)
    if n_clashes is None:
        return "NA", "NA", "could not parse probe summary"

    atom_count = _count_atoms(reduced_pdb)
    if atom_count <= 0:
        return "NA", "NA", "no atoms found in reduced structure"

    clashscore = round((n_clashes * 1000.0) / atom_count, 2)
    return clashscore, n_clashes, None


def validate_pdb(pdb_path):
    """Validate a single PDB file."""
    result = {
        "filename": os.path.basename(pdb_path),
        "method": _infer_method(pdb_path),
        "n_residues": None,
        "rama_favored": None,
        "rama_allowed": None,
        "rama_outlier": None,
        "rama_favored_frac": None,
        "rama_allowed_frac": None,
        "rama_outlier_frac": None,
        "clashscore": "NA",
        "n_clashes": "NA",
        "clashscore_error": "",
        "error": "",
    }

    try:
        # Determine output directory for reduced PDB
        method = result["method"]
        reduced_output_dir = None
        if method in ("laproteina", "reqflow"):
            reduced_output_dir = Path("reduced_pdbs") / method
            reduced_output_dir.mkdir(parents=True, exist_ok=True)
        
        with tempfile.TemporaryDirectory(prefix="validate_") as work_dir:
            reduced_path, reduce_error = _run_reduce_pipeline(pdb_path, work_dir)
            rama_input = reduced_path if reduced_path is not None else pdb_path

            pdb_input = pdb.input(file_name=rama_input)
            hierarchy = pdb_input.construct_hierarchy()
            rama = ramalyze.ramalyze(hierarchy)

            result["n_residues"] = rama.n_total
            result["rama_favored"] = rama.n_favored
            result["rama_allowed"] = rama.n_allowed
            result["rama_outlier"] = rama.n_outliers
            if rama.n_total:
                result["rama_favored_frac"] = round(rama.n_favored / rama.n_total, 4)
                result["rama_allowed_frac"] = round(rama.n_allowed / rama.n_total, 4)
                result["rama_outlier_frac"] = round(rama.n_outliers / rama.n_total, 4)

            if reduced_path is not None:
                # Save reduced PDB to reduced_pdbs directory
                if reduced_output_dir:
                    basename = os.path.basename(pdb_path)
                    reduced_name = basename.replace(".pdb", "_reduced.pdb")
                    final_reduced_path = reduced_output_dir / reduced_name
                    shutil.copy(reduced_path, str(final_reduced_path))
                
                clashscore_value, n_clashes, clash_error = _run_clashscore(reduced_path)
                result["clashscore"] = clashscore_value if clash_error is None else "NA"
                result["n_clashes"] = n_clashes if clash_error is None else "NA"
                result["clashscore_error"] = clash_error or ""
            else:
                result["clashscore_error"] = reduce_error or "reduce failed"

    except Exception as exc:
        result["error"] = str(exc)

    return result


def find_pdb_files(input_dir):
    """Recursively find all PDB files in a directory."""
    input_path = Path(input_dir)
    for pdb_file in sorted(input_path.rglob("*.pdb")):
        yield str(pdb_file)


def _infer_method(pdb_path):
    filename = os.path.basename(pdb_path).lower()
    if filename.startswith("laproteina"):
        return "laproteina"
    if filename.startswith("reqflow"):
        return "reqflow"
    return "unknown"


def validate_directory(input_dir, output_csv, verbose=False):
    """Validate all PDB files in a directory."""
    pdb_files = list(find_pdb_files(input_dir))

    if not pdb_files:
        print(f"No PDB files found in {input_dir}")
        return

    if verbose:
        print(f"Found {len(pdb_files)} PDB files")

    results = []
    failed = 0
    clashscore_attempted = 0
    clashscore_failed = 0

    for index, pdb_path in enumerate(pdb_files, 1):
        if verbose:
            print(f"[{index}/{len(pdb_files)}] Validating {os.path.basename(pdb_path)}...")

        result = validate_pdb(pdb_path)
        results.append(result)

        if result["n_residues"] is None:
            failed += 1
            if verbose:
                print("  ERROR: validation failed")
        if result["clashscore"] == "NA":
            clashscore_failed += 1
        else:
            clashscore_attempted += 1

    fieldnames = [
        "filename",
        "method",
        "n_residues",
        "rama_favored",
        "rama_allowed",
        "rama_outlier",
        "rama_favored_frac",
        "rama_allowed_frac",
        "rama_outlier_frac",
        "clashscore",
        "n_clashes",
        "clashscore_error",
        "error",
    ]

    with open(output_csv, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    if verbose:
        print("\nValidation complete:")
        print(f"  Processed: {len(pdb_files)}")
        print(f"  Successful: {len(pdb_files) - failed}")
        print(f"  Failed: {failed}")
        print(f"  Clashscore computed for: {clashscore_attempted}")
        print(f"  Clashscore NA for: {clashscore_failed}")
        print(f"  Results written to: {output_csv}")


def main():
    parser = argparse.ArgumentParser(description="Validate protein backbone structures using CCTBX")
    parser.add_argument("input_dir", help="Directory containing PDB files to validate")
    parser.add_argument("--out", required=True, help="Output CSV file path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print progress messages")
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory not found: {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:
        validate_directory(args.input_dir, args.out, verbose=args.verbose)
    except Exception as exc:
        print(f"Error during validation: {exc}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
