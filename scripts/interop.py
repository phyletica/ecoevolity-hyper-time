#!/usr/bin/env python

import os
import sys
import math
import re
import shutil
import gzip
import subprocess
import multiprocessing
import json
import glob
import pycoevolity

import eco_config
import project_utils


def compress_file(path, compressed_path):
    with open(path, 'rb') as in_stream:
        with gzip.open(compressed_path, 'wb') as out_stream:
            shutil.copyfileobj(in_stream, out_stream)

def compress_output_path(log_path, output_dir = None):
    if not output_dir:
        output_dir = os.path.dirname(log_path)
    gz_log_path = os.path.join(
        output_dir,
        f"{os.path.basename(log_path)}.gz",
    )
    compress_file(log_path, gz_log_path)
    return gz_log_path

# def parse_sim_results(results):
#     sim_configs = results["simulation_configs"]
#     inf_configs = results["inference_configs"]
#     nchains = results["number_of_chains"]
#     burnin = results["burnin"]
#     for sim_conf, sims in results["simulations"].items():
#         assert sim_conf in sim_configs
#         for true_vals_path, inf_results in sims.items():
#             for inf_conf, rep_results in inf_results.items():
#                 assert inf_conf in inf_configs
#                 assert len(rep_results["chains"]) == nchains
#                 # At this point I think it is worth simply using pycoevolity's
#                 # posterior code, which means we need to specify/fix burnin
#                 # from the beginning and use it here, and assemble one
#                 # posterior sample and summary across chaings
#                 # We cannot serialize pycoevolity posterior classes to json, so
#                 # we need to decide how to store results

def load_results_json(in_stream):
    return json.load(in_stream)

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
            f"ecoevolity found at '{eco_path}', but does have execute "
            f"permissions"
        )
    return os.path.dirname(eco_path)

def parse_info_from_output(output_str):
    run_time_pattern = re.compile(
        r'^\s*runtime:\s+(?P<run_time>\d+)\s+seconds\.\s*$',
        re.IGNORECASE,
    )
    summary_pattern = re.compile(
        r'^\s*Summary\s+of\s+data\s+from\s+(?P<num_comparisons>\d+)\s+comparisons:\s*$',
        re.IGNORECASE,
    )
    num_var_sites_pattern = re.compile(
        r'^\s*Number\s+of\s+variable\s+sites:\s+(?P<num_var_sites>\d+)\s*$',
        re.IGNORECASE,
    )
    run_time = None
    num_comparisons = None
    num_var_sites = []
    for l in output_str.splitlines():
        line = l.strip()
        m = summary_pattern.match(line)
        if m:
            num_comparisons = int(m.group("num_comparisons"))
            continue
        m = num_var_sites_pattern.match(line)
        if m:
            num_var_sites.append(int(m.group("num_var_sites")))
            continue
        m = run_time_pattern.match(line)
        if m:
            run_time = int(m.group("run_time"))
    if num_comparisons is None:
        raise Exception(
            f"Could not find number of comparisons in this output:\n{output_str}\n"
        )
    if not num_var_sites:
        raise Exception(
            f"Could not find number of variable sites in this output:\n{output_str}\n"
        )
    if run_time is None:
        raise Exception(
            f"Could not find runtime in this output:\n{output_str}\n"
        )
    if num_comparisons != len(num_var_sites):
        raise Exception(
            f"Expected number of variable sites for {num_comparisons} pairs, "
            f"but found {len(num_var_sites)} in this output:\n{output_str}\n"
        )
    return run_time, num_var_sites

def run_cmd(cmd, timeout = None):
    result = subprocess.run(
        cmd,
        capture_output = True,
        text = True,
        check = True,
        timeout = timeout,
    )
    return result

def clean_up_ecoevolity_output(state_log_path):
    operator_log_path.replace("state", "operator")
    if os.path.exists(state_log_path):
        os.remove(state_log_path)
    if os.path.exists(operator_log_path):
        os.remove(operator_log_path)
    return

