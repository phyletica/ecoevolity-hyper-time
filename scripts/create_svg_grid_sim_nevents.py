#!/usr/bin/env python

import os
import sys

import svgutils.transform as svgt
import svgutils.compose as svgc

import svg_helpers

def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    project_dir = os.path.dirname(script_dir)
    image_dir_path = os.path.join(
        project_dir,
        "docs",
        "images",
    )

    unif_svg_files = (
        "unif-hp-sim-study-nevents-heatmap-grid.svg",
        "unif-hp-sim-study-nevents-error-scatter-grid.svg",
    )
    unif_svg_paths = tuple(os.path.join(image_dir_path, f) for f in unif_svg_files)
    out_path = os.path.join(
        image_dir_path,
        "unif-hp-sim-study-nevents-grid.svg",
    )

    fig = svg_helpers.stack_plots(
        svg_paths = unif_svg_paths,
        space = 0,
        scale_by_width = True,
        include_letters = False,
        letter_font_weight = "bold",
        letter_font_size = 18,
        letter_x_indent = None,
    )
    fig.save(out_path)

    exp_svg_files = (
        "exp-hp-sim-study-nevents-heatmap-grid.svg",
        "exp-hp-sim-study-nevents-error-scatter-grid.svg",
    )
    exp_svg_paths = tuple(os.path.join(image_dir_path, f) for f in exp_svg_files)
    out_path = os.path.join(
        image_dir_path,
        "exp-hp-sim-study-nevents-grid.svg",
    )

    fig = svg_helpers.stack_plots(
        svg_paths = exp_svg_paths,
        space = 0,
        scale_by_width = True,
        include_letters = False,
        letter_font_weight = "bold",
        letter_font_size = 18,
        letter_x_indent = None,
    )
    fig.save(out_path)

if __name__ == '__main__':
    main()
