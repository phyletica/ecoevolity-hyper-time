#!/usr/bin/env python

import os
import sys
import random
import argparse
import copy
import json

import pycoevolity

import project_utils
import interop
import eco_config
import plotting


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
        '-p', '--number-of-procs',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_nonnegative_int,
        default = 4,
        help = (
            'The number of processors to use to generate and analyze '
            'simulations.'
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

    args = parser.parse_args()
    return args

def process_output_dir_arg(output_dir):
    if not output_dir:
        output_dir = os.curdir
    else:
        if not os.path.exists(output_dir):
            try:
                os.mkdir(output_dir)
            except Exception as e:
                sys.stderr.write(
                    f"ERROR: Could not create output directory '{output_dir}'\n"
                )
                raise e
    return output_dir

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

def main_cli():
    args = parse_cli_args()

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
            results = interop.load_results_json(json_stream)
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
        sim_files_dir = process_output_dir_arg(
            os.path.join(output_dir, "simulation-working-files")
        )
    else:
        if (not args.sim_config) or (not args.config_paths):
            msg = (
                "Simulation and inference configs are required when not "
                "appending to previous results."
            )
            raise Exception(msg)
        args.sim_config = [os.path.abspath(p) for p in args.sim_config]
        args.config_paths = [os.path.abspath(p) for p in args.config_paths]
        output_dir = os.path.abspath(process_output_dir_arg(args.output_dir))
        sim_files_dir = process_output_dir_arg(
            os.path.join(output_dir, "simulation-working-files")
        )
        results_dir = process_output_dir_arg(
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
        trueval_config_paths = interop.generate_simulations(
            rng = rng,
            sim_config = sim_config,
            infer_configs = args.config_paths,
            output_dir = sim_files_dir,
            eco_exe_dir = args.ecoevolity_dir,
            number_of_sims = args.number_of_sims,
            number_of_procs = args.number_of_procs,
            singleton_sample_prob = None,
            locus_size = None,
            max_one_variable_site_per_locus = False,
            charsets = False,
            relax_constant_sites = False,
            relax_missing_sites = False,
            relax_triallelic_sites = False,
            output_nexus = False,
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
        interop.add_sumcoevolity_to_results(
            rng = rng,
            results = tmp_results[rel_sim_config],
            eco_exe_dir = args.ecoevolity_dir,
            output_dir = sim_files_dir,
            num_prior_draws = args.number_of_prior_draws,
            burnin = args.burnin,
            number_of_procs = args.number_of_procs,
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
    with open(json_path, 'w') as out_stream:
        json.dump(results, out_stream, indent=4)

if __name__ == "__main__":
    main_cli()
