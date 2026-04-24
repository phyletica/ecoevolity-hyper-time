#!/usr/bin/env python

import os
import sys
import random
import argparse
import tempfile
import scipy.stats as st
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

import pycoevolity

import project_utils
import interop
import eco_config
import plotting


def plot_cdf_comparison(
    prior_settings,
    posterior_samples,
    numpy_rng,
):
    if eco_config.distribution_is_fixed(prior_settings):
        prior_distribution = eco_config.get_fixed_distribution(prior_settings)
    else:
        prior_distribution = eco_config.sample_distribution(
            numpy_rng = numpy_rng,
            prior_settings = prior_settings,
            n = 100000,
        )
    fig = matplotlib.figure.Figure()
    gs = fig.add_gridspec(
        nrows = 1, ncols = 1,
        wspace = 0.0,
        hspace = 0.0,
    )
    ax = fig.add_subplot(gs[0, 0])
    empirical_line, model_line = plotting.compare_samples_to_cdf(
        ax = ax,
        samples = posterior_samples,
        prob_dist = prior_distribution,
        include_ks_test = True,
    )
    fig.tight_layout()
    return fig, ax, empirical_line, model_line

def plot_qq(
    prior_settings,
    posterior_samples,
    numpy_rng,
):
    if eco_config.distribution_is_fixed(prior_settings):
        prior_distribution = eco_config.get_fixed_distribution(prior_settings)
    else:
        prior_distribution = eco_config.sample_distribution(
            numpy_rng = numpy_rng,
            prior_settings = prior_settings,
            n = 100000,
        )
    fig = matplotlib.figure.Figure()
    gs = fig.add_gridspec(nrows = 1, ncols = 1,
            wspace = 0.0,
            hspace = 0.0)
    ax = fig.add_subplot(gs[0, 0])
    qline = plotting.qq(
        ax = ax,
        samples = posterior_samples,
        prob_dist = prior_distribution,
    )
    fig.tight_layout()
    return fig, ax, qline

def process_parameter(
    parameter_name,
    parameter_settings,
    posterior_samples,
    output_prefix,
    numpy_rng,
):
    if not eco_config.parameter_is_estimated(parameter_settings):
        is_valid, expected_val, val = eco_config.fixed_param_values_are_valid(
            parameter_settings,
            posterior_samples,
        )
        if not is_valid:
            raise Exception(
                f"{parameter_name} should be fixed at {expected_val} "
                "but sampled {val}\n"
            )
    else:
        plot_path = f"{output_prefix}prior-cdf-comparison-{parameter_name}.svg"
        fig, ax, eline, mline = plot_cdf_comparison(
            prior_settings = parameter_settings["prior"],
            posterior_samples = posterior_samples,
            numpy_rng = numpy_rng,
        )
        ax.set(xlabel = f"{parameter_name}")
        fig.savefig(plot_path, bbox_inches = "tight")
        plt.close(fig)
    
        plot_path = f"{output_prefix}prior-qq-plot-{parameter_name}.svg"
        fig, ax, qline = plot_qq(
            prior_settings = parameter_settings["prior"],
            posterior_samples = posterior_samples,
            numpy_rng = numpy_rng,
        )
        ax.set(title = f"{parameter_name}")
        fig.savefig(plot_path, bbox_inches = "tight")
        plt.close(fig)

