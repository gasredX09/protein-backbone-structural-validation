#!/usr/bin/env python
"""Bonus plot generator from validation results.

Generates publication-quality figures from results CSV:
- Ramachandran favored fraction by method
- Ramachandran outlier fraction by method
- Summary statistics table

Usage:
    python bonus/generate_plots.py --results bonus/results_bonus.csv --summary bonus/summary_by_method.csv
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def generate_plots(results_csv, summary_csv, output_dir="bonus/plots"):
    """Generate publication-quality plots from validation results."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        df = pd.read_csv(results_csv)
        summary_df = pd.read_csv(summary_csv)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Figure 1: Boxplot of Ramachandran Favored by Method
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    methods_order = sorted(df["method"].unique())
    colors = {"laproteina": "#2E86AB", "reqflow": "#A23B72"}

    # Favored fraction
    ax1 = axes[0]
    data_favored = [
        df[df["method"] == method]["rama_favored_frac"].values for method in methods_order
    ]
    bp1 = ax1.boxplot(
        data_favored,
        tick_labels=[m.capitalize() for m in methods_order],
        patch_artist=True,
        widths=0.6,
    )
    for patch, method in zip(bp1["boxes"], methods_order):
        patch.set_facecolor(colors.get(method, "#999999"))
        patch.set_alpha(0.7)

    ax1.set_ylabel("Ramachandran Favored Fraction", fontsize=11, fontweight="bold")
    ax1.set_title("Favored Residue Fraction", fontsize=12, fontweight="bold")
    ax1.grid(axis="y", alpha=0.3, linestyle="--")
    ax1.set_ylim([0.93, 1.01])

    # Outlier fraction
    ax2 = axes[1]
    data_outlier = [
        df[df["method"] == method]["rama_outlier_frac"].values for method in methods_order
    ]
    bp2 = ax2.boxplot(
        data_outlier,
        tick_labels=[m.capitalize() for m in methods_order],
        patch_artist=True,
        widths=0.6,
    )
    for patch, method in zip(bp2["boxes"], methods_order):
        patch.set_facecolor(colors.get(method, "#999999"))
        patch.set_alpha(0.7)

    ax2.set_ylabel("Ramachandran Outlier Fraction", fontsize=11, fontweight="bold")
    ax2.set_title("Outlier Residue Fraction", fontsize=12, fontweight="bold")
    ax2.grid(axis="y", alpha=0.3, linestyle="--")

    fig.suptitle("Ramachandran Analysis by Method", fontsize=13, fontweight="bold", y=1.00)
    plt.tight_layout()
    fig.savefig(output_path / "ramachandran_by_method.png", dpi=150, bbox_inches="tight")
    print(f"✓ Saved: {output_path / 'ramachandran_by_method.png'}")
    plt.close(fig)

    # Figure 2: Distribution plots
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Ramachandran Distributions", fontsize=13, fontweight="bold", y=1.00)

    for idx, method in enumerate(methods_order):
        method_df = df[df["method"] == method]
        color = colors.get(method, "#999999")

        # Histogram: favored
        ax = axes[idx, 0]
        ax.hist(
            method_df["rama_favored_frac"],
            bins=15,
            alpha=0.7,
            color=color,
            edgecolor="black",
        )
        ax.set_xlabel("Favored Fraction", fontsize=10)
        ax.set_ylabel("Count", fontsize=10)
        ax.set_title(f"{method.capitalize()} - Favored", fontsize=11, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)

        # Histogram: outlier
        ax = axes[idx, 1]
        ax.hist(
            method_df["rama_outlier_frac"],
            bins=15,
            alpha=0.7,
            color=color,
            edgecolor="black",
        )
        ax.set_xlabel("Outlier Fraction", fontsize=10)
        ax.set_ylabel("Count", fontsize=10)
        ax.set_title(f"{method.capitalize()} - Outlier", fontsize=11, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    fig.savefig(output_path / "distributions.png", dpi=150, bbox_inches="tight")
    print(f"✓ Saved: {output_path / 'distributions.png'}")
    plt.close(fig)

    # Figure 3: Summary table as figure
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.axis("tight")
    ax.axis("off")

    table_data = []
    for _, row in summary_df.iterrows():
        table_data.append(
            [
                row["method"].capitalize(),
                f"{row['mean_rama_favored']:.4f}",
                f"{row['median_rama_favored']:.4f}",
                f"{row['mean_rama_outlier']:.6f}",
                f"{row['median_rama_outlier']:.6f}",
            ]
        )

    columns = [
        "Method",
        "Mean Favored Fraction",
        "Median Favored Fraction",
        "Mean Outlier Fraction",
        "Median Outlier Fraction",
    ]

    table = ax.table(
        cellText=table_data,
        colLabels=columns,
        cellLoc="center",
        loc="center",
        colWidths=[0.18, 0.2, 0.2, 0.2, 0.2],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.5)

    # Style header
    for i in range(len(columns)):
        table[(0, i)].set_facecolor("#2C3E50")
        table[(0, i)].set_text_props(weight="bold", color="white")

    # Alternate row colors
    for i in range(1, len(table_data) + 1):
        for j in range(len(columns)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor("#ECF0F1")
            else:
                table[(i, j)].set_facecolor("#FFFFFF")

    fig.suptitle("Validation Summary by Method", fontsize=12, fontweight="bold", y=0.98)
    fig.savefig(output_path / "summary_table.png", dpi=150, bbox_inches="tight")
    print(f"✓ Saved: {output_path / 'summary_table.png'}")
    plt.close(fig)

    print(f"\nAll plots saved to: {output_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Generate plots from bonus validation results"
    )
    parser.add_argument(
        "--results",
        default="bonus/results_bonus.csv",
        help="Path to results CSV from bonus validator",
    )
    parser.add_argument(
        "--summary",
        default="bonus/summary_by_method.csv",
        help="Path to summary CSV from bonus validator",
    )
    parser.add_argument(
        "--output-dir",
        default="bonus/plots",
        help="Directory to save generated plots",
    )
    args = parser.parse_args()

    return generate_plots(args.results, args.summary, args.output_dir)


if __name__ == "__main__":
    sys.exit(main())
