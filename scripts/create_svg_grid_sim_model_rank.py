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

    svg_files = (
        "exp-hp-sim-study-true-model-rank-sum-violin-grid.svg",
        "unif-hp-sim-study-true-model-rank-sum-violin-grid.svg",
    )
    svg_paths = tuple(os.path.join(image_dir_path, f) for f in svg_files)
    out_path = os.path.join(
        image_dir_path,
        "hp-sim-study-true-model-rank-sum-grid.svg",
    )

    fig = svg_helpers.align_plots(
        svg_paths = svg_paths,
        space = 0,
        scale_by_height = True,
        include_letters = False,
        letter_font_weight = "bold",
        letter_font_size = 18,
        letter_x_indent = None,
    )
    fig.save(out_path)

if __name__ == '__main__':
    main()