def process_event_model_prior(
    settings,
    nevent_samples,
    number_of_comparisons,
    output_prefix,
    numpy_rng,
):
    assert len(settings) == 1
    model_prior_name = list(settings.keys())[0]
    if model_prior_name == "fixed":
        return
    elif model_prior_name == "pitman_yor_process":
        model_prior_parameters = settings[model_prior_name][
                "parameters"]
        prior_nevent_samples = eco_config.sample_hyper_pitman_yor_distribution(
            numpy_rng = numpy_rng,
            prior_parameters = model_prior_parameters,
            number_of_elements = number_of_comparisons,
            n = 100000,
        )
    elif model_prior_name == "dirichlet_process":
        model_prior_parameters = settings[model_prior_name][
                "parameters"]
        prior_nevent_samples = eco_config.sample_hyper_dirichlet_distribution(
            numpy_rng = numpy_rng,
            prior_parameters = model_prior_parameters,
            number_of_elements = number_of_comparisons,
            n = 100000,
        )
    else:
        raise Exception(
            f"Unsupported event_model_prior: {model_prior_name}"
        )
    plot_path = f"{output_prefix}prior-cmf-comparison-nevents.svg"
    fig = matplotlib.figure.Figure()
    gs = fig.add_gridspec(nrows = 1, ncols = 1,
            wspace = 0.0,
            hspace = 0.0)
    ax = fig.add_subplot(gs[0, 0])
    emp_line, model_line = plotting.compare_nevents_samples_to_cdf(
        ax = ax,
        samples = nevent_samples,
        prior_samples = prior_nevent_samples,
        number_of_comparisons = number_of_comparisons,
        include_ks_test = True,
    )
    fig.tight_layout()
    fig.savefig(plot_path, bbox_inches = "tight")
    plt.close(fig)

