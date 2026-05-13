#!/usr/bin/env python

import os
import sys
import random
import argparse
import copy
import json
import re
import math
import multiprocessing
import operator
from collections import OrderedDict
import gzip
import pandas as pd
import seaborn as sns
import yaml

import pycoevolity

import project_utils
import interop
import eco_config
import plotting


def get_result_path(rel_path, results_dir):
    return os.path.abspath(os.path.join(results_dir, rel_path))

def parse_true_values(true_values_path):
    true_values = pycoevolity.parsing.get_dict_from_spreadsheets(
        [true_values_path],
        sep = "\t",
        header = None,
    )
    for v in true_values.values():
        assert len(v) == 1
    return true_values

def parse_sim_rep_results(
    sim_id,
    sim_config_name,
    inference_config_name,
    true_values,
    state_log_paths,
    run_times,
    parameter_names,
    numbers_of_variable_sites = None,
    include_time_in_coal_units = True,
    burnin = 0,
    config_labels = None,
):
    assert len(run_times) == len(state_log_paths)
    if not config_labels:
        config_labels = {
            sim_config_name : sim_config_name,
            inference_config_name : inference_config_name,
        }
    nchains = len(state_log_paths)
    post_sample = pycoevolity.posterior.PosteriorSample(
        state_log_paths,
        burnin = burnin,
        include_time_in_coal_units = include_time_in_coal_units,
    )
    results = {
        'simulation_id': sim_id,
        'simulation_config' : config_labels.get(
            sim_config_name, sim_config_name),
        'inference_config': config_labels.get(
            inference_config_name, inference_config_name),
        'mean_run_time' : sum(run_times) / len(run_times),
        'median_run_time' : pycoevolity.stats.median(run_times),
        'min_run_time' : min(run_times),
        'sample_size' : post_sample.number_of_samples,
    }

    assert post_sample.number_of_samples % nchains == 0
    nsamples_per_chain = post_sample.number_of_samples // nchains

    if include_time_in_coal_units:
        for label in post_sample.height_labels:
            ht_key = "root_height_{0}".format(label)
            sz_key = "pop_size_{0}".format(label)
            t = float(true_values[ht_key][0])
            n = float(true_values[sz_key][0])
            t_coal = t / (2.0 * n)
            coal_key = "coal_root_height_{0}".format(label)
            true_values[coal_key] = [t_coal]

    if numbers_of_variable_sites:
        assert len(numbers_of_variable_sites) == post_sample.number_of_comparisons
        for i, n_var_sites in enumerate(numbers_of_variable_sites):
            results[f"n_var_sites_{post_sample.height_labels[i]}"] = n_var_sites
    
    true_model = tuple(int(true_values[h][0]) for h in post_sample.height_index_keys)
    true_model_p = post_sample.get_model_probability(true_model)
    true_model_cred = post_sample.get_model_credibility_level(true_model)
    map_models = post_sample.get_map_models()
    map_model = map_models[0]
    if len(map_models) > 1:
        if true_model in map_models:
            map_model = true_model
    map_model_p = post_sample.get_model_probability(map_model)
    results["true_model"] = ",".join((str(i) for i in true_model))
    results["map_model"] = ",".join((str(i) for i in map_model))
    results["true_model_cred_level"] = true_model_cred
    results["map_model_p"] = map_model_p
    results["true_model_p"] = true_model_p
    model_dist_summary = pycoevolity.stats.get_summary(
        post_sample.distances_from(true_model))
    results["mean_model_distance"] = model_dist_summary["mean"]
    results["median_model_distance"] = model_dist_summary["median"]
    results["std_dev_model_distance"] = math.sqrt(model_dist_summary["variance"])
    results["hpdi_95_lower_model_distance"] = model_dist_summary["hpdi_95"][0]
    results["hpdi_95_upper_model_distance"] = model_dist_summary["hpdi_95"][1]
    results["eti_95_lower_model_distance"] = model_dist_summary["qi_95"][0]
    results["eti_95_upper_model_distance"] = model_dist_summary["qi_95"][1]
    map_model_distances = post_sample.get_map_model_distances_from(true_model)
    if len(map_model_distances) > 1:
        map_model_dist_summary = pycoevolity.stats.get_summary(
                map_model_distances)
        results["mean_map_model_distance"] = map_model_dist_summary["mean"]
        results["median_map_model_distance"] = map_model_dist_summary["median"]
    else:
        results["mean_map_model_distance"] = map_model_distances[0]
        results["median_map_model_distance"] = map_model_distances[0]
    
    true_nevents = int(true_values["number_of_events"][0])
    true_nevents_p = post_sample.get_number_of_events_probability(true_nevents)
    true_nevents_cred = post_sample.get_number_of_events_credibility_level(true_nevents)
    map_numbers_of_events = post_sample.get_map_numbers_of_events()
    map_nevents = map_numbers_of_events[0]
    if len(map_numbers_of_events) > 1:
        if true_nevents in map_numbers_of_events:
            map_nevents = true_nevents
    map_nevents_p = post_sample.get_number_of_events_probability(map_nevents)
    results["true_num_events"] = true_nevents
    results["map_num_events"] = map_nevents
    results["true_num_events_cred_level"] = true_nevents_cred
    results["map_num_events_p"] = map_nevents_p
    results["true_num_events_p"] = true_nevents_p
    nevents_cred_set = []
    cum_prob = 0.0
    for n, p in post_sample.get_numbers_of_events():
        nevents_cred_set.append(n)
        cum_prob += p
        if cum_prob > 0.95:
            break
    hpdi_lower_nevents = min(nevents_cred_set)
    hpdi_upper_nevents = max(nevents_cred_set)
    results["hpdi_95_lower_num_events"] = hpdi_lower_nevents
    results["hpdi_95_upper_num_events"] = hpdi_upper_nevents
    results["map_num_events_distance"] = map_nevents - true_nevents
    results["hpdi_95_lower_num_events_distance"] = hpdi_lower_nevents - true_nevents
    results["hpdi_95_upper_num_events_distance"] = hpdi_upper_nevents - true_nevents
    
    sum_of_abs_mean_error_root_height = 0.0
    sum_of_abs_mean_error_pop_size_root = 0.0
    for parameter in parameter_names:
        true_val = None
        true_val_rank = None
        post_mean = None
        post_median = None
        post_stdev = None
        hpdi_lower = None
        hpdi_upper = None
        eti_lower = None
        eti_upper = None
        ess = None
        ess_sum = None
        psrf = None
        have_true_val = bool(parameter in true_values)
        have_post = bool(parameter in post_sample.parameter_samples)
        if have_true_val:
            true_val = float(true_values[parameter][0])
        if have_post:
            if have_true_val:
                true_val_rank = post_sample.get_rank(parameter, true_val)
            ss = pycoevolity.stats.get_summary(
                    post_sample.parameter_samples[parameter])
            if parameter in post_sample.get_height_keys():
                sum_of_abs_mean_error_root_height += math.fabs(
                    true_val - ss["mean"])
            elif parameter in post_sample.get_ancestral_pop_size_keys():
                sum_of_abs_mean_error_pop_size_root += math.fabs(
                    true_val - ss["mean"])
            ess = pycoevolity.stats.effective_sample_size(
                    post_sample.parameter_samples[parameter])
            ess_sum = 0.0
            samples_by_chain = []
            for i in range(nchains):
                chain_samples = post_sample.parameter_samples[parameter][
                        i * nsamples_per_chain : (i + 1) * nsamples_per_chain]
                assert(len(chain_samples) == nsamples_per_chain)
                ess_sum += pycoevolity.stats.effective_sample_size(chain_samples)
                if nchains > 1:
                    samples_by_chain.append(chain_samples)
            if nchains > 1:
                psrf = pycoevolity.stats.potential_scale_reduction_factor(samples_by_chain)
            post_mean = ss["mean"]
            post_median = ss["median"]
            post_stdev = math.sqrt(ss["variance"])
            hpdi_lower = ss["hpdi_95"][0]
            hpdi_upper = ss["hpdi_95"][1]
            eti_lower = ss["qi_95"][0]
            eti_upper = ss["qi_95"][1]
        if nchains > 1:
            results["psrf_{0}".format(parameter)] = psrf
        results["true_{0}".format(parameter)] = true_val
        results["true_{0}_rank".format(parameter)] = true_val_rank
        results["mean_{0}".format(parameter)] = post_mean
        results["median_{0}".format(parameter)] = post_median
        results["stddev_{0}".format(parameter)] = post_stdev
        results["hpdi_95_lower_{0}".format(parameter)] = hpdi_lower
        results["hpdi_95_upper_{0}".format(parameter)] = hpdi_upper
        results["eti_95_lower_{0}".format(parameter)] = eti_lower
        results["eti_95_upper_{0}".format(parameter)] = eti_upper
        results["ess_{0}".format(parameter)] = ess
        results["ess_sum_{0}".format(parameter)] = ess_sum
    results["sum_of_abs_mean_error_root_height"] = sum_of_abs_mean_error_root_height
    results["sum_of_abs_mean_error_pop_size_root"] = sum_of_abs_mean_error_pop_size_root
    return results

