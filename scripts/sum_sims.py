#!/usr/bin/env python

import os
import sys
import random
import argparse
import json

import pycoevolity

import project_utils
import plotting


def parse_cli_args():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        'json_results_file',
        type = pycoevolity.argparse_utils.arg_is_file,
        help = (
            'Path to JSON results file.'
        ),
    )
    parser.add_argument(
        '-o', '--output-dir',
        action = 'store',
        type = project_utils.arg_is_dir_or_new_dir,
        help = (
            'The directory in which to put all output files.'
        ),
    )

    args = parser.parse_args()
    return args

def main_cli():
    args = parse_cli_args()

    output_dir = os.path.abspath(
        project_utils.process_output_dir_arg(args.output_dir))
    with open(args.json_results_file, "r") as json_stream:
        results = interop.load_results_json(json_stream)

if __name__ == "__main__":
    main_cli()
