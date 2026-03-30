#!/usr/bin/env python

import os
import sys
import random
import argparse
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
        nargs = "+",
        help = (
            'Paths to ecoevolity configuration files to use to analyze each '
            'simulated data set.'
        ),
    )
    parser.add_argument(
        '-c', '--sim-config',
        action = 'store',
        required = True,
        type = pycoevolity.argparse_utils.arg_is_file,
        help = (
            'Path to the ecoevolity configuratino file to use to simulate '
            'data sets from the prior.'
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
        '-o', '--output-dir',
        action = 'store',
        type = pycoevolity.argparse_utils.arg_is_dir,
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

def main_cli():
    args = parse_cli_args()

    output_dir = process_output_dir_arg(args.output_dir)

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

    trueval_config_paths = interop.generate_simulations(
        rng = rng,
        sim_config = args.sim_config,
        infer_configs = args.config_paths,
        output_dir = output_dir,
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
    results = interop.run_analyses_on_sims(
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
    )

    with open('results.json', 'w') as out_stream:
        json.dump(results, out_stream, indent=4)

if __name__ == "__main__":
    main_cli()