def get_free_parameter_labels(
    analyses_dict,
    results_dir,
    include_time_in_coal_units = True,
):
    parameters = set()
    time_parameters = None
    for analysis_config, analysis_results in analyses_dict.items():
        chains = analysis_results["chains"]
        log_paths = [chains[seed]["state_log_path"] for seed in chains]
        log_paths = [get_result_path(p, results_dir) for p in log_paths]
        post_sample = pycoevolity.posterior.PosteriorSample(
            log_paths,
            burnin = 1,
            include_time_in_coal_units = include_time_in_coal_units,
        )
        time_params = sorted(post_sample.get_height_keys())
        if not time_parameters:
            time_parameters = time_params
            parameters.update(time_params)
        else:
            if time_params != time_parameters:
                raise Exception(
                    "Time (root_height) parameters do not match among analysis "
                    "outputs from different configs."
                )
        for comp_idx in range(post_sample.number_of_comparisons):
            tip_labels = post_sample.tip_labels[comp_idx]
            comp_label = post_sample.height_labels[comp_idx]
            tip_pop_size_keys = [f"pop_size_{l}" for l in tip_labels]
            anc_pop_size_key = f"pop_size_root_{comp_label}"
            tip_pop_sizes_last = [post_sample.parameter_samples[k][-1] for k in tip_pop_size_keys]
            anc_pop_size_last = post_sample.parameter_samples[anc_pop_size_key][-1]
            anc_pop_size_first = post_sample.parameter_samples[anc_pop_size_key][0]
            pop_sizes_constrained = math.isclose(
                anc_pop_size_last - tip_pop_sizes_last[0], 0.0, abs_tol=1e-10)
            anc_pop_size_fixed = math.isclose(
                anc_pop_size_last - anc_pop_size_first, 0.0, abs_tol=1e-10)
            if not anc_pop_size_fixed:
                parameters.add(anc_pop_size_key)
            if not pop_sizes_constrained:
                tip_pop_sizes_first = [post_sample.parameter_samples[k][0] for k in tip_pop_size_keys]
                tip_size_0_fixed = math.isclose(
                    tip_pop_sizes_last[0] - tip_pop_sizes_first[0], 0.0, abs_tol=1e-10)
                tip_size_1_fixed = math.isclose(
                    tip_pop_sizes_last[1] - tip_pop_sizes_first[1], 0.0, abs_tol=1e-10)
                if not tip_size_0_fixed:
                    parameters.add(tip_pop_size_keys[0])
                if not tip_size_1_fixed:
                    parameters.add(tip_pop_size_keys[1])

        for param in post_sample.parameter_samples.keys():
            if (
                param.startswith("root_height_")
                or param.startswith("pop_size_")
                or (param == "model")
                or (param == "number_of_events")
            ):
                continue
            if not param in parameters:
                first_val = post_sample.parameter_samples[param][0]
                last_val = post_sample.parameter_samples[param][-1]
                param_fixed = math.isclose(
                    first_val - last_val, 0.0, abs_tol = 1e-10)
                if not param_fixed:
                    parameters.add(param)
    return parameters