def run_ecoevolity(
    config_path,
    seed,
    output_dir,
    eco_exe_dir = None,
    ignore_data = False,
    relax_constant_sites = False,
    relax_missing_sites = False,
    relax_triallelic_sites = False,
    timeout = None,
    max_num_attempts = 1,
    extra_returns = [],
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

    for attempt_idx in range(max_num_attempts):
        try:
            result = run_cmd(cmd, timeout = timeout)
            # `check_returncode` will raise CalledProcessError if return code
            # is non-zero This is likely redundant given we use `check = True`
            # in `run_cmd`, but it doesn't hurt to double check
            result.check_returncode()
            break
        except Exception as e:
            if (attempt_idx + 1) < max_num_attempts:
                sys.stderr.write(
                    f"Attempt {attempt_idx + 2} for command:\n\t{cmd}\n"
                )
                clean_up_ecoevolity_output(state_log_path)
                continue
            raise e

    run_time = None
    try:
        run_time, num_var_sites = parse_info_from_output(result.stdout)
    except Exception as e:
        raise Exception(
            f"ERROR: could not parse stdout from ecoevolity run; "
            f"here is the run's stdout and stderr:\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}\n"
        )
    return run_time, num_var_sites, state_log_path, *extra_returns

def get_comparison_map(
    simcoevolity_config_comparisons,
    inference_config_comparisons,
):
    if len(simcoevolity_config_comparisons) != len(inference_config_comparisons):
        raise Exception(
            f"simcoevolity config ({len(simcoevolity_config_comparisons)}) "
            f"and inference config ({len(inference_config_comparisons)}) "
            f"have different number of comparisons."
        )
    to_simco_map = {}
    for i, i_comp in enumerate(inference_config_comparisons):
        found = False
        i_path = os.path.basename(i_comp["comparison"]["path"])
        for j, s_comp in enumerate(simcoevolity_config_comparisons):
            s_path = s_comp["comparison"]["path"]
            if s_path.endswith(i_path):
                if found is True:
                    raise Exception(
                        f"Multiple comparisons' paths in the simcoevolity "
                        f"match path in inference config ({i_path})."
                    )
                found = True
                assert not i in to_simco_map
                to_simco_map[i] = j
        if not found:
            raise Exception(
                f"Comparison path {i_path} in inference config does not match "
                f"any comparison paths in the simcoevolity config."
            )
    return to_simco_map

def create_sim_configs(sim_config_paths, inference_config_paths):
    sim_infer_config_paths = []
    for s_conf_path in sim_config_paths:
        s_conf = eco_config.get_yaml_config(s_conf_path)
        s_conf_path_prefix = os.path.splitext(s_conf_path)[0]
        sim_infer_confs = []
        for infer_conf_path in inference_config_paths:
            i_conf = eco_config.get_yaml_config(infer_conf_path)
            i_conf_name = os.path.splitext(os.path.basename(infer_conf_path))[0]
            i_out_path = f"{s_conf_path_prefix}-{i_conf_name}.yml"
            inf_to_sim_indices = get_comparison_map(
                simcoevolity_config_comparisons = s_conf["comparisons"],
                inference_config_comparisons = i_conf["comparisons"],
            )
            for i_idx, s_idx in inf_to_sim_indices.items():
                i_conf["comparisons"][i_idx]["comparison"]["path"]                      = s_conf["comparisons"][s_idx]["comparison"]["path"]
                # Ploidy is really a modeling choice
                # i_conf["comparisons"][i_idx]["ploidy"]                    = s_conf["comparisons"][s_idx]["ploidy"]
                i_conf["comparisons"][i_idx]["comparison"]["genotypes_are_diploid"]     = s_conf["comparisons"][s_idx]["comparison"]["genotypes_are_diploid"]
                i_conf["comparisons"][i_idx]["comparison"]["markers_are_dominant"]      = s_conf["comparisons"][s_idx]["comparison"]["markers_are_dominant"]
                i_conf["comparisons"][i_idx]["comparison"]["population_name_delimiter"] = s_conf["comparisons"][s_idx]["comparison"]["population_name_delimiter"]
                i_conf["comparisons"][i_idx]["comparison"]["population_name_is_prefix"] = s_conf["comparisons"][s_idx]["comparison"]["population_name_is_prefix"]
                i_conf["comparisons"][i_idx]["comparison"]["constant_sites_removed"]    = s_conf["comparisons"][s_idx]["comparison"]["constant_sites_removed"]
            eco_config.write_yaml_config(i_conf, i_out_path)
            sim_infer_confs.append((i_out_path, infer_conf_path))
        sim_infer_config_paths.append(tuple(sim_infer_confs))
    return sim_infer_config_paths

def run_simcoevolity(
    sim_config_path,
    infer_config_paths,
    seed,
    output_dir,
    number_of_replicates,
    eco_exe_dir = None,
    singleton_sample_prob = None,
    locus_size = None,
    max_one_variable_site_per_locus = False,
    charsets = False,
    relax_constant_sites = False,
    relax_missing_sites = False,
    relax_triallelic_sites = False,
    output_nexus = False,
):
    eco_exe = "simcoevolity"
    if eco_exe_dir:
        eco_exe = os.path.join(eco_exe_dir, eco_exe)

    prefix = f"seed-{seed}-"

    cmd = [
        eco_exe,
        f"--seed={seed}",
        f"--number-of-replicates={number_of_replicates}",
        f"--output-directory={output_dir}",
        f"--prefix={prefix}",
    ]
    if not singleton_sample_prob is None:
        cmd.append(f"--singleton-sample-probability={singleton_sample_prob}")
    if not locus_size is None:
        cmd.append(f"--locus-size={locus_size}")
    if max_one_variable_site_per_locus:
        cmd.append("--max-one-variable-site-per-locus")
    if charsets:
        cmd.append("--charsets")
    if relax_constant_sites:
        cmd.append("--relax-constant-sites")
    if relax_missing_sites:
        cmd.append("--relax-missing-sites")
    if relax_triallelic_sites:
        cmd.append("--relax-triallelic-sites")
    if output_nexus:
        cmd.append("--nexus")
    cmd.append(sim_config_path)

    full_prefix = os.path.join(
        output_dir,
        prefix,
    )
    sim_model_out_path = f"{full_prefix}simcoevolity-model-used-for-sims.yml"

    if os.path.exists(sim_model_out_path):
        raise Exception(
            f"Output path already exists: '{sim_model_out_path}'\n"
        )

    result = run_cmd(cmd)
    if result.returncode != 0:
        raise Exception(
            f"ERROR: simcoevolity run returned non-zero exit code "
            f"'{result.returncode}'; here is the stderr:\n"
            f"{result.stderr}\n"
        )
    run_time, num_var_sites = parse_info_from_output(result.stderr)


    config_paths = glob.glob(
        f"{full_prefix}simcoevolity-sim-[0-9]*-config.yml"
    )
    assert len(config_paths) == number_of_replicates
    true_val_paths = glob.glob(
        f"{full_prefix}simcoevolity-sim-[0-9]*-true-values.txt"
    )
    assert len(true_val_paths) == number_of_replicates

    sim_infer_config_paths = create_sim_configs(
        sim_config_paths = config_paths,
        inference_config_paths = infer_config_paths,
    )
    true_conf_paths = tuple(
        zip(true_val_paths, sim_infer_config_paths, strict = True))

    for path in config_paths:
        os.remove(path)

    return run_time, true_conf_paths

def collect_prior_samples(
    seeds,
    config_path,
    output_dir,
    number_of_procs = 4,
    eco_exe_dir = None,
    timeout = 300,
    max_num_attempts = 2,
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
                    True,   # ignore_data
                    False,  # relax_constant_sites
                    False,  # relax_missing_sites
                    False,  # relax_triallelic_sites
                    timeout,
                    max_num_attempts,
                )
            )
            for seed in seeds
        ]
        sys.stderr.write(
            f"Loaded {len(workers)} ecoevolity workers for {number_of_procs} processors\n"
        )
        for run_time, num_var_sites, state_log_path in (w.get() for w in workers):
            log_raths.append(state_log_path)
    return log_paths

