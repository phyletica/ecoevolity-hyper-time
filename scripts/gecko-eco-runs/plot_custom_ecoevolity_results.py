#!/usr/bin/env python

import sys
import os
import zipfile
import tempfile
import yaml
import matplotlib.pyplot as plt
import matplotlib
# import seaborn as sns
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

def main():
    # sns.set_theme(
    #     context = 'notebook',
    #     style = 'ticks',
    #     palette = 'colorblind', 
    #     font = 'sans-serif',
    #     font_scale = 1.0,
    # )

    comparison_label_map = {
        "Bohol0"                : "Bohol",
        "CamiguinSur0"          : "Camiguin Sur - C",
        "root-Bohol0"           : "Bohol-Camiguin Sur Root-C",
        "Palawan1"              : "Palawan",
        "Kinabalu1"             : "Borneo - C",
        "root-Palawan1"         : "Palawan-Borneo Root-C",
        "Samar2"                : "Samar",
        "Leyte2"                : "Leyte - C",
        "root-Samar2"           : "Samar-Leyte Root-C",
        "Luzon3"                : "Luzon 1",
        "BabuyanClaro3"         : "Babuyan Claro - C",
        "root-Luzon3"           : "Luzon-Babuyan Claro Root-C",
        "Luzon4"                : "Luzon 2",
        "CamiguinNorte4"        : "Camiguin Norte - C",
        "root-Luzon4"           : "Luzon-Camiguin Norte Root-C",
        "Polillo5"              : "Polillo",
        "Luzon5"                : "Luzon 3 - C",
        "root-Polillo5"         : "Polillo-Luzon Root-C",
        "Panay6"                : "Panay",
        "Negros6"               : "Negros - C",
        "root-Panay6"           : "Panay-Negros Root-C",
        "Sibuyan7"              : "Sibuyan",
        "Tablas7"               : "Tablas - C",
        "root-Sibuyan7"         : "Sibuyan-Tablas Root-C",
        "BabuyanClaro8"         : "Babuyan Claro",
        "Calayan8"              : "Calayan - G",
        "root-BabuyanClaro8"    : "Babuyan Claro-Calayan Root-G",
        "SouthGigante9"         : "S. Gigante",
        "NorthGigante9"         : "N. Gigante - G",
        "root-SouthGigante9"    : "S. Gigante-N. Gigante Root-G",
        "Lubang11"              : "Lubang",
        "Luzon11"               : "Luzon - G",
        "root-Lubang11"         : "Lubang-Luzon Root-G",
        "MaestreDeCampo12"      : "Maestre De Campo",
        "Masbate12"             : "Masbate",
        "root-MaestreDeCampo12" : "Maestre De Campo-Masbate Root",
        "Panay13"               : "Panay 1",
        "Masbate13"             : "Masbate - G",
        "root-Panay13"          : "Panay-Masbate Root-G",
        "Negros14"              : "Negros",
        "Panay14"               : "Panay 2 - G",
        "root-Negros14"         : "Negros-Panay Root-G",
        "Sabtang15"             : "Sabtang",
        "Batan15"               : "Batan - G",
        "root-Sabtang15"        : "Sabtang-Batan Root-G",
        "Romblon16"             : "Romblon",
        "Tablas16"              : "Tablas - G",
        "root-Romblon16"        : "Romblon-Tablas Root-G",
        "CamiguinNorte17"       : "Camiguin Norte",
        "Dalupiri17"            : "Dalupiri - G",
        "root-CamiguinNorte17"  : "Camiguin Norte-Dalupiri Root-G",
    }

    old_timer = "Palawan1"

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
    plot_dir = os.path.join(
        project_dir,
        'docs',
        'images',
    )

    burnin = 101
    config_to_zip = {
        'geckos-combined' : os.path.join(
            output_dir, 'state-logfiles-geckos.zip'),
        'geckos-combined-hyper-time' : os.path.join(
            output_dir, 'state-logfiles-geckos.zip'),
        'geckos-combined-conc11' : os.path.join(
            output_dir, 'state-logfiles-geckos-conc11.zip'),
        'geckos-combined-hyper-time-conc11' : os.path.join(
            output_dir, 'state-logfiles-geckos-conc11.zip'),
    }

    config_to_coords = {
        'geckos-combined' : (0, 0),
        'geckos-combined-hyper-time' : (1, 0),
        'geckos-combined-conc11' : (0, 1),
        'geckos-combined-hyper-time-conc11' : (1, 1),
    }

    config_to_prior_label = {
        'geckos-combined' : r'$\tau \sim \text{Exp}(\text{mean} = 20 \text{mya})$',
        'geckos-combined-hyper-time' : r'$\tau \sim \text{Exp}(\text{mean} \sim \text{Exp}(\text{mean} = 10 \text{mya}))$',
        'geckos-combined-conc11' : r'$\tau \sim \text{Exp}(\text{mean} = 20 \text{mya})$',
        'geckos-combined-hyper-time-conc11' : r'$\tau \sim \text{Exp}(\text{mean} \sim \text{Exp}(\text{mean} = 10 \text{mya}))$',
    }
    config_to_conc_label = {
        'geckos-combined' : r'$\text{DP } \alpha \sim \text{Exp}(\text{mean} = 293)$',
        'geckos-combined-hyper-time' : r'$\text{DP } \alpha \sim \text{Exp}(\text{mean} = 293)$',
        'geckos-combined-conc11' : r'$\text{DP } \alpha \sim \text{Exp}(\text{mean} = 10.84)$',
        'geckos-combined-hyper-time-conc11' : r'$\text{DP } \alpha \sim \text{Exp}(\text{mean} = 10.84)$',
    }

    label_font_size = 14
    bayes_factor_font_size = 6
    posterior_bar_color = "0.3"
    prior_bar_color = "0.85"
    bar_width = 0.45
    full_prob_axis = True
    add_legend = False
    legend_in_plot = True
    col_label_pad = 10
    row_label_x = 1.15
    time_colors = None
    include_map_model = True
    time_x_limits = None
    include_time_zero = True

    nevents_plot_width = 5.5
    nevents_plot_height = nevents_plot_width / 1.618034
    nevents_wspace = 0.25
    nevents_hspace = 0.12

    nevents_fig_width = (
        (2 * nevents_plot_width)
        + (nevents_wspace * nevents_plot_width)
    )
    nevents_fig_height = (
        (2 * nevents_plot_height)
        + (nevents_hspace * nevents_plot_height)
    )

    time_plot_width = 5.5
    time_plot_height = time_plot_width / 1.618034
    time_wspace = 0.63
    time_hspace = 0.12

    time_fig_width = (
        (2 * time_plot_width)
        + (time_wspace * time_plot_width)
    )
    time_fig_height = (
        (2 * time_plot_height)
        + (time_hspace * time_plot_height)
    )
    time_row_label_x = 1.02
    time_label_font_size = 14

    config_to_results = {}
    for config_name, zip_path in config_to_zip.items():
        state_log_suffix = f"{config_name}-state-run-1.log"
        posterior = get_posterior_from_zip(
            zip_path = zip_path,
            state_log_suffix = state_log_suffix,
            burnin = burnin)
        nevents_path = os.path.join(
            output_dir,
            f"sumcoevolity-{config_name}-sumcoevolity-results-nevents.txt",
        )
        nevents = pycoevolity.posterior.SumcoevolityNeventsTable(nevents_path)
        config_to_results[config_name] = {
            'posterior' : posterior,
            'nevents' : nevents,
        }


    # Create grid of nevents plots
    fig = matplotlib.figure.Figure(
        figsize = [nevents_fig_width, nevents_fig_height],
    )
    gs = fig.add_gridspec(
        nrows = 2, ncols = 2,
        wspace = nevents_wspace,
        hspace = nevents_hspace,
    )
    for config_name, results in config_to_results.items():
        col_idx, row_idx = config_to_coords[config_name]
        ax = fig.add_subplot(gs[row_idx, col_idx])
        twin_ax = pycoevolity.plotting.plot_num_events_with_bf(
            ax = ax,
            nevents_table = results['nevents'],
            posterior_color = posterior_bar_color,
            prior_color = prior_bar_color,
            bf_marker = "o",
            bf_markersize = 4,
            bf_markerfacecolor = "none",
            bf_markeredgecolor = "black",
            bf_markeredgewidth = 1.0,
            bf_label = "Bayes factor",
            bar_width = bar_width,
            full_prob_axis = full_prob_axis,
            add_legend = False,
            legend_in_plot = legend_in_plot,
        )
        if row_idx == 0:
            ax.set_title(
                config_to_prior_label[config_name],
                fontsize = label_font_size,
                pad = col_label_pad,
            )
            ax.set_xlabel("")
            if col_idx == 0:
                ax.legend(loc = "upper left")
                twin_ax.legend(loc = "center left")
        if col_idx == 1:
            ax.annotate(
                text = config_to_conc_label[config_name],
                xy = (row_label_x, 0.5),
                xycoords = 'axes fraction',
                va = 'center',
                ha = 'left',
                fontsize = label_font_size,
                rotation = -90,
            )
    plot_path = os.path.join(
        plot_dir,
        "gecko-nevents-grid.svg",
    )
    # fig.tight_layout()
    fig.savefig(plot_path, bbox_inches = "tight")
    plt.close(fig)



    # Create grid of div time plots with/without Palawan comparison
    fig = matplotlib.figure.Figure(
        figsize = [time_fig_width, time_fig_height],
    )
    fig_sans_old = matplotlib.figure.Figure(
        figsize = [time_fig_width, time_fig_height],
    )
    gs = fig.add_gridspec(
        nrows = 2, ncols = 2,
        wspace = time_wspace,
        hspace = time_hspace,
    )
    gs_sans_old = fig.add_gridspec(
        nrows = 2, ncols = 2,
        wspace = time_wspace,
        hspace = time_hspace,
    )
    for config_name, results in config_to_results.items():
        col_idx, row_idx = config_to_coords[config_name]
        ax = fig.add_subplot(gs[row_idx, col_idx])
        ax_sans_old = fig_sans_old.add_subplot(gs_sans_old[row_idx, col_idx])
        for i, current_ax in enumerate([ax, ax_sans_old]):
            comparisons_to_ignore = []
            if i == 1:
                comparisons_to_ignore = [old_timer]
            pycoevolity.plotting.plot_comparison_times(
                ax = current_ax,
                posterior_sample = results['posterior'],
                label_map = comparison_label_map,
                x_label = "Divergence time",
                y_label = "Comparison",
                comparisons_to_ignore = comparisons_to_ignore,
                include_map_model = include_map_model,
                colors = time_colors,
                x_limits = time_x_limits,
                include_zero = include_time_zero,
            )
            if row_idx == 0:
                current_ax.set_title(
                    config_to_prior_label[config_name],
                    fontsize = time_label_font_size,
                    pad = col_label_pad,
                )
            if col_idx == 1:
                current_ax.annotate(
                    text = config_to_conc_label[config_name],
                    xy = (time_row_label_x, 0.5),
                    xycoords = 'axes fraction',
                    va = 'center',
                    ha = 'left',
                    fontsize = time_label_font_size,
                    rotation = -90,
                )
    plot_path = os.path.join(
        plot_dir,
        "gecko-div-times-grid.svg",
    )
    # fig.tight_layout()
    fig.savefig(plot_path, bbox_inches = "tight")
    plt.close(fig)
    plot_path = os.path.join(
        plot_dir,
        "gecko-div-times-sans-palawan-grid.svg",
    )
    # fig_sans_old.tight_layout()
    fig_sans_old.savefig(plot_path, bbox_inches = "tight")
    plt.close(fig_sans_old)


    time_plot_width = 7.0
    time_plot_height = time_plot_width / 1.618034
    # Create individual plots without Palawan comparison
    for config_name, results in config_to_results.items():
        plot_path = os.path.join(
            plot_dir,
            f"{config_name}-div-times-sans-palawan.svg",
        )
        fig = matplotlib.figure.Figure(
            figsize = [time_plot_width, time_plot_height],
        )
        gs = fig.add_gridspec(nrows = 1, ncols = 1,
                wspace = 0.0,
                hspace = 0.0)
        ax = fig.add_subplot(gs[0, 0])
        pycoevolity.plotting.plot_comparison_times(
            ax = ax,
            posterior_sample = results['posterior'],
            label_map = comparison_label_map,
            x_label = "Divergence time",
            y_label = "Comparison",
            comparisons_to_ignore = [old_timer],
            include_map_model = include_map_model,
            colors = time_colors,
            x_limits = None,
            include_zero = include_time_zero,
        )
        fig.tight_layout()
        fig.savefig(plot_path, bbox_inches = "tight")
        plt.close(fig)
    
if __name__ == '__main__':
    main()