def file_names_are_unique(file_paths):
    file_names = [os.path.basename(p) for p in file_paths]
    return len(file_names) == len(set(file_names))

def parse_sim_id(true_values_path):
    true_values_file_pattern_str = (
        r"^.*seed-(?P<seed>\d+)-simcoevolity-sim-(?P<sim_num>\d+)-true-values\.txt.*$"
    )
    true_values_file_pattern = re.compile(true_values_file_pattern_str)
    m = true_values_file_pattern.match(true_values_path)
    if not m:
        raise Exception(
            f"Unexpected true values file name: {true_values_path}"
        )
    seed = m.group("seed")
    sim_num = m.group("sim_num")
    return f"{seed}-{sim_num}"

def parse_sim_results(
    results_path,
    config_labels = None,
    include_time_in_coal_units = True,
    number_of_procs = 1,
):
    results_dir = os.path.dirname(results_path)
    with open(results_path, "r") as json_stream:
        results = interop.load_json(json_stream)
    sim_configs = results["simulation_configs"]
    if not file_names_are_unique(sim_configs):
        raise Exception(
            "Simulation config file names are not unique"
        )
    inf_configs = results["inference_configs"]
    if not file_names_are_unique(inf_configs):
        raise Exception(
            "Inference config file names are not unique"
        )
    nchains = results["number_of_chains"]
    burnin = results["burnin"]
    parameter_names = None

    workers = []
    with multiprocessing.Pool(number_of_procs) as pool:
        for sim_conf, sims in results["simulations"].items():
            assert sim_conf in sim_configs
            for true_vals_path, rep_data in sims.items():
                true_vals_path = get_result_path(true_vals_path, results_dir)
                true_values = parse_true_values(true_vals_path)
                numbers_of_variable_sites = rep_data[
                    "numbers_of_variable_sites"]
                sim_id = parse_sim_id(os.path.basename(true_vals_path))
                if not parameter_names:
                    parameter_names = get_free_parameter_labels(
                        rep_data["analyses"],
                        results_dir,
                        include_time_in_coal_units = include_time_in_coal_units,
                    )
                for analysis_conf, analysis_results in rep_data["analyses"].items():
                    assert analysis_conf in inf_configs
                    chains = analysis_results["chains"]
                    assert len(chains) == nchains
                    run_times = [chains[seed]["run_time"] for seed in chains]
                    log_paths = [chains[seed]["state_log_path"] for seed in chains]
                    log_paths = [get_result_path(p, results_dir) for p in log_paths]
                    workers.append(
                        pool.apply_async(
                            parse_sim_rep_results,
                            args = (
                                sim_id,
                                os.path.basename(sim_conf),      # sim_config_name
                                os.path.basename(analysis_conf), # inference_config_name
                                true_values,
                                log_paths,
                                run_times,
                                parameter_names,
                                numbers_of_variable_sites,
                                include_time_in_coal_units,
                                burnin,
                                config_labels,
                            )
                        )
                    )
        num_workers = len(workers)
        sys.stdout.write(
            f"Loaded {num_workers} result parsing workers for {number_of_procs} processors\n"
        )
        reporting_freq = 100
        if num_workers < 500:
            reporting_freq = 10
        results = []
        for i, result_dict in enumerate(w.get() for w in workers):
            results.append(result_dict)
            if (i + 1) % reporting_freq == 0:
                sys.stdout.write(
                    f"{i + 1} of {num_workers} result parsing workers finished\n"
                )
    results.sort(key=operator.itemgetter(
        'simulation_config',
        'simulation_id',
        'inference_config',
    ))
    df = pd.DataFrame(results)
    return df