def main_cli():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('config_path',
            metavar = 'ECOEVOLITY-CONFIG-PATH',
            type = pycoevolity.argparse_utils.arg_is_file,
            help = ('Path to ecoevolity configuration file to use to sample '
                    'from the prior.'))
    parser.add_argument('-e', '--ecoevolity-dir',
            action = 'store',
            type = pycoevolity.argparse_utils.arg_is_dir,
            help = ('The directory in which ecoevolity\'s programs are '
                    'installed. By default, ecoevolity\'s programs will be ' 
                    'called without a path (i.e., the directory in which '
                    'they are installed need to be in your environment\'s '
                    'PATH variable.'
                   ))
    parser.add_argument('-r', '--number-of-runs',
            action = 'store',
            type = pycoevolity.argparse_utils.arg_is_nonnegative_int,
            default = 10,
            help = ('The number of independent runs for sampling from the '
                    'prior. This will determine the number of samples to be '
                    'collected. The length of the chain and samping frequency '
                    'are defined in the configuration file. The total number '
                    'samples will equal (ignoring burn-in):  '
                    'number of runs x ((chain_length / sample_frequency) - burnin).'
                   ))
    parser.add_argument('-p', '--number-of-procs',
            action = 'store',
            type = pycoevolity.argparse_utils.arg_is_nonnegative_int,
            default = 4,
            help = ('The number of processors to use to run the '
                    '\'-r/--number-of-runs\' ecoevolity runs that sample from '
                    'the prior. The default is smaller of 4 or the number of '
                    'runs.'
                   ))
    parser.add_argument('-b', '--burnin',
            action = 'store',
            type = pycoevolity.argparse_utils.arg_is_nonnegative_int,
            default = 0,
            help = ('The number of samples to remove from the beginning of '
                    'each log file as burn in.'))
    parser.add_argument('-o', '--output-dir',
            action = 'store',
            type = project_utils.arg_is_dir_or_new_dir,
            help = ('The directory in which to put all output files.'))
    parser.add_argument('--seed',
            action = 'store',
            type = pycoevolity.argparse_utils.arg_is_positive_int,
            help = ('Seed for random number generator.'))
    args = parser.parse_args()

    output_dir = args.output_dir
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

    config_name = os.path.splitext(os.path.basename(args.config_path))[0]
    output_prefix = os.path.join(
        output_dir,
        f"{config_name}-",
    )

    seeds = project_utils.get_safe_seeds(rng, n = args.number_of_runs)

    tmp_prefix = "ecoevolity-prior-sampling-"
    with tempfile.TemporaryDirectory(prefix = tmp_prefix) as temp_dir:
        state_log_paths = interop.collect_prior_samples(
            seeds = seeds,
            config_path = args.config_path,
            output_dir = temp_dir,
            number_of_procs = args.number_of_procs,
            eco_exe_dir = eco_exe_dir,
        )
        posterior_sample = pycoevolity.posterior.PosteriorSample(
            paths = state_log_paths,
            burnin = args.burnin,
            include_time_in_coal_units = False,
        )

        result, sumco_nevents_path, sumco_model_path = interop.run_sumcoevolity(
            config_path = args.config_path,
            input_state_log_paths = state_log_paths,
            seed = project_utils.get_safe_seed(rng),
            output_dir = temp_dir,
            num_prior_draws = 1000000,
            eco_exe_dir = eco_exe_dir,
            burnin = args.burnin,
        )
        if not result.returncode == 0:
            raise Exception(
                f"ERROR: sumcoevolity run returned non-zero exit code "
                f"'{result.returncode}'; here is the stderr:\n"
                f"{result.stderr}\n"
            )
        sumco_nevents_table = pycoevolity.posterior.SumcoevolityNeventsTable(
            sumcoevolity_nevents_table_path = sumco_nevents_path,
        )

    config = eco_config.get_yaml_config(args.config_path)
    number_of_comparisons = len(config.get("comparisons"))

    model_prior_settings = config.get("event_model_prior")
    assert len(model_prior_settings) == 1

    process_event_model_prior(
        settings = model_prior_settings,
        nevent_samples = posterior_sample.parameter_samples["number_of_events"],
        number_of_comparisons = number_of_comparisons,
        output_prefix = output_prefix,
        numpy_rng = np_rng,
    )

    model_prior_name = list(model_prior_settings.keys())[0]
    if not model_prior_name == "fixed":
        model_prior_parameters = model_prior_settings[model_prior_name][
                "parameters"]
        for parameter_name, parameter_settings in model_prior_parameters.items():
            values = posterior_sample.parameter_samples[parameter_name]
            process_parameter(
                parameter_name = parameter_name,
                parameter_settings = parameter_settings,
                posterior_samples = values,
                output_prefix = output_prefix,
                numpy_rng = np_rng,
            )

    event_time_prior = config["event_time_prior"]
    event_time_settings = {
        "estimate" : True,
        "prior" : event_time_prior,
    }

    height_keys = list(posterior_sample.get_height_keys())
    # Vet div times for first and last comparison
    height_keys_to_plot = [height_keys[0], height_keys[-1]]
    for height_key in height_keys_to_plot:
        values = posterior_sample.parameter_samples[height_key]
        process_parameter(
            parameter_name = height_key,
            parameter_settings = event_time_settings,
            posterior_samples = values,
            output_prefix = output_prefix,
            numpy_rng = np_rng,
        )

    leaf_population_size_settings = config[
        "global_comparison_settings"][
            "parameters"][
                "population_size"]

    leaf_pop_size_keys = list(posterior_sample.get_descendant_pop_size_keys())
    # Vet population sizes for first and last leaf population
    leaf_pop_sizes_to_plot = [leaf_pop_size_keys[0], leaf_pop_size_keys[-1]]
    for leaf_pop_size_key in leaf_pop_sizes_to_plot:
        values = posterior_sample.parameter_samples[leaf_pop_size_key]
        process_parameter(
            parameter_name = leaf_pop_size_key,
            parameter_settings = leaf_population_size_settings,
            posterior_samples = values,
            output_prefix = output_prefix,
            numpy_rng = np_rng,
        )

    # Make sure pop sizes (the root size and two leaves) are constrained to be
    # equal for each comparison
    equal_pop_sizes = config[
        "global_comparison_settings"][
            "equal_population_sizes"]
    if not equal_pop_sizes:
        raise Exception("Population sizes not constrained to be equal")

    leaf_sizes = posterior_sample.parameter_samples[
        posterior_sample.get_descendant_pop_size_keys()[0]
    ]
    root_sizes = posterior_sample.parameter_samples[
        posterior_sample.get_ancestral_pop_size_keys()[0]
    ]
    assert len(leaf_sizes) == len(root_sizes)
    for i in range(len(leaf_sizes)):
        if not project_utils.almost_equal(
            leaf_sizes[i],
            root_sizes[i],
        ):
            msg = (
                f"Unequal leaf and root pop sizes for first comparison: "
                f"{leaf_sizes[i]}, {root_sizes[i]}\n"
            )
            raise Exception(msg)


if __name__ == "__main__":
    sns.set_theme(context = "talk", style = "ticks", palette = "colorblind")

    main_cli()
