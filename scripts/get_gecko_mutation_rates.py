#!/usr/bin/env python

import sys
import re
import io
import gzip
import requests
import yaml

def get_file_lines(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text.splitlines()

def get_gecko_genus_root_ages():
    root_age_pattern_str = (
        r'^(?P<genus>[a-z]+)_root_age=(?P<age>[0-9.]+)$'
    )
    root_age_pattern = re.compile(root_age_pattern_str)
    url = "https://raw.githubusercontent.com/phyletica/phycoeval-experiments/refs/heads/master/scripts/gekkonid-scripts/labels_and_calibrations.sh"
    ages = {}
    for line in get_file_lines(url):
        m = root_age_pattern.match(line.strip())
        if m:
            ages[m.group("genus")] = float(m.group("age"))
    return ages

# This is too slow and memory-intensive, so defining a new function below to
# parse line-by-line to find a specific value
def parse_gzipped_yaml_from_url(gzipped_yaml_url):
    response = requests.get(gzipped_yaml_url, stream = True)
    response.raise_for_status()
    with gzip.GzipFile(fileobj = response.raw) as gz_file:
        yaml_data = yaml.safe_load(gz_file)
    return yaml_data

def parse_value_from_gzipped_yaml_url(gzipped_yaml_url, key_path):
    key_path = tuple(key_path)
    assert len(key_path) > 0
    target_value = None
    with requests.get(gzipped_yaml_url, stream = True) as response:
        response.raise_for_status()
        with gzip.GzipFile(fileobj = response.raw) as gz_file:
            current_level = 0
            indent_size = None

            for line in gz_file:
                line_rstrip = line.decode('utf-8').rstrip()
                line_lstrip = line_rstrip.lstrip()
                if ':' not in line_lstrip:
                    continue
                if not line_lstrip or line_lstrip.startswith('#'):
                    continue
                
                indent = len(line_rstrip) - len(line_lstrip)

                if (indent_size is None) and (indent > 0):
                    indent_size = indent

                divisor = indent_size if indent_size else 2
                calc_level = indent // divisor

                key, _, val = line_lstrip.partition(':')
                key = key.strip().strip("'\"")

                if calc_level < current_level:
                    # We stepped out of a block
                    current_level = calc_level

                if (calc_level == current_level) and (key == key_path[current_level]):
                    current_level += 1

                    if current_level == len(key_path):
                        target_value = val.strip().strip("'\"")
                        break
    return target_value

def get_gecko_genus_divs():
    urls = {
        "cyrt" : "https://github.com/phyletica/phycoeval-experiments/raw/refs/heads/master/gekkonid-output/posterior-summary-cyrt-nopoly.yml.gz",
        "gekko" : "https://github.com/phyletica/phycoeval-experiments/raw/refs/heads/master/gekkonid-output/posterior-summary-gekko-nopoly.yml.gz",
    }
    subs_per_site = {}
    for genus, url in urls.items():
        # data = parse_gzipped_yaml_from_url(url)
        # subs_per_site[genus] = data["splits"]["root"]["height_mean"]
        root_height = parse_value_from_gzipped_yaml_url(
            gzipped_yaml_url = url,
            key_path = ("splits", "root", "height_mean"),
        )
        subs_per_site[genus] = float(root_height)
    return subs_per_site

def get_gecko_mutation_rates():
    sys.stderr.write(
        "Getting gecko genus clade ages...\n"
    )
    ages = get_gecko_genus_root_ages()
    sys.stderr.write(
        "Getting gecko genus genetic divergence...\n"
    )
    divs = get_gecko_genus_divs()
    assert sorted(ages.keys()) == sorted(divs.keys())
    rates = {}
    for genus, divergence in divs.items():
        rate = divergence / ages[genus]
        rates[genus] = rate
    return rates

def main(out_stream = sys.stdout):
    mu_rates = get_gecko_mutation_rates()
    d = {
        'units': 'substitutions/site/million years',
        'rates' : {
            'Cyrtodactylus' : mu_rates['cyrt'],
            'Gekko' : mu_rates['gekko'],
        },
    }
    yaml.dump(d, out_stream, default_flow_style = False, sort_keys = False)

if __name__ == '__main__':
    if len(sys.argv) > 2:
        sys.stderr.write(
            "ERROR: At most 1 command-line argument is excepted\n"
        )
        sys.exit(1)
    if len(sys.argv) == 2:
        out_path = sys.argv[1]
        with open(out_path, "w") as out_stream:
            main(out_stream)
    else:
        main(sys.stdout)
