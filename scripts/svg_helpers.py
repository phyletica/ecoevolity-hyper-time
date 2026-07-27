#!/usr/bin/env python

import os
import sys
import math
import string

import svgutils.transform as svgt
import svgutils.compose as svgc

def get_plot_dimensions(svg_path):
    fig = svgt.fromfile(svg_path)
    w = float(fig.width[:-2])
    h = float(fig.height[:-2])
    u = fig.height[-2:]
    return w, h, u

def scale_by_max_width(max_width, max_height, width, height):
    if width < max_width:
        m = max_width / width
        return width * m, height * m
    return width, height

def scale_by_max_height(max_width, max_height, width, height):
    if height < max_height:
        m = max_height / height
        return width * m, height * m
    return width, height

def get_max_plot_dimensions(svg_paths, scale_func = None):
    max_height = None
    max_width = None
    units = None
    for svg_path in svg_paths:
        w, h, u = get_plot_dimensions(svg_path)
        if units is None:
            max_height = h
            max_width = w
            units = u
        else:
            if scale_func:
                w, h = scale_func(max_width, max_height, w, h)
            if h > max_height:
                max_height = h
            if w > max_width:
                max_width = w
            assert units == u
    return max_width, max_height, units

def stack_plots(
    svg_paths,
    space = 0,
    scale_by_width = True,
    include_letters = False,
    letter_font_weight = "bold",
    letter_font_size = 16,
    letter_x_indent = None,
):
    scale_func = None
    if scale_by_width:
        scale_func = scale_by_max_width
    max_width, max_height, units = get_max_plot_dimensions(svg_paths, scale_func)
    if letter_x_indent is None:
        letter_x_indent = 0.01 * max_width
    panels = []
    current_y = 0.0
    half_space = space / 2.0
    for i, svg_path in enumerate(svg_paths):
        letter = string.ascii_uppercase[i]
        scaler = 1.0
        w, h, u = get_plot_dimensions(svg_path)
        if scale_by_width:
            scaler = max_width / w
        if include_letters:
            p = svgc.Panel(
                svgc.SVG(
                    svg_path,
                ).scale(scaler).move(0, space),
                svgc.Text(
                    letter,
                    letter_x_indent, (letter_font_size * 0.9),
                    size = letter_font_size,
                    weight = letter_font_weight,
                ),
                # Moving SVG image down within the panel to give room under
                # letter
            ).move(0, current_y)
        else:
            p = svgc.Panel(
                svgc.SVG(svg_path),
            ).scale(scaler).move(0, current_y)
        panels.append(p)
        if i < (len(svg_paths) - 1) or include_letters:
            current_y += (h * scaler) + space
        else:
            current_y += (h * scaler)
    figure_width = max_width
    figure_height = current_y
    fig = svgc.Figure(
        f"{figure_width}px", f"{figure_height}px",
        *panels,
    )
    return fig

def align_plots(
    svg_paths,
    space = 0,
    scale_by_height = True,
    include_letters = False,
    letter_font_weight = "bold",
    letter_font_size = 16,
    letter_x_indent = None,
):
    scale_func = None
    if scale_by_height:
        scale_func = scale_by_max_height
    max_width, max_height, units = get_max_plot_dimensions(svg_paths, scale_func)
    if letter_x_indent is None:
        letter_x_indent = 0.01 * max_width
    panels = []
    current_x = 0.0
    half_space = space / 2.0
    for i, svg_path in enumerate(svg_paths):
        letter = string.ascii_uppercase[i]
        scaler = 1.0
        w, h, u = get_plot_dimensions(svg_path)
        if scale_by_height:
            scaler = max_height / h
        if include_letters:
            p = svgc.Panel(
                svgc.SVG(
                    svg_path,
                ).scale(scaler).move(0, space),
                svgc.Text(
                    letter,
                    letter_x_indent, (letter_font_size * 0.9),
                    size = letter_font_size,
                    weight = letter_font_weight,
                ),
                # Moving SVG image down within the panel to give room under
                # letter
            ).move(current_x, 0)
        else:
            p = svgc.Panel(
                svgc.SVG(svg_path),
            ).scale(scaler).move(current_x, 0)
        panels.append(p)
        current_x += (w * scaler)
    figure_width = current_x
    figure_height = max_height + space
    fig = svgc.Figure(
        f"{figure_width}px", f"{figure_height}px",
        *panels,
    )
    return fig

