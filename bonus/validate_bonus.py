#!/usr/bin/env python
"""Bonus validator with robust clashscore fallback and error logging.

Features:
- Ramachandran analysis by default for all PDBs.
- Clashscore attempted automatically when reduce/probe are available.
- Graceful fallback to NA when clashscore cannot be computed.
- Optional --skip-clashscore flag.
- Structured error logging to bonus/logs/validation_errors.txt.
"""

import argparse
import csv
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from datetime import datetime
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

    trim_rc, _, trim_size = _run_command_to_file(
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

    # reduce may return non-zero even when output is valid.
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


def _infer_method(pdb_path):
    filename = os.path.basename(pdb_path).lower()
    if filename.startswith("laproteina"):
        return "laproteina"
    if filename.startswith("reqflow"):
        return "reqflow"
    return "unknown"


def _find_pdb_files(input_dir, recursive=False):
    input_path = Path(input_dir)
    if recursive:
        pdb_iter = input_path.rglob("*.pdb")
    else:
        pdb_iter = input_path.glob("*.pdb")
    for pdb_file in sorted(pdb_iter):
        yield str(pdb_file)


def _append_error_log(log_file, pdb_path, stage, message):
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")
    with open(log_file, "a") as handle:
        handle.write(f"[{timestamp}] stage={stage} file={pdb_path}\n")
        handle.write(f"  {message}\n")


def _to_float(value):
    if value in (None, "", "NA"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_or_na(value, digits=4):
    if value is None:
        return "NA"
    return round(value, digits)


def _write_method_summary(results, summary_out):
    summary_path = Path(summary_out)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    by_method = {}
    for row in results:
        method = row.get("method", "unknown") or "unknown"
        by_method.setdefault(method, []).append(row)

    fieldnames = [
        "method",
        "n_total",
        "n_successful",
        "mean_rama_favored",
        "median_rama_favored",
        "mean_rama_outlier",
        "median_rama_outlier",
        "mean_clashscore",
    ]

    with open(summary_path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for method in sorted(by_method):
            rows = by_method[method]
            successful = [r for r in rows if not r.get("error")]
            # rama_* now store fractions directly (per new schema)
            favored_vals = [_to_float(r.get("rama_favored")) for r in successful]
            outlier_vals = [_to_float(r.get("rama_outlier")) for r in successful]
            clash_vals = [_to_float(r.get("clashscore")) for r in successful]

            favored_vals = [v for v in favored_vals if v is not None]
            outlier_vals = [v for v in outlier_vals if v is not None]
            clash_vals = [v for v in clash_vals if v is not None]

            writer.writerow(
                {
                    "method": method,
                    "n_total": len(rows),
                    "n_successful": len(successful),
                    "mean_rama_favored": _round_or_na(
                        sum(favored_vals) / len(favored_vals) if favored_vals else None,
                        4,
                    ),
                    "median_rama_favored": _round_or_na(
                        statistics.median(favored_vals) if favored_vals else None,
                        4,
                    ),
                    "mean_rama_outlier": _round_or_na(
                        sum(outlier_vals) / len(outlier_vals) if outlier_vals else None,
                        4,
                    ),
                    "median_rama_outlier": _round_or_na(
                        statistics.median(outlier_vals) if outlier_vals else None,
                        4,
                    ),
                    "mean_clashscore": _round_or_na(
                        sum(clash_vals) / len(clash_vals) if clash_vals else None,
                        2,
                    ),
                }
            )


def validate_pdb(pdb_path, skip_clashscore=False, reduced_root=None, log_file=None):
    result = {
        "filename": os.path.basename(pdb_path),
        "method": _infer_method(pdb_path),  # Needed for method-level summaries
        "n_residues": None,
        # Per assignment schema: rama_* store fractions directly
        "rama_favored": None,
        "rama_allowed": None,
        "rama_outlier": None,
        "clashscore": "NA",
        "n_clashes": "NA",
        "clashscore_error": "",
        "error": "",
    }

    try:
        rama_input = pdb_path

        if not skip_clashscore:
            with tempfile.TemporaryDirectory(prefix="validate_bonus_") as work_dir:
                reduced_path, reduce_error = _run_reduce_pipeline(pdb_path, work_dir)
                if reduced_path is not None:
                    rama_input = reduced_path
                    if reduced_root is not None:
                        method_dir = Path(reduced_root) / result["method"]
                        method_dir.mkdir(parents=True, exist_ok=True)
                        reduced_name = os.path.basename(pdb_path).replace(".pdb", "_reduced.pdb")
                        reduced_copy_path = method_dir / reduced_name
                        shutil.copy(reduced_path, str(reduced_copy_path))

                    clashscore_value, n_clashes, clash_error = _run_clashscore(reduced_path)
                    result["clashscore"] = clashscore_value if clash_error is None else "NA"
                    result["n_clashes"] = n_clashes if clash_error is None else "NA"
                    result["clashscore_error"] = clash_error or ""

                    if clash_error and log_file:
                        _append_error_log(log_file, pdb_path, "clashscore", clash_error)
                else:
                    result["clashscore_error"] = reduce_error or "reduce failed"
                    if log_file:
                        _append_error_log(log_file, pdb_path, "reduce", result["clashscore_error"])

                pdb_input = pdb.input(file_name=rama_input)
                hierarchy = pdb_input.construct_hierarchy()
                rama = ramalyze.ramalyze(hierarchy)
        else:
            pdb_input = pdb.input(file_name=rama_input)
            hierarchy = pdb_input.construct_hierarchy()
            rama = ramalyze.ramalyze(hierarchy)
            result["clashscore_error"] = "skipped by --skip-clashscore"

        result["n_residues"] = rama.n_total
        # Per assignment schema: store fractions directly in rama_* columns
        if rama.n_total:
            result["rama_favored"] = round(rama.n_favored / rama.n_total, 4)
            result["rama_allowed"] = round(rama.n_allowed / rama.n_total, 4)
            result["rama_outlier"] = round(rama.n_outliers / rama.n_total, 4)
        else:
            result["rama_favored"] = None
            result["rama_allowed"] = None
            result["rama_outlier"] = None

    except Exception as exc:
        result["error"] = str(exc)
        if log_file:
            _append_error_log(log_file, pdb_path, "validate", str(exc))

    return result


def validate_directory(
    input_dir,
    output_csv,
    summary_out="bonus/summary_by_method.csv",
    recursive=False,
    skip_clashscore=False,
    reduced_root="bonus/reduced_pdbs",
    log_file="bonus/logs/validation_errors.txt",
    verbose=False,
):
    pdb_files = list(_find_pdb_files(input_dir, recursive=recursive))

    if not pdb_files:
        print(f"No PDB files found in {input_dir}")
        return 1

    if verbose:
        print(f"Found {len(pdb_files)} PDB files")

    reduced_dir = None if skip_clashscore else reduced_root

    results = []
    failed = 0
    clashscore_attempted = 0
    clashscore_failed = 0

    for index, pdb_path in enumerate(pdb_files, 1):
        if verbose:
            print(f"[{index}/{len(pdb_files)}] Validating {os.path.basename(pdb_path)}...")

        result = validate_pdb(
            pdb_path,
            skip_clashscore=skip_clashscore,
            reduced_root=reduced_dir,
            log_file=log_file,
        )
        results.append(result)

        if result["n_residues"] is None:
            failed += 1
            if verbose:
                print("  ERROR: validation failed")

        if result["clashscore"] == "NA":
            clashscore_failed += 1
        else:
            clashscore_attempted += 1

    out_dir = os.path.dirname(output_csv)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    fieldnames = [
        "filename",
        "n_residues",
        "rama_favored",
        "rama_allowed",
        "rama_outlier",
        "clashscore",
        "n_clashes",
        "clashscore_error",
        "error",
    ]

    with open(output_csv, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        # Only write fields that are in fieldnames (filters out 'method' which is for internal summaries)
        filtered_results = [{k: v for k, v in r.items() if k in fieldnames} for r in results]
        writer.writerows(filtered_results)

    if summary_out:
        _write_method_summary(results, summary_out)

    print("Validation complete:")
    print(f"  Processed: {len(pdb_files)}")
    print(f"  Successful: {len(pdb_files) - failed}")
    print(f"  Failed: {failed}")
    print(f"  Clashscore computed for: {clashscore_attempted}")
    print(f"  Clashscore NA for: {clashscore_failed}")
    print(f"  Results written to: {output_csv}")
    if summary_out:
        print(f"  Summary written to: {summary_out}")
    print(f"  Error log: {log_file}")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Bonus validator with robust clashscore fallback")
    parser.add_argument("input_dir", help="Directory containing PDB files to validate")
    parser.add_argument("--out", required=True, help="Output CSV file path")
    parser.add_argument(
        "--summary-out",
        default="bonus/summary_by_method.csv",
        help="Output CSV path for per-method summary statistics",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively search input directory for PDB files",
    )
    parser.add_argument(
        "--skip-clashscore",
        action="store_true",
        help="Skip clashscore and run Ramachandran-only validation",
    )
    parser.add_argument(
        "--reduced-dir",
        default="bonus/reduced_pdbs",
        help="Directory to store reduced PDB files when clashscore runs",
    )
    parser.add_argument(
        "--log-file",
        default="bonus/logs/validation_errors.txt",
        help="Path to append structured validation errors",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Print progress messages")
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory not found: {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    rc = validate_directory(
        args.input_dir,
        args.out,
        summary_out=args.summary_out,
        recursive=args.recursive,
        skip_clashscore=args.skip_clashscore,
        reduced_root=args.reduced_dir,
        log_file=args.log_file,
        verbose=args.verbose,
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
