#!/usr/bin/env python

import sys
import os
import zipfile
import tempfile
import yaml
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import numpy as np
import scipy.stats as st
import pandas as pd

import pycoevolity


def get_posterior_from_zip(zip_path, state_log_suffix, burnin):
    with tempfile.TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(zip_path, 'r') as zip_archive:
            state_logs = [
                f for f in zip_archive.namelist() if f.endswith(state_log_suffix)
            ]
            zip_archive.extractall(path = tmp_dir, members = state_logs)
            state_log_paths = [os.path.join(tmp_dir, l) for l in state_logs]
            return pycoevolity.posterior.PosteriorSample(
                paths = state_log_paths,
                burnin = burnin,
            )

def ax_plot_kde(
    ax,
    values,
    x_buffer = 0.05,
):
    pdf = st.gaussian_kde(values)
    min_x = min(values)
    max_x = max(values)
    x_buffer = (max_x - min_x) * x_buffer
    x = np.linspace(min_x - x_buffer, max_x + x_buffer, 100)
    dens = pdf(x)
    return ax.plot(x, dens)

def ax_compare_samples_to_pdf(
    ax,
    samples,
    prob_dist,
    xlabel = "Value",
    rug_linewidth = 1.1,
    rug_alpha = 0.8,
):
    if hasattr(prob_dist, "ppf"):
        model_x = np.linspace(prob_dist.ppf(0.001), prob_dist.ppf(0.999), 100)
        model_dens = prob_dist.pdf(model_x)
        model_line, = ax.plot(model_x, model_dens)
    else:
        model_line, = ax_plot_kde(
            ax = ax,
            values = prob_dist,
            x_buffer = 0.05,
        )
    plt.setp(model_line,
            color = "C0",
            alpha = 1.0,
            linestyle = '-',
            # linewidth = 1.0,
            marker = '',
            label = "Prior",
            zorder = 200)
    sample_line, = ax_plot_kde(
        ax = ax,
        values = samples,
        x_buffer = 0.05,
    )
    plt.setp(sample_line,
            color = "C1",
            alpha = 1.0,
            linestyle = '-',
            # linewidth = 1.0,
            marker = '',
            label = "Posterior",
            zorder = 300)
    min_y, max_y = ax.get_ylim()
    rug_y_step = abs(max_y - min_y) * 0.035
    rug_y = -rug_y_step
    rug, = ax.plot(samples, [rug_y for _ in samples])
    plt.setp(rug,
            marker = '|',
            linestyle = '',
            markerfacecolor = "C1",
            markeredgecolor = "C1",
            markeredgewidth = rug_linewidth,
            alpha = rug_alpha,
            zorder = 100,
            label = "MCMC sample",
            rasterized = True)
    ax.set(
        xlabel = xlabel,
        ylabel = "Density",
    )
    ax.legend(loc = "upper right")
    return model_line, sample_line, rug

def process_time_prior_parameter(
    config_path,
    posterior_samples,
):
    config = pycoevolity.fileio.load_yaml(config_path)
    event_time_prior = config["event_time_prior"]
    assert len(event_time_prior) == 1
    event_time_prior_name = list(event_time_prior.keys())[0]
    event_time_prior_parameters = event_time_prior[event_time_prior_name]
    assert len(event_time_prior_parameters) == 1
    parameter_name = list(event_time_prior_parameters.keys())[0]
    parameter_settings = event_time_prior_parameters[parameter_name]
    if not pycoevolity.ecoevolity_config.parameter_is_estimated(parameter_settings):
        raise Exception(
            f"{parameter_name} is not estimated; nothing to plot: {config_path}"
        )
    prior_distribution = pycoevolity.ecoevolity_config.get_fixed_distribution(
        parameter_settings["prior"])
    fig = matplotlib.figure.Figure()
    gs = fig.add_gridspec(
        nrows = 1, ncols = 1,
        wspace = 0.0,
        hspace = 0.0,
    )
    ax = fig.add_subplot(gs[0, 0])
    prior_line, post_line, post_samples = ax_compare_samples_to_pdf(
        ax = ax,
        samples = posterior_samples,
        prob_dist = prior_distribution,
        xlabel = f"Divergence time prior {parameter_name}",
    )
    fig.tight_layout()
    return fig, ax, prior_line, post_line, post_samples

def main():
    sns.set_theme(
        context = 'notebook',
        style = 'ticks',
        palette = 'colorblind', 
        font = 'sans-serif',
        font_scale = 1.0,
    )

    plot_extensions = ("svg", "pdf")

    script_dir = os.path.dirname(os.path.realpath(__file__))
    project_dir = os.path.dirname(os.path.dirname(script_dir))
    config_dir = os.path.join(
        project_dir,
        'ecoevolity-configs',
    )
    output_dir = os.path.join(
        project_dir,
        'gecko-ecoevolity-output',
    )

    zip_config_tups = (
        (
            os.path.join(output_dir, 'state-logfiles-geckos.zip'),
            'geckos-combined-hyper-time',
        ),
        (
            os.path.join(output_dir, 'state-logfiles-geckos-conc11.zip'),
            'geckos-combined-hyper-time-conc11',
        ),
    )

    parameter_key = 'time_prior_parameter_0'
    burnin = 101
    for zip_path, config_name in zip_config_tups:
        for plot_ext in plot_extensions:
            config_path = os.path.join(config_dir, f"{config_name}.yml")
            plot_path = os.path.join(output_dir, f"{config_name}-time-prior-mean.{plot_ext}")
            state_log_suffix = f"{config_name}-state-run-1.log"
            posterior = get_posterior_from_zip(
                zip_path = zip_path,
                state_log_suffix = state_log_suffix,
                burnin = burnin)
            parameter_samples = posterior.parameter_samples[parameter_key]
            fig, ax, prior_line, post_line, post_rug = process_time_prior_parameter(
                config_path = config_path,
                posterior_samples = parameter_samples,
            )
            fig.savefig(plot_path, bbox_inches = "tight")
            plt.close(fig)


if __name__ == '__main__':
    main()
