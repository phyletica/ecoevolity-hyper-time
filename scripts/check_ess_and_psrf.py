#!/usr/bin/env python

import os
import sys
import math
import pandas as pd

import pycoevolity


def get_min_ess(df):
    ess_mins = {}
    for col_name in df.columns:
        if col_name.startswith("ess_"):
            min_ess = df[col_name].min()
            if min_ess == 0.0:
                # Fixed parameter
                continue
            ess_mins[col_name] = min_ess
    return min(ess_mins.values()), ess_mins

def get_max_psrf(df):
    psrf_maxs = {}
    for col_name in df.columns:
        if col_name.startswith("psrf_"):
            max_psrf = df[col_name].max()
            if max_psrf == float('inf'):
                # Fixed parameter
                continue
            psrf_maxs[col_name] = max_psrf
    return min(psrf_maxs.values()), psrf_maxs

def main(out = sys.stdout):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    project_dir = os.path.dirname(script_dir)

    sim_dirs = (
        "exp-hyperprior-sim-study",
        "unif-hyperprior-sim-study",
        "coverage-check-exp-hyperprior",
        "coverage-check-unif-hyperprior",
    )

    overall_min_ess = 999999999999.0
    overall_max_psrf = -1.0
    for sim_dir in sim_dirs:
        results_path = os.path.join(
            project_dir,
            sim_dir,
            "results-summary.tsv.gz",
        )

        df = pd.read_csv(
            results_path,
            sep = "\t",
        )

        min_ess, ess_mins = get_min_ess(df)
        max_psrf, psrf_maxs = get_max_psrf(df)

        if min_ess < overall_min_ess:
            overall_min_ess = min_ess
        if max_psrf > overall_max_psrf:
            overall_max_psrf = max_psrf

        out.write(f"{sim_dir}\n")
        out.write(f"  Minimum ESS: {min_ess}\n")
        out.write(f"  Maximum PSRF: {max_psrf}\n")
        out.write(f"  Min ESS per parameter:\n")
        for param, val in ess_mins.items():
            out.write(f"    {param}: {val}\n")
        out.write(f"  Max PSRF per parameter:\n")
        for param, val in psrf_maxs.items():
            out.write(f"    {param}: {val}\n")

    out.write(f"Overall minimum ESS: {overall_min_ess}\n")
    out.write(f"Overall Maximum PSRF: {overall_max_psrf}\n")

if __name__ == '__main__':
    main()
