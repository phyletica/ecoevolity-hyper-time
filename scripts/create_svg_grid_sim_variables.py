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

    files_to_out_file = {
        (
            "unif-hp-sim-study-nevents-heatmap-grid.svg",
            "unif-hp-sim-study-nevents-error-scatter-grid.svg",
        ) : "unif-hp-sim-study-nevents-grid.svg",
        (
            "exp-hp-sim-study-nevents-heatmap-grid.svg",
            "exp-hp-sim-study-nevents-error-scatter-grid.svg",
        ) : "exp-hp-sim-study-nevents-grid.svg",
        (
            "exp-hp-sim-study-nevents-heatmap-grid.svg",
            "unif-hp-sim-study-nevents-heatmap-grid.svg",
        ) : "hp-sim-study-nevents-grid.svg",
        (
            "exp-hp-sim-study-nevents-error-scatter-grid.svg",
            "unif-hp-sim-study-nevents-error-scatter-grid.svg",
        ) : "hp-sim-study-nevents-error-grid.svg",
        (
            "exp-hp-sim-study-root_height-scatter-grid.svg",
            "unif-hp-sim-study-root_height-scatter-grid.svg",
        ) : "hp-sim-study-div-time-grid.svg",
        (
            "exp-hp-sim-study-concentration-scatter-grid.svg",
            "unif-hp-sim-study-concentration-scatter-grid.svg",
        ) : "hp-sim-study-concentration-grid.svg",
        (
            "exp-hp-sim-study-pop_size_root-scatter-grid.svg",
            "unif-hp-sim-study-pop_size_root-scatter-grid.svg",
        ) : "hp-sim-study-pop-size-grid.svg",
    }

    for svg_files, out_file in files_to_out_file.items():
        svg_paths = tuple(os.path.join(image_dir_path, f) for f in svg_files)
        out_path = os.path.join(
            image_dir_path,
            out_file,
        )

        fig = svg_helpers.stack_plots(
            svg_paths = svg_paths,
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
