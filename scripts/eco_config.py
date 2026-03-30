#!/usr/bin/env python

import scipy.stats as st
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import project_utils


def get_yaml_config(path):
    with open(path, 'r') as stream:
        config = yaml.load(stream, Loader = Loader)
    return config

def write_yaml_config(data, path):
    with open(path, 'w') as stream:
        yaml.dump(data, stream, Dumper = Dumper)

def get_gamma_shape_scale(mean, sd):
    variance = sd**2
    shape = (mean**2) / variance
    scale = variance / mean
    return shape, scale

def get_param_set(prior_parameters):
    params = list(prior_parameters.keys())
    param_set = set(params)
    if len(param_set) != len(params):
        raise Exception(
            "Duplicate parameters in distribution: {0}".format(
                ", ".join(params),
            )
        )
    return param_set

def vet_uniform_dist_params(prior_parameters):
    valid_param_sets = (
        {"min", "max"},
    )
    param_set = get_param_set(prior_parameters)
    if not param_set in valid_param_sets:
        raise Exception(
            "Invalid parameters for uniform distribution: {0}".format(
                ", ".join(prior_parameters.keys()),
            )
        )
    return

def vet_beta_dist_params(prior_parameters):
    valid_param_sets = (
        {"alpha", "beta"},
    )
    param_set = get_param_set(prior_parameters)
    if not param_set in valid_param_sets:
        raise Exception(
            "Invalid parameters for beta distribution: {0}".format(
                ", ".join(prior_parameters.keys()),
            )
        )
    return

def vet_exponential_dist_params(prior_parameters):
    valid_param_sets = (
        {"rate", "offset"},
        {"mean", "offset"},
        {"rate"},
        {"mean"},
    )
    param_set = get_param_set(prior_parameters)
    if not param_set in valid_param_sets:
        raise Exception(
            "Invalid parameters for exponential distribution: {0}".format(
                ", ".join(prior_parameters.keys()),
            )
        )
    return

def vet_gamma_dist_params(prior_parameters):
    valid_param_sets = (
        {"shape", "scale"},
        {"shape", "mean"},
        {"shape", "scale", "offset"},
        {"shape", "mean", "offset"},
    )
    param_set = get_param_set(prior_parameters)
    if not param_set in valid_param_sets:
        raise Exception(
            "Invalid parameters for gamma distribution: {0}".format(
                ", ".join(prior_parameters.keys()),
            )
        )
    return

def vet_hyper_gamma_dist_params(prior_parameters):
    valid_param_sets = (
        {"shape", "scale"},
        {"mean", "standard_deviation"},
    )
    param_set = get_param_set(prior_parameters)
    if not param_set in valid_param_sets:
        raise Exception(
            "Invalid parameters for 2-level gamma distribution: {0}".format(
                ", ".join(prior_parameters.keys()),
            )
        )
    return

def get_fixed_gamma_distribution(prior_parameters):
    vet_gamma_dist_params(prior_parameters)
    shape = float(prior_parameters["shape"])
    if "scale" in prior_parameters:
        assert not parameter_is_estimated(prior_parameters["scale"])
        scale = float(prior_parameters["scale"])
    elif "mean" in prior_parameters:
        assert not parameter_is_estimated(prior_parameters["mean"])
        scale = float(prior_parameters["mean"]) / shape
    if "offset" in prior_parameters:
        assert not parameter_is_estimated(prior_parameters["offset"])
        offset = float(prior_parameters["offset"])
        if offset != 0.0:
            raise Exception(
                "This python wrapper doesn't support gamma offset\n"
            )
    dist = st.gamma(shape, scale = scale)
    return dist

def get_fixed_beta_distribution(prior_parameters):
    vet_beta_dist_params(prior_parameters)
    assert not parameter_is_estimated(prior_parameters["alpha"])
    assert not parameter_is_estimated(prior_parameters["beta"])
    a = float(prior_parameters["alpha"])
    b = float(prior_parameters["beta"])
    dist = st.beta(a = a, b = b)
    return dist