def parse_cli_args():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        'config_paths',
        metavar = 'ECOEVOLITY-CONFIG-PATH',
        type = pycoevolity.argparse_utils.arg_is_file,
        nargs = "*",
        help = (
            'Paths to ecoevolity configuration files to use to analyze each '
            'simulated data set.'
        ),
    )
    parser.add_argument(
        '-c', '--sim-config',
        action = 'append',
        required = False,
        type = pycoevolity.argparse_utils.arg_is_file,
        help = (
            'Path to the ecoevolity configuration file to use to simulate '
            'data sets from the prior. This option can be used multiple times '
            'if you want to generate simulations under multiple configs.'
        ),
    )
    parser.add_argument(
        '-e', '--ecoevolity-dir',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_dir,
        help = (
            'The directory in which ecoevolity\'s programs are '
            'installed. By default, ecoevolity\'s programs will be ' 
            'called without a path (i.e., the directory in which '
            'they are installed need to be in your environment\'s '
            'PATH variable.'
        ),
    )
    parser.add_argument(
        '-s', '--number-of-sims',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_nonnegative_int,
        default = 100,
        help = (
            'The number of data sets to simulate with simcoevolity.'
        ),
    )
    parser.add_argument(
        '-r', '--number-of-chains',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_nonnegative_int,
        default = 2,
        help = (
            'The number of independent ecoevolity MCMC chains '
            'to run on each siumlated data set.'
        ),
    )
    parser.add_argument(
        '--number-of-sim-procs',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_nonnegative_int,
        default = 1,
        help = (
            'The number of processors to use to generate '
            'simulations with simcoevolity.'
        ),
    )
    parser.add_argument(
        '-p', '--number-of-procs',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_nonnegative_int,
        default = 4,
        help = (
            'The number of processors to use to analyze '
            'simulations with ecoevolity.'
        ),
    )
    parser.add_argument(
        '-b', '--burnin',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_nonnegative_int,
        default = 101,
        help = (
            'The number of samples to remove from the beginning of '
            'each log file as burn in.'
        ),
    )
    parser.add_argument(
        '--number-of-prior-draws',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_nonnegative_int,
        default = 100000,
        help = (
            'The number of prior samples to use when running sumcoevolity.'
        ),
    )
    parser.add_argument(
        '-o', '--output-dir',
        action = 'store',
        type = project_utils.arg_is_dir_or_new_dir,
        help = (
            'The directory in which to put all output files.'
        ),
    )
    parser.add_argument(
        '--seed',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_positive_int,
        help = (
            'Seed for random number generator.'
        ),
    )
    parser.add_argument(
        '-t', '--chain-timeout',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_nonnegative_int,
        default = 86400,
        help = (
            'The timeout (in seconds) for each ecoevolity MCMC chain. '
            'If a chain runs longer than this the subprocess will raise an '
            'error.'
        ),
    )
    parser.add_argument(
        '-a', '--chain-attempts',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_nonnegative_int,
        default = 3,
        help = (
            'The max number of times to try running each ecoevolity MCMC '
            'chain.'
        ),
    )
    parser.add_argument(
        '--append-to',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_file,
        help = (
            'Path to results file to which to append more simulations. '
            'When this option is used, the only other options that are used '
            'are: '
            '--seed, '
            '-e | --ecoevolity-dir, '
            '-s | --number-of-sims, '
            '-p | --number-of-procs, '
            '-t | --chain-timeout, '
            'and '
            '-a | --chain-attempts. '
            'All other arguments will be ignored.'
        ),
    )
    parser.add_argument(
        '-l', '--config-label-file',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_file,
        help = (
            'Path to YAML-formatted file that maps config file names to labels '
            'to use in their place for plotting.'
        ),
    )
    parser.add_argument(
        '--skip-sims',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_file,
        help = (
            'Skip simulations and parse and plot results from file.'
        ),
    )
    parser.add_argument(
        '--plot-only',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_file,
        help = (
            'Skip to plotting results.'
        ),
    )

    args = parser.parse_args()
    return args

