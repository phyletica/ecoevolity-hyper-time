#!/usr/bin/env python

import os
import sys
import numpy as np
import scipy.stats as st
import matplotlib.pyplot as plt
import seaborn as sns

import pycoevolity


def compare_samples_to_cdf(
    ax,
    samples,
    prob_dist,
    include_ks_test = True,
):
    samples = sorted(samples)
    sample_cd = np.arange(len(samples)) / float(len(samples))
    emp_line = sns.lineplot(
        x = samples,
        y = sample_cd,
        ax = ax,
        label = "Empirical",
    )
    if hasattr(prob_dist, "ppf"):
        x = np.linspace(prob_dist.ppf(0.001), prob_dist.ppf(0.999), 100)
        model_cd = prob_dist.cdf(x)
    else:
        prob_dist = sorted(prob_dist)
        x = prob_dist
        model_cd = np.arange(len(prob_dist)) / float(len(prob_dist))

    mod_line = sns.lineplot(
        x = x,
        y = model_cd,
        ax = ax,
        label = "Model",
    )
    ax.set(
        xlabel = "X",
        ylabel = "Cumulative density",
    )
    if include_ks_test:
        prob_arg = prob_dist
        if hasattr(prob_dist, "cdf"):
            prob_arg = prob_dist.cdf
        res = st.kstest(
            samples,
            prob_arg,
            alternative = "two-sided",
        )
        ks_str = f"KS D = {res.statistic:.2g}\np = {res.pvalue:.2g}"
        ax.text(
            0.99, 0.02,
            ks_str,
            horizontalalignment = "right",
            verticalalignment = "bottom",
            transform = ax.transAxes,
            zorder = 500,
            fontsize = 'small',
            # bbox = {
            #     'facecolor': 'white',
            #     'edgecolor': 'white',
            #     'pad': 2},
        )
    # ax.legend(bbox_to_anchor = (1.01, 0.5), loc = "center left")
    ax.legend(loc = "center right")
    return emp_line, mod_line

def compare_nevents_samples_to_cdf(
    ax,
    samples,
    prior_samples,
    number_of_comparisons,
    include_ks_test = True,
):
    emp_line = sns.ecdfplot(
        x = samples,
        ax = ax,
        label = "Empirical",
    )
    mod_line = sns.ecdfplot(
        x = prior_samples,
        ax = ax,
        label = "Model",
    )
    ax.set(
        xlabel = "Number of events",
        ylabel = "Cumulative probability",
        xlim = (1, number_of_comparisons),
    )
    if include_ks_test:
        res = st.kstest(
            samples,
            prior_samples,
            alternative = "two-sided",
        )
        ks_str = f"KS D = {res.statistic:.2g}\np = {res.pvalue:.2g}"
        ax.text(
            0.99, 0.02,
            ks_str,
            horizontalalignment = "right",
            verticalalignment = "bottom",
            transform = ax.transAxes,
            zorder = 500,
            fontsize = 'small',
            # bbox = {
            #     'facecolor': 'white',
            #     'edgecolor': 'white',
            #     'pad': 2},
        )
    # ax.legend(bbox_to_anchor = (1.01, 0.5), loc = "center left")
    ax.legend(loc = "center right")
    return emp_line, mod_line

def qq(ax, samples, prob_dist):
    probs = np.linspace(0.01, 0.99, num = 99)
    if hasattr(prob_dist, "ppf"):
        q = prob_dist.ppf(probs)
    else:
        q = np.quantile(prob_dist, probs)
    sample_q = np.quantile(samples, probs)
    mn = min(min(q), min(sample_q))
    mx = max(max(q), max(sample_q))
    identity_line, = ax.plot(
        [mn, mx],
        [mn, mx],
    )
    plt.setp(
        identity_line,
        color = '0.7',
        linestyle = '-',
        linewidth = 1.0,
        marker = '',
        zorder = 0,
    )
    ax.set_xlim(mn, mx)
    ax.set_ylim(mn, mx)
    line, = ax.plot(q, sample_q)
    plt.setp(
        line,
        marker = 'o',
        linestyle = '',
        markerfacecolor = 'none',
        markeredgecolor = '0.35',
        markeredgewidth = 1.0,
        # markersize = 2.5,
        zorder = 100,
    )
    ax.set(
        xlabel = "Model quantiles",
        ylabel = "Sample quantiles",
    )
    return line