def get_fixed_exponential_distribution(prior_parameters):
    vet_exponential_dist_params(prior_parameters)
    scale = None
    if "rate" in prior_parameters:
        assert not parameter_is_estimated(prior_parameters["rate"])
        scale = 1.0 / float(prior_parameters["rate"])
    elif "mean" in prior_parameters:
        assert not parameter_is_estimated(prior_parameters["mean"])
        scale = float(prior_parameters["mean"])
    if "offset" in prior_parameters:
        assert not parameter_is_estimated(prior_parameters["offset"])
        offset = float(prior_parameters["offset"])
        if offset != 0.0:
            raise Exception(
                "This python wrapper doesn't support gamma offset\n"
            )
    dist = st.gamma(1.0, scale = scale)
    return dist

def get_fixed_uniform_distribution(prior_parameters):
    vet_uniform_dist_params(prior_parameters)
    assert not parameter_is_estimated(prior_parameters["min"])
    assert not parameter_is_estimated(prior_parameters["max"])
    mn = float(prior_parameters["min"])
    mx = float(prior_parameters["max"])
    dist = st.uniform(mn, mx - mn)
    return dist

def get_fixed_distribution(prior_settings):
    assert len(prior_settings) == 1
    prior_name = list(prior_settings.keys())[0]
    prior_parameters = prior_settings[prior_name]
    if prior_name == "gamma_distribution":
        return get_fixed_gamma_distribution(prior_parameters)
    if prior_name == "exponential_distribution":
        return get_fixed_exponential_distribution(prior_parameters)
    if prior_name == "beta_distribution":
        return get_fixed_beta_distribution(prior_parameters)
    if prior_name == "uniform_distribution":
        return get_fixed_uniform_distribution(prior_parameters)
    raise Exception("Unexpected prior distribution: {0}".format(prior_name))

def parameter_is_estimated(parameter_settings):
    try:
        return parameter_settings.get("estimate", False)
    except AttributeError as e:
        return False

def fixed_param_values_are_valid(parameter_settings, posterior_samples):
    assert parameter_is_estimated(parameter_settings) is False
    fixed_value = parameter_settings["value"]
    valid = True
    for value in posterior_samples:
        if not project_utils.almost_equal(fixed_value, value):
            valid = False
            break
    return valid, fixed_value, value

def sample_uniform_distribution(numpy_rng, prior_parameters, n = 100000):
    vet_uniform_dist_params(prior_parameters)
    if parameter_is_estimated(prior_parameters["min"]):
        min_dist = get_fixed_distribution(prior_parameters["min"]["prior"])
    else:
        mn = float(prior_parameters["min"]["value"])
        min_dist = st.uniform(mn, 0.0)
    if parameter_is_estimated(prior_parameters["max"]):
        max_dist = get_fixed_distribution(prior_parameters["max"]["prior"])
    else:
        mx = float(prior_parameters["max"]["value"])
        max_dist = st.uniform(mx, 0.0)
    samples = []
    for i in range(n):
        a = min_dist.rvs(random_state = numpy_rng)
        b = max_dist.rvs(random_state = numpy_rng)
        x = st.uniform.rvs(a, b-a, random_state = numpy_rng)
        samples.append(x)
    return samples

def sample_exponential_distribution(numpy_rng, prior_parameters, n = 100000):
    vet_exponential_dist_params(prior_parameters)
    scale_dist = None
    if "rate" in prior_parameters:
        if parameter_is_estimated(prior_parameters["rate"]):
            scale_dist = get_fixed_distribution(prior_parameters["rate"]["prior"])
        else:
            scale = 1.0 / float(prior_parameters["rate"]["value"])
            scale_dist = st.uniform(scale, 0.0)
    elif "mean" in prior_parameters:
        if parameter_is_estimated(prior_parameters["mean"]):
            scale_dist = get_fixed_distribution(prior_parameters["mean"]["prior"])
        else:
            scale = float(prior_parameters["mean"]["value"])
            scale_dist = st.uniform(scale, 0.0)
    if "offset" in prior_parameters:
        assert not parameter_is_estimated(prior_parameters["offset"])
        offset = float(prior_parameters["offset"])
        if offset != 0.0:
            raise Exception(
                "This python wrapper doesn't support non-zero gamma offset\n"
            )
    samples = []
    for i in range(n):
        scale = scale_dist.rvs(random_state = numpy_rng)
        x = st.gamma.rvs(1.0, scale = scale, random_state = numpy_rng)
        samples.append(x)
    return samples