def package_results(results_dict, results_dir, relative_to_dir = None):
    new_results = {}
    for true_vals_path in results_dict:
        gz_true_vals_path = interop.compress_output_path(true_vals_path, results_dir)
        if relative_to_dir:
            gz_true_vals_path = os.path.relpath(gz_true_vals_path, relative_to_dir)
        new_results[gz_true_vals_path] = {
            "analyses": {},
            "numbers_of_variable_sites": copy.deepcopy(
                results_dict[true_vals_path]["numbers_of_variable_sites"]
            ),
        }
        for config_path in results_dict[true_vals_path]["analyses"]:
            results_info = copy.deepcopy(results_dict[true_vals_path]["analyses"][config_path])
            if relative_to_dir:
                config_path = os.path.relpath(config_path, relative_to_dir)
            new_results[gz_true_vals_path]["analyses"][config_path] = results_info
            nevents_sum_path = results_info["sumcoevolity"]["nevents_summary_path"]
            gz_nevents_path = interop.compress_output_path(nevents_sum_path, results_dir)
            if relative_to_dir:
                gz_nevents_path = os.path.relpath(gz_nevents_path, relative_to_dir)
            results_info["sumcoevolity"]["nevents_summary_path"] = gz_nevents_path
            model_sum_path = results_info["sumcoevolity"]["model_summary_path"]
            gz_model_path = interop.compress_output_path(model_sum_path, results_dir)
            if relative_to_dir:
                gz_model_path = os.path.relpath(gz_model_path, relative_to_dir)
            results_info["sumcoevolity"]["model_summary_path"] = gz_model_path
            for seed, chain_info in results_info["chains"].items():
                state_log_path = chain_info["state_log_path"]
                gz_state_log_path = interop.compress_output_path(state_log_path, results_dir)
                if relative_to_dir:
                    gz_state_log_path = os.path.relpath(gz_state_log_path, relative_to_dir)
                chain_info["state_log_path"] = gz_state_log_path
    return new_results

