#!/usr/bin/env python

import os
import sys
import shutil
import subprocess
import multiprocessing

import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def get_ecoevolity_dir(dir_to_check = None):
    eco_path = None
    if not dir_to_check:
        eco_path = shutil.which("ecoevolity")
        if not eco_path:
            raise Exception(
                "'ecoevolity' was not found in system's PATH"
            )
    else:
        eco_path = os.path.join(dir_to_check, "ecoevolity")

    if not os.access(eco_path, os.X_OK):
        raise Exception(
            "ecoevolity found at '{eco_path}', but does have execute "
            "permissions"
        )
    return os.path.dirname(eco_path)

def run_cmd(cmd):
    result = subprocess.run(
        cmd,
        capture_output = True,
        text = True,
        check = True,
    )
    return result

def run_ecoevolity(
    config_path,
    seed,
    output_dir,
    eco_exe_dir = None,
    ignore_data = False,
    relax_constant_sites = False,
    relax_missing_sites = False,
    relax_triallelic_sites = False,
):
    eco_exe = "ecoevolity"
    if eco_exe_dir:
        eco_exe = os.path.join(eco_exe_dir, eco_exe)

    config_file_name = os.path.basename(config_path)
    config_name = os.path.splitext(config_file_name)[0]

    prefix = os.path.join(
        output_dir,
        f"run-{seed}-",
    )

    state_log_path = f"{prefix}{config_name}-state-run-1.log"

    cmd = [
        eco_exe,
        f"--seed={seed}",
        f"--prefix={prefix}",
    ]
    if ignore_data:
        cmd.append("--ignore-data")
    if relax_constant_sites:
        cmd.append("--relax-constant-sites")
    if relax_missing_sites:
        cmd.append("--relax-missing-sites")
    if relax_triallelic_sites:
        cmd.append("--relax-triallelic-sites")
    cmd.append(config_path)

    if os.path.exists(state_log_path):
        raise Exception(
            f"Output log path already exists: '{state_log_path}'\n"
        )

    result = run_cmd(cmd)
    return result, state_log_path

def collect_prior_samples(
    seeds,
    config_path,
    output_dir,
    number_of_procs = 4,
    eco_exe_dir = None,
):
    log_paths = []
    with multiprocessing.Pool(number_of_procs) as pool:
        workers = [
            pool.apply_async(
                run_ecoevolity,
                args = (
                    config_path,
                    seed,
                    output_dir,
                    eco_exe_dir,
                    True, # ignore_data
                ))
            for seed in seeds
        ]
        # sys.stdout.write(
        #     f"Loaded {len(workers)} workers for {number_of_runs} processors\n"
        # )
        for result, state_log_path in (w.get() for w in workers):
            if result.returncode != 0:
                raise Exception(
                    f"ERROR: ecoevolity run returned non-zero exit code "
                    f"'{result.returncode}'; here is the stderr:\n"
                    f"{result.stderr}\n")
            log_paths.append(state_log_path)
    return log_paths

def run_sumcoevolity(
    config_path,
    input_state_log_paths,
    seed,
    output_dir,
    num_prior_draws = 1000000,
    eco_exe_dir = None,
    burnin = 0,
):
    eco_exe = "sumcoevolity"
    if eco_exe_dir:
        eco_exe = os.path.join(eco_exe_dir, eco_exe)

    config_file_name = os.path.basename(config_path)
    config_name = os.path.splitext(config_file_name)[0]

    prefix = os.path.join(
        output_dir,
        f"{config_name}-seed-{seed}-n-{num_prior_draws}-",
    )

    results_path = f"{prefix}sumcoevolity-results-nevents.txt"

    cmd = [
        eco_exe,
        f"--seed={seed}",
        f"--prefix={prefix}",
        f"--config={config_path}",
        f"--number-of-samples={num_prior_draws}",
        f"--burnin={burnin}",
        *input_state_log_paths,
    ]

    if os.path.exists(results_path):
        raise Exception(
            f"Output results path already exists: '{results_path}'\n"
        )

    result = run_cmd(cmd)
    return result, results_path