def sample_gamma_distribution(numpy_rng, prior_parameters, n = 100000):
    vet_hyper_gamma_dist_params(prior_parameters)
    samples = []
    if "mean" in prior_parameters:
        mean_dist = None
        sd_dist = None
        if parameter_is_estimated(prior_parameters["mean"]):
            mean_dist = get_fixed_distribution(prior_parameters["mean"]["prior"])
        else:
            mean = float(prior_parameters["mean"]["value"])
            mean_dist = st.uniform(mean, 0.0)
        if parameter_is_estimated(prior_parameters["standard_deviation"]):
            sd_dist = get_fixed_distribution(prior_parameters["standard_deviation"]["prior"])
        else:
            sd = float(prior_parameters["standard_deviation"]["value"])
            sd_dist = st.uniform(sd, 0.0)
        for i in range(n):
            mean = mean_dist.rvs(random_state = numpy_rng)
            sd = sd_dist.rvs(random_state = numpy_rng)
            shape, scale = get_gamma_shape_scale(mean, sd)
            x = st.gamma.rvs(shape, scale = scale, random_state = numpy_rng)
            samples.append(x)
    elif "shape" in prior_parameters:
        shape_dist = None
        scale_dist = None
        if parameter_is_estimated(prior_parameters["shape"]):
            shape_dist = get_fixed_distribution(prior_parameters["shape"]["prior"])
        else:
            shape = float(prior_parameters["shape"]["value"])
            shape_dist = st.uniform(shape, 0.0)
        if parameter_is_estimated(prior_parameters["scale"]):
            scale_dist = get_fixed_distribution(prior_parameters["scale"]["prior"])
        else:
            scale = float(prior_parameters["scale"]["value"])
            scale_dist = st.uniform(scale, 0.0)
        samples = []
        for i in range(n):
            shape = shape_dist.rvs(random_state = numpy_rng)
            scale = scale_dist.rvs(random_state = numpy_rng)
            x = st.gamma.rvs(shape, scale = scale, random_state = numpy_rng)
            samples.append(x)
    return samples

def distribution_is_fixed(prior_settings):
    fixed = True
    assert len(prior_settings) == 1
    prior_name = list(prior_settings.keys())[0]
    prior_parameters = prior_settings[prior_name]
    for param in prior_parameters.keys():
        if parameter_is_estimated(prior_parameters[param]):
            fixed = False
            break
    return fixed

def sample_distribution(numpy_rng, prior_settings, n = 100000):
    assert len(prior_settings) == 1
    prior_name = list(prior_settings.keys())[0]
    prior_parameters = prior_settings[prior_name]
    samples = None
    if distribution_is_fixed(prior_settings):
        dist = get_fixed_distribution(prior_settings)
        samples = [dist.rvs(random_state = numpy_rng) for _ in range(n)]
    elif prior_name == "uniform_distribution":
        samples = sample_uniform_distribution(numpy_rng, prior_parameters, n)
    elif prior_name == "exponential_distribution":
        samples = sample_exponential_distribution(numpy_rng, prior_parameters, n)
    elif prior_name == "gamma_distribution":
        samples = sample_gamma_distribution(numpy_rng, prior_parameters, n)
    else:
        raise Exception(
            f"python wrapper does not support sampling distribution: "
            f"{prior_name}\n"
        )
    return samples