def get_panel_figure(
    svg_paths,
    num_cols,
    scale_by_width = False,
    col_headers = None,
    col_header_svg_paths = None,
    header_svg_scale = 1.0,
    header_font_weight = "bold",
    header_font_size = 22,
    header_x_indent = None,
    header_y_indent = None,
    include_letters = False,
    letter_font_weight = "bold",
    letter_font_size = 16,
    letter_x_indent = None,
    letter_y_indent = None,
):
    num_rows = int(math.ceil(len(svg_paths) / num_cols))
    scale_func = None
    if scale_by_width:
        scale_func = scale_by_max_width
    plot_width, plot_height, units = get_max_plot_dimensions(svg_paths, scale_func)
    header_width = None
    header_height = None
    header_units = None
    if col_header_svg_paths:
        header_width, header_height, header_units = get_max_plot_dimensions(col_header_svg_paths)
    if header_x_indent is None:
        header_x_indent = 0.05 * plot_width
    if header_y_indent is None:
        header_y_indent = header_font_size
    if letter_x_indent is None:
        letter_x_indent = 0.01 * plot_width
    if letter_y_indent is None:
        letter_y_indent = letter_font_size
    letter_height_buffer = 0
    if include_letters:
        letter_height_buffer = letter_y_indent * 1.2
    header_height_buffer = 0
    if col_header_svg_paths:
        header_height_buffer = header_height * header_svg_scale
    elif col_headers:
        header_height_buffer = header_y_indent * 1.2
    header_panels = []
    if col_header_svg_paths:
        assert len(col_header_svg_paths) == num_cols
        for i, col_head_svg in enumerate(col_header_svg_paths):
            move_x = (plot_width * i) + header_x_indent
            p = svgc.Panel(
                svgc.SVG(col_head_svg),
            )
            p.scale(header_svg_scale)
            p.move(move_x, 0)
            header_panels.append(p)
    elif col_headers:
        assert len(col_headers) == num_cols
        for i, col_head in enumerate(col_headers):
            p = svgc.Panel(
                svgc.Text(
                    col_head,
                    header_x_indent, header_y_indent,
                    size = header_font_size,
                    weight = header_font_weight,
                ),
            ).move(plot_width * i, 0)
            header_panels.append(p)

    panels = []
    for i, svg_path in enumerate(svg_paths):
        col_index = i % num_cols
        first_pos = i - col_index
        row_index = first_pos // num_cols
        letter = string.ascii_uppercase[i]
        move_x = plot_width * col_index
        move_y = plot_height * row_index
        move_y += header_height_buffer
        scaler = 1.0
        if scale_by_width:
            w, h, u = get_plot_dimensions(svg_path)
            if w < plot_width:
                scaler = plot_width / w
        if include_letters:
            # Move whole panel down for previous rows' letters
            move_y += (row_index * letter_height_buffer)
            p = svgc.Panel(
                svgc.SVG(
                    svg_path,
                ).scale(scaler).move(0, letter_y_indent * 1.2),
                svgc.Text(
                    letter,
                    letter_x_indent, letter_y_indent,
                    size = letter_font_size,
                    weight = letter_font_weight,
                ),
                # Moving SVG image down within the panel to give room under
                # letter
            ).move(move_x, move_y)
        else:
            p = svgc.Panel(
                svgc.SVG(svg_path),
            ).scale(scaler).move(move_x, move_y)
        panels.append(p)
    figure_width = plot_width * num_cols
    figure_height = plot_height * num_rows
    figure_height += header_height_buffer
    figure_height += (num_rows * letter_height_buffer)
    fig = svgc.Figure(
        f"{figure_width}px", f"{figure_height}px",
        *header_panels,
        *panels,
    )
    return fig