def append_results(previous_results, new_results):
    for sim_config, sim_reps in new_results.items():
        for true_vals_path, infer_info in sim_reps.items():
            assert not true_vals_path in previous_results["simulations"][sim_config]
            previous_results["simulations"][sim_config][true_vals_path] = infer_info

def parse_config_label_yaml(path):
    with open(path, "r") as in_stream:
        d = yaml.safe_load(in_stream)
    is_valid = all(isinstance(k, str) and isinstance(v, str) for k, v in d.items())
    if not is_valid:
        raise Exception(
            f"Yaml file '{path}' is not a simple map of file names to labels"
        )
    for k in d.keys():
        if k != os.path.basename(k):
            raise Exception(
                f"Keys in config label yaml file should be file names (not paths): {k}"
            )
    # Hack to preserve order of config names
    kv_pattern = re.compile(
        r"(?P<key>[^:,{}=]+)\s*:\s*(?P<value>[^:,{}=]+)"
    )
    ordered_keys = []
    with open(path, "r") as in_stream:
        for line in in_stream:
            for match in kv_pattern.finditer(line):
                key = match.group("key").strip()
                ordered_keys.append(key)
    if set(ordered_keys) != set(d.keys()):
        raise Exception(
            "Problem parsing config names from YAML file"
        )
    od = OrderedDict()
    for k in ordered_keys:
        od[k] = d[k]
    return od