def run_sumcoevolity(
    config_path,
    input_state_log_paths,
    seed,
    output_dir,
    num_prior_draws = 1000000,
    eco_exe_dir = None,
    burnin = 0,
    extra_returns = [],
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

    nevents_results_path = f"{prefix}sumcoevolity-results-nevents.txt"
    model_results_path = f"{prefix}sumcoevolity-results-model.txt"

    cmd = [
        eco_exe,
        f"--seed={seed}",
        f"--prefix={prefix}",
        f"--config={config_path}",
        f"--number-of-samples={num_prior_draws}",
        f"--burnin={burnin}",
        *input_state_log_paths,
    ]

    if os.path.exists(nevents_results_path):
        raise Exception(
            f"Output results path already exists: '{nevents_results_path}'\n"
        )
    if os.path.exists(model_results_path):
        raise Exception(
            f"Output results path already exists: '{model_results_path}'\n"
        )

    result = run_cmd(cmd)
    return result, nevents_results_path, model_results_path, *extra_returns

def generate_simulations(
    rng,
    sim_config,
    infer_configs,
    output_dir,
    eco_exe_dir = None,
    number_of_sims = 100,
    number_of_procs = 4,
    singleton_sample_prob = None,
    locus_size = None,
    max_one_variable_site_per_locus = False,
    charsets = False,
    relax_constant_sites = False,
    relax_missing_sites = False,
    relax_triallelic_sites = False,
    output_nexus = False,
):
    if number_of_procs > number_of_sims:
        number_of_procs = number_of_sims
    num_sims_per_proc = math.floor(number_of_sims / number_of_procs)
    remainder_sims = number_of_sims - (num_sims_per_proc * number_of_procs)

    num_sims_args = [num_sims_per_proc for _ in range(number_of_procs)]
    num_sims_args[-1] += remainder_sims

    with multiprocessing.Pool(number_of_procs) as pool:
        workers = [
            pool.apply_async(
                run_simcoevolity,
                args = (
                    sim_config,
                    infer_configs,
                    project_utils.get_safe_seed(rng),
                    output_dir,
                    num_reps,
                    eco_exe_dir,
                    singleton_sample_prob,
                    locus_size,
                    max_one_variable_site_per_locus,
                    charsets,
                    relax_constant_sites,
                    relax_missing_sites,
                    relax_triallelic_sites,
                    output_nexus,
                ))
            for num_reps in num_sims_args
        ]
        sys.stderr.write(
            f"Loaded {len(workers)} simcoevolity workers for {number_of_procs} processors\n"
        )
        all_true_config_paths = []
        for run_time, true_val_config_paths in (w.get() for w in workers):
            all_true_config_paths.extend(true_val_config_paths)
    return all_true_config_paths

def run_analyses_on_sims(
    rng,
    true_val_config_paths,
    eco_exe_dir = None,
    number_of_chains = 2,
    number_of_procs = 4,
    relax_constant_sites = False,
    relax_missing_sites = False,
    relax_triallelic_sites = False,
    timeout = None,
    max_num_attempts = 3,
    output_dir = None,
):
    total_num_runs = 0
    for true_vals_path, config_paths in true_val_config_paths:
        total_num_runs += (len(config_paths) * number_of_chains)
    if number_of_procs > total_num_runs:
        number_of_procs = total_num_runs

    if not output_dir:
        output_dir = os.path.dirname(true_val_config_paths[0][0])

    results = {}
    workers = []
    with multiprocessing.Pool(number_of_procs) as pool:
        for true_vals_path, config_paths in true_val_config_paths:
            assert not true_vals_path in results
            results[true_vals_path] = {"analyses": {}}
            for rep_inf_conf_path, orig_inf_conf_path in config_paths:
                assert not orig_inf_conf_path in results[true_vals_path]
                results[true_vals_path]["analyses"][orig_inf_conf_path] = {}
                results[true_vals_path]["analyses"][orig_inf_conf_path]["chains"] = {}
                for i in range(number_of_chains):
                    seed = project_utils.get_safe_seed(rng)
                    assert not seed in results[true_vals_path]["analyses"][orig_inf_conf_path]["chains"]
                    results[true_vals_path]["analyses"][orig_inf_conf_path]["chains"][seed] = {}
                    workers.append(
                        pool.apply_async(
                            run_ecoevolity,
                            args = (
                                rep_inf_conf_path,
                                seed,
                                output_dir,
                                eco_exe_dir,
                                False,  # ignore_data
                                False,  # relax_constant_sites
                                False,  # relax_missing_sites
                                False,  # relax_triallelic_sites
                                timeout,
                                max_num_attempts,
                                (true_vals_path, orig_inf_conf_path, seed), # extra_returns
                            )
                        )
                    )
        sys.stderr.write(
            f"Loaded {len(workers)} ecoevolity workers for {number_of_procs} processors\n"
        )
        num_var_sites = {}
        for run_time, n_var_sites, state_log_path, true_path, conf_path, seed in (w.get() for w in workers):
            if "numbers_of_variable_sites" in results[true_path]:
                assert results[true_path]["numbers_of_variable_sites"] == n_var_sites
            else:
                results[true_path]["numbers_of_variable_sites"] = n_var_sites
            results[true_path]["analyses"][conf_path]["chains"][seed]["run_time"] = run_time
            results[true_path]["analyses"][conf_path]["chains"][seed]["state_log_path"] = state_log_path
    return results

def add_sumcoevolity_to_results(
    rng,
    results,
    eco_exe_dir = None,
    output_dir = None,
    num_prior_draws = 1000000,
    burnin = 0,
    number_of_procs = 4,
):
    if not output_dir:
        output_dir = os.path.dirname(next(iter(results)))

    worker_count = 0
    for true_vals_path, infer_info in results.items():
        worker_count += len(infer_info)
    if number_of_procs > worker_count:
        number_of_procs = worker_count

    nchains = None
    workers = []
    with multiprocessing.Pool(number_of_procs) as pool:
        for true_vals_path, infer_info in results.items():
            for config_path, results_info in infer_info["analyses"].items():
                state_log_paths = [results_info["chains"][seed]["state_log_path"] for seed in results_info["chains"]]
                if nchains is None:
                    nchains = len(state_log_paths)
                else:
                    assert nchains == len(state_log_paths)
                seed = project_utils.get_safe_seed(rng)
                extra_returns = (true_vals_path, config_path, seed)
                workers.append(
                    pool.apply_async(
                        run_sumcoevolity,
                        args = (
                            config_path,
                            state_log_paths,
                            seed,
                            output_dir,
                            num_prior_draws,
                            eco_exe_dir,
                            burnin,
                            extra_returns,
                        )
                    )
                )
        sys.stderr.write(
            f"Loaded {len(workers)} sumcoevolity workers for {number_of_procs} processors\n"
        )
        for res, nevents_results_path, model_results_path, true_vals_path, config_path, seed in (w.get() for w in workers):
            assert true_vals_path in results
            assert config_path in results[true_vals_path]["analyses"]
            results[true_vals_path]["analyses"][config_path]["sumcoevolity"] = {}
            results[true_vals_path]["analyses"][config_path]["sumcoevolity"]["seed"] = seed
            results[true_vals_path]["analyses"][config_path]["sumcoevolity"]["nevents_summary_path"] = nevents_results_path
            results[true_vals_path]["analyses"][config_path]["sumcoevolity"]["model_summary_path"] = model_results_path
