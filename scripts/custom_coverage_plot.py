#!/usr/bin/env python

import os
import sys
import math
import pandas as pd
import scipy.stats as st
import matplotlib.pyplot as plt
import seaborn as sns

import pycoevolity


def rename_hyperparameter_columns(df):
    name_map = {}
    for col_name in df.columns:
        if "time_prior_parameter" in col_name:
            if "_0" in col_name:
                new_name = "".join(col_name.split("_0"))
            elif "_1" in col_name:
                new_name = "".join(col_name.split("_1"))
            else:
                raise Exception(
                    f"Unexpected column header: {col_name}"
                )
            name_map[col_name] = new_name
    df = df.rename(columns = name_map)
    return df

def get_parameter_data_frame(
    df,
    parameter_root,
    parameter_label = None,
    other_cols_to_keep = (
        "simulation_id",
        "simulation_config",
        "inference_config",
    ),
):
    parameters = pycoevolity.plotting.get_all_comparison_parameters(
        parameter_prefix = parameter_root,
        column_headers = df.columns,
    )
    if not parameters:
        if f"mean_{parameter_root}" in df.columns:
            parameters = [parameter_root]
        else:
            raise Exception(
                f"Unexpected parameter root: {parameter_root}"
            )
    new_df = pycoevolity.plotting.get_stacked_parameter_data_frame(
        data_frame = df,
        parameters = parameters,
        parameter_root = parameter_root,
        extra_cols_to_keep = other_cols_to_keep,
    )
    name_map = {}
    for col_name in new_df.columns:
        if parameter_root in col_name:
            new_name = "".join(col_name.split(f"_{parameter_root}"))
            name_map[col_name] = new_name
    new_df = new_df.rename(columns = name_map)
    if not parameter_label:
        parameter_label = parameter_root
    new_df["variable"] = parameter_label
    return new_df

def custom_annotate_scatter(
    data,
    x,
    y,
    y_error_lower = None,
    y_error_upper = None,
    position = (0.02, 0.98),
    cred_level = 0.95,
    stat_label = None,
    **kwargs,
):
    ax = plt.gca()
    sum_sq_err = ((data[x].values - data[y].values) ** 2).sum()
    mean_sq_err = sum_sq_err / len(data)
    root_mean_sq_err = math.sqrt(mean_sq_err)
    if not stat_label:
        stat_label = "x"
    annot_str = (
        r"$\text{{RMSE}} = {rmse:.2g}$".format(
            rmse = root_mean_sq_err,
        )
    )
    if y_error_lower and y_error_upper:
        num_within_ci = (
            (data[x] >= data[y_error_lower])
            & (data[x] <= data[y_error_upper])
        ).sum()
        prop_within_ci = num_within_ci / len(data[x])
        binom_test = st.binomtest(
            k = num_within_ci,
            n = len(data[x]),
            p = 0.5,
            alternative = 'two-sided',
        )
        annot_str = (
            r"$p({stat_label} \in {cred_level:.2f}\,\text{{CI}}) = {coverage:.2g}$"
            "\n"
            r"$\text{{p-value}} = {pval:.2g}$".format(
                stat_label = stat_label,
                cred_level = cred_level,
                coverage = prop_within_ci,
                pval = binom_test.pvalue,
            )
        )
    default_args = {
        'horizontalalignment' : "left",
        'verticalalignment' : "top",
        'transform' : ax.transAxes,
        'zorder' : 200,
        'fontsize' : 'small',
        'bbox' : {
            'facecolor': 'white',
            # 'edgecolor': 'white',
            'pad': 2,
            'alpha': 0.5,
        },
    }
    default_args.update(kwargs)
    # seaborn passes in color keyword arg set to the same color used for
    # plotting points; overriding that here
    default_args["color"] = "black"
    ax.text(
        position[0], position[1],
        annot_str,
        **default_args,
    )

def main():
    sns.set_theme(
        context = 'notebook',
        style = 'ticks',
        palette = 'colorblind',
        font = 'sans-serif',
        font_scale = 1.4,
    )

    script_dir = os.path.dirname(os.path.realpath(__file__))
    project_dir = os.path.dirname(script_dir)
    plot_path = os.path.join(
        project_dir,
        "docs",
        "images",
        "posterior-coverage-grid.svg",
    )

    exp_coverage_results_path = os.path.join(
        project_dir,
        "coverage-check-exp-hyperprior",
        "results-summary.tsv.gz",
    )

    unif_coverage_results_path = os.path.join(
        project_dir,
        "coverage-check-unif-hyperprior",
        "results-summary.tsv.gz",
    )

    exp_df = pd.read_csv(
        exp_coverage_results_path,
        sep = "\t",
    )

    exp_df = rename_hyperparameter_columns(exp_df)

    unif_df = pd.read_csv(
        unif_coverage_results_path,
        sep = "\t",
    )

    unif_df = rename_hyperparameter_columns(unif_df)

    assert sorted(exp_df.columns) == sorted(unif_df.columns)

    df = pd.concat([exp_df, unif_df])

    ci = pycoevolity.plotting.get_cred_interval_percent(df.columns)
    cred_level = int(ci) / 100

    other_cols_to_keep = [
        "simulation_id",
        "simulation_config",
        "inference_config",
    ]

    parameters_to_plot = {
        "root_height" : {
            "label" : "Divergence time",
        },
        "pop_size_root" : {
            "label" : "Ancestral $N_e$",
        },
        "concentration" : {
            "label" : "DP concentration",
        },
        "time_prior_parameter" : {
            "label" : "Time prior parameter",
        },
    }
    param_dfs = []
    for param, settings in parameters_to_plot.items():
        d = get_parameter_data_frame(
            df = df,
            parameter_root = param,
            parameter_label = settings["label"],
            other_cols_to_keep = other_cols_to_keep,
        )
        param_dfs.append(d)

    param_df = pd.concat(param_dfs)

    grid = pycoevolity.plotting.plot_scatter_grid(
        data_frame = param_df,
        true_col = "true",
        est_col = "mean",
        row_col = "variable",
        column_col = "simulation_config",
        est_lower_col = f"hpdi_{ci}_lower",
        est_upper_col = f"hpdi_{ci}_upper",
        true_val_rank_col = "true_rank",
        xlabel = "True value",
        ylabel = "Posterior mean",
        ess_col = "ess",
        psrf_col = "psrf",
        ess_min = 200,
        psrf_max = 1.2,
        bad_sampling_color = "C1",
        ordered_labels = None,
        height = 4.5,
        annotate_stats = True,
        annotate_func = custom_annotate_scatter,
        stat_label = "x",
        annot_position = (0.02, 0.98),
        cred_level = cred_level,
        scatter_kwargs = {},
        annotate_kwargs = {},
        col_title_template = r"$\tau \sim$ {col_name}",
        row_title_template = "{row_name}",
        sharey = False,
        sharex = False,
    )
    width, height = grid.fig.get_size_inches()
    width *= 1.3
    grid.fig.set_size_inches(width, height)
    grid.savefig(plot_path)

if __name__ == '__main__':
    main()