def main_cli():
    args = parse_cli_args()

    if args.skip_sims and (not args.plot_only):
        config_labels = None
        if args.config_label_file:
            config_labels = parse_config_label_yaml(args.config_label_file)
        df = parse_sim_results(
            results_path = args.skip_sims,
            config_labels = config_labels,
            include_time_in_coal_units = True,
            number_of_procs = args.number_of_procs,
        )
        summary_path = os.path.join(
            os.path.dirname(args.skip_sims),
            "results-summary.tsv.gz",
        )
        df.to_csv(
            summary_path,
            sep = "\t",
            compression = "gzip",
            index = False,
        )
        return
    
    if args.plot_only:
        df = pd.read_csv(
            args.plot_only,
            sep = "\t",
        )
        config_labels = None
        ordered_labels = None
        if args.config_label_file:
            config_labels = parse_config_label_yaml(args.config_label_file)
            ordered_labels = [v for k, v in config_labels.items()]
        grid = plotting.plot_nevents_heatmap_grid(
            df,
            sim_config_col = "simulation_config",
            inference_config_col = "inference_config",
            ordered_labels = ordered_labels,
            height = 6.5,
            annotate_counts = False,
            include_cbar = True,
            outline_identity = True,
            annotate_stats = True,
            cred_level = 0.95,
        )
        plot_path = os.path.join(
            os.path.dirname(args.plot_only),
            "nevents-heatmap-grid.pdf",
        )
        grid.savefig(plot_path)
        grid = plotting.process_error_scatter_grid(
            df,
            parameters = ["concentration"],
            parameter_root = None,
            use_mean = True,
            use_hpdi = True,
            xlabel = "True concentration",
            ylabel = "Mean concentration",
            ess_min = 200,
            psrf_max = 1.2,
            bad_sampling_color = "C1",
            ordered_labels = ordered_labels,
            height = 6.5,
            annotate_stats = True,
            stat_label = r"\alpha",
            annot_x_position = 0.02,
            annot_y_position = 0.98,
            cred_level = 0.95,
        )
        plot_path = os.path.join(
            os.path.dirname(args.plot_only),
            "concentration-scatter-grid.pdf",
        )
        grid.savefig(plot_path)

        parameter_root = "root_height"
        parameters = plotting.get_all_parameters(
            parameter_prefix = parameter_root,
            column_headers = df.columns,
        )
        grid = plotting.process_error_scatter_grid(
            df,
            # parameters = parameters,
            # parameter_root = parameter_root,
            # parameters = ["root_height_c1sp1"],
            parameters = ["pop_size_root_c1sp1"],
            parameter_root = parameter_root,
            use_mean = True,
            use_hpdi = True,
            xlabel = "True divergence time",
            ylabel = "Mean divergence time",
            ess_min = 200,
            psrf_max = 1.2,
            bad_sampling_color = "C1",
            ordered_labels = ordered_labels,
            height = 6.5,
            annotate_stats = True,
            stat_label = r"\tau",
            annot_x_position = 0.02,
            annot_y_position = 0.98,
            cred_level = 0.95,
        )
        plot_path = os.path.join(
            os.path.dirname(args.plot_only),
            "div-time-scatter-grid.pdf",
        )
        grid.savefig(plot_path)
        return

    eco_exe_dir = interop.get_ecoevolity_dir(
        dir_to_check = args.ecoevolity_dir)

    sys.stdout.write(
        f"Using ecoevolity programs found in '{eco_exe_dir}'\n"
    )

    rng = random.Random()
    seed = args.seed
    if not seed:
        seed = project_utils.get_safe_seed()
    rng.seed(seed)
    np_rng = project_utils.get_numpy_rng(seed)

    results = None
    json_path = None
    json_dir = None
    if args.append_to:
        json_path = args.append_to
        json_dir = os.path.abspath(os.path.dirname(json_path))
        with open(json_path, "r") as json_stream:
            results = interop.load_json(json_stream)
        if seed in results["seeds"]:
            raise Exception(
                f"Seed {seed} was already used; please use a different seed."
            )
        results["seeds"].append(seed)
        args.sim_config = [
            os.path.abspath(
                os.path.join(json_dir, p)
            ) for p in results["simulation_configs"]
        ]
        args.config_paths = [
            os.path.abspath(
                os.path.join(json_dir, p)
            ) for p in results["inference_configs"]
        ]
        args.number_of_chains = results["number_of_chains"]
        args.number_of_prior_draws = results["number_of_prior_draws"]
        args.burnin = results["burnin"]
        output_dir = json_dir
        results_dir = os.path.join(output_dir, "simulation-results-files")
        if not os.path.isdir(results_dir):
            raise Exception(
                f"Unexpected results directory determined from json results "
                f"file: {results_dir}\n"
                "Please don't move a 'results.json' file before appending "
                "simulations to it."
            )
        sim_files_dir = project_utils.process_output_dir_arg(
            os.path.join(output_dir, "simulation-working-files")
        )
    else:
        if (not args.sim_config) or (not args.config_paths):
            msg = (
                "Simulation and inference configs are required when not "
                "appending to previous results."
            )
            raise Exception(msg)
        if not file_names_are_unique(args.sim_config):
            raise Exception(
                "Simulation config file names are not unique"
            )
        if not file_names_are_unique(args.config_paths):
            raise Exception(
                "Inference config file names are not unique"
            )
        args.sim_config = [os.path.abspath(p) for p in args.sim_config]
        args.config_paths = [os.path.abspath(p) for p in args.config_paths]
        output_dir = os.path.abspath(
            project_utils.process_output_dir_arg(args.output_dir))
        sim_files_dir = project_utils.process_output_dir_arg(
            os.path.join(output_dir, "simulation-working-files")
        )
        results_dir = project_utils.process_output_dir_arg(
            os.path.join(output_dir, "simulation-results-files")
        )
        json_path = os.path.join(output_dir, "results.json")
        json_dir = output_dir
        results = { "seeds" : [seed] }
        results["simulation_configs"] = [
            os.path.relpath(p, json_dir) for p in args.sim_config
        ]
        results["inference_configs"] = [
            os.path.relpath(p, json_dir) for p in args.config_paths
        ]
        results["number_of_chains"] = args.number_of_chains
        results["number_of_prior_draws"] = args.number_of_prior_draws
        results["burnin"] = args.burnin

    tmp_results = {}
    for sim_config in args.sim_config:
        rel_sim_config = os.path.relpath(sim_config, json_dir)
        sys.stdout.write(
            f"Generating simulated datasets for '{sim_config}'...\n"
        )
        trueval_config_paths = interop.generate_simulations(
            rng = rng,
            sim_config = sim_config,
            infer_configs = args.config_paths,
            output_dir = sim_files_dir,
            eco_exe_dir = args.ecoevolity_dir,
            number_of_sims = args.number_of_sims,
            number_of_procs = args.number_of_sim_procs,
            singleton_sample_prob = None,
            locus_size = None,
            max_one_variable_site_per_locus = False,
            charsets = False,
            relax_constant_sites = False,
            relax_missing_sites = False,
            relax_triallelic_sites = False,
            output_nexus = False,
        )
        sys.stdout.write(
            f"Starting analyses of simulated datasets for '{sim_config}'...\n"
        )
        tmp_results[rel_sim_config] = interop.run_analyses_on_sims(
            rng = rng,
            true_val_config_paths = trueval_config_paths,
            eco_exe_dir = args.ecoevolity_dir,
            number_of_chains = args.number_of_chains,
            number_of_procs = args.number_of_procs,
            relax_constant_sites = False,
            relax_missing_sites = False,
            relax_triallelic_sites = False,
            timeout = args.chain_timeout,
            max_num_attempts = args.chain_attempts,
            output_dir = sim_files_dir,
        )
        sys.stdout.write(
            f"Running sumcoevolity on results for '{sim_config}'...\n"
        )
        interop.add_sumcoevolity_to_results(
            rng = rng,
            results = tmp_results[rel_sim_config],
            eco_exe_dir = args.ecoevolity_dir,
            output_dir = sim_files_dir,
            num_prior_draws = args.number_of_prior_draws,
            burnin = args.burnin,
            number_of_procs = args.number_of_procs,
        )
        sys.stdout.write(
            f"Packaging results for '{sim_config}'...\n"
        )
        tmp_results[rel_sim_config] = package_results(
            results_dict = tmp_results[rel_sim_config],
            results_dir = results_dir,
            relative_to_dir = json_dir,
        )
    if args.append_to:
        append_results(results, tmp_results)
    else:
        results["simulations"] = tmp_results
    pycoevolity.fileio.write_json(results, json_path, indent = 4)

if __name__ == "__main__":
    sns.set_theme(context = "talk", style = "ticks", palette = "colorblind")

    main_cli()
