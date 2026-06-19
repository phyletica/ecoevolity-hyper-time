#!/usr/bin/env python

import sys
import os
import yaml

import get_gecko_mutation_rates


# Avoid anchors and aliases in yaml output
yaml.Dumper.ignore_aliases = lambda self, data: True
yaml.SafeDumper.ignore_aliases = lambda self, data: True


def get_mutation_rates(yaml_path):
    with open(yaml_path, "r") as in_stream:
        data = yaml.safe_load(in_stream)
    return data

def get_genus(config):
    genus = "Cyrtodactylus"
    data_path = config["comparisons"][0]["comparison"]["path"]
    data_file_name = os.path.basename(data_path)
    if data_file_name.startswith("G-"):
        genus = "Gekko"
    return genus

def convert_time_prior(config, mu_rate):
    exp_rate = config["event_time_prior"]["exponential_distribution"]["rate"]
    exp_mean = 1.0 / exp_rate

    config["event_time_prior"]["exponential_distribution"].pop("rate")

    new_mean = exp_mean / mu_rate
    config["event_time_prior"]["exponential_distribution"]["mean"] = {
        "value" : new_mean,
        "estimate" : "true",
        "prior" : {
            "exponential_distribution" : {
                "mean" : new_mean,
            },
        }
    }

def convert_comparison_parameters(config, mu_rate):
    pop_size_shape = config["global_comparison_settings"]["parameters"]["population_size"]["prior"]["gamma_distribution"]["shape"]
    pop_size_scale = config["global_comparison_settings"]["parameters"]["population_size"]["prior"]["gamma_distribution"]["scale"]
    pop_size_mean = pop_size_shape * pop_size_scale

    new_mean = pop_size_mean / mu_rate
    config["global_comparison_settings"]["parameters"]["population_size"]["prior"]["gamma_distribution"]["mean"] = new_mean
    config["global_comparison_settings"]["parameters"]["population_size"]["value"] = new_mean
    config["global_comparison_settings"]["parameters"]["population_size"]["prior"]["gamma_distribution"].pop("scale")

    config["global_comparison_settings"]["parameters"]["mutation_rate"]["value"] = mu_rate

    for comp in config["comparisons"]:
        comp["comparison"]["parameters"] = {}
        comp["comparison"]["parameters"]["population_size"] = config["global_comparison_settings"]["parameters"]["population_size"]
        comp["comparison"]["parameters"]["mutation_rate"] =   config["global_comparison_settings"]["parameters"]["mutation_rate"]

    config["global_comparison_settings"]["parameters"].pop("population_size")
    config["global_comparison_settings"]["parameters"].pop("mutation_rate")

def update_ops(config):
    config["operator_settings"]["operators"]["ConcentrationScaler"]["weight"] = 8.0
    config["operator_settings"]["operators"]["TimePriorParameterScaler-0"] = {
        "parameter_name" : "mean",
        "weight" : 10.0,
    }

def update_config(config, mu_rate):
    convert_time_prior(config, mu_rate)
    convert_comparison_parameters(config, mu_rate)
    update_ops(config)

def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    project_dir = os.path.dirname(script_dir)

    mu_rate_data_path = os.path.join(
        project_dir,
        "data",
        "mutation_rates.yml",
    )

    if not os.path.exists(mu_rate_data_path):
        get_gecko_mutation_rates.main(mu_rate_data_path)

    mu_rates = get_mutation_rates(mu_rate_data_path)

    input_data = sys.stdin.read()

    data = yaml.safe_load(input_data)

    genus = get_genus(data)
    mu_rate = mu_rates["rates"][genus]

    update_config(data, mu_rate)

    yaml.dump(data, sys.stdout, default_flow_style = False, sort_keys = False)

if __name__ == '__main__':
    main()
