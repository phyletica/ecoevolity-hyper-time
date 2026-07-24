#!/usr/bin/env python

import os
import sys

import svg_helpers

def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    project_dir = os.path.dirname(script_dir)
    image_dir_path = os.path.join(
        project_dir,
        "docs",
        "images",
    )
    out_path = os.path.join(image_dir_path, "prior-sampling-grid.svg")
    svg_files = (
        "dpp-conc-hypergamma-4-10-time-hyperexp-02-pairs-20-sites-20000-prior-cmf-comparison-nevents.svg",
        "dpp-conc-hypergamma-4-10-time-hyperunif-02-pairs-20-sites-20000-prior-cmf-comparison-nevents.svg",
        "dpp-conc-hypergamma-4-10-time-hyperexp-02-pairs-20-sites-20000-prior-cdf-comparison-mean.svg",
        "dpp-conc-hypergamma-4-10-time-hyperunif-02-pairs-20-sites-20000-prior-cdf-comparison-max.svg",
        "dpp-conc-hypergamma-4-10-time-hyperexp-02-pairs-20-sites-20000-prior-cdf-comparison-concentration.svg",
        "dpp-conc-hypergamma-4-10-time-hyperunif-02-pairs-20-sites-20000-prior-cdf-comparison-concentration.svg",
        "dpp-conc-hypergamma-4-10-time-hyperexp-02-pairs-20-sites-20000-prior-cdf-comparison-root_height_c1sp1.svg",
        "dpp-conc-hypergamma-4-10-time-hyperunif-02-pairs-20-sites-20000-prior-cdf-comparison-root_height_c1sp1.svg",
        "dpp-conc-hypergamma-4-10-time-hyperexp-02-pairs-20-sites-20000-prior-cdf-comparison-pop_size_c1sp1.svg",
        "dpp-conc-hypergamma-4-10-time-hyperunif-02-pairs-20-sites-20000-prior-cdf-comparison-pop_size_c1sp1.svg",
    )
    svg_paths = tuple(os.path.join(image_dir_path, f) for f in svg_files)
    col_header_files = (
        "model-exp-short.svg",
        "model-unif-short.svg",
    )
    col_header_paths = tuple(os.path.join(image_dir_path, f) for f in col_header_files) 
    headers = (
        "τ ~ Exp(mean ~ Exp(mean = 0.2))",
        "τ ~ Unif(0, max ~ Unif(0, 0.2))",
    )
    fig = svg_helpers.get_panel_figure(
        svg_paths = svg_paths,
        num_cols = 2,
        col_headers = headers,
        col_header_svg_paths = None,
        header_svg_scale = 2.0,
        header_font_weight = "bold",
        header_font_size = 22,
        include_letters = False,
        letter_font_weight = "normal",
        letter_font_size = 16,
    )
    fig.save(out_path)

if __name__ == '__main__':
    main()
