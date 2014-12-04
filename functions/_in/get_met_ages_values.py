# -*- coding: utf-8 -*-
"""
Created on Tue Dic 2 12:00:00 2014

@author: gabriel
"""

import re
from os import path, listdir
import numpy as np
from .._in import get_in_params as g
import girardi_isochs_format as gif


def match_ranges(met_vals_all, met_files, age_vals_all, z_range, a_range):
    '''
    Matches available metallicity and ages values with those stored in the
    ranges given to these two parameters.
    '''

    # Match metallicity values in ranges with values available.
    met_f_filter, met_values = [], []
    for i, met in enumerate(met_vals_all):
        # Store metallicity file only if it's inside the given range.
        if np.isclose(z_range, met, atol=0.0001).any():
            met_f_filter.append(met_files[i])
            met_values.append(met)

    # Match age values in ranges with values available.
    age_values = []
    for age in age_vals_all:
        # If age value falls inside the given range, store the value.
        if np.isclose(a_range, age, atol=0.01).any():
            age_values.append(round(age, 2))

    return met_f_filter, met_values, age_values


def get_ranges(par_ranges):
    '''
    Calculate parameter ranges to be used by the selected best fit method.
    '''

    # Copy to avoid modifiyng the real list.
    param_rs = list(par_ranges)

    # UPDATE max values.
    # Add a small value to each max value to ensure that the range is a bit
    # larger than the one between the real min and max values. This simplifies
    # the input of data and ensures that the GA algorithm won't fail when
    # encoding/decoding the floats into their binary representations.
    param_ranges = []
    for param in param_rs:
        # If min == max then set step value to be a very large number so
        # the GA will select the number of digits in the encoding binary
        # correctly.
        if param[0] == param[1]:
            param[2] = 1e6
        #
        # Differential to add to the max value.
        diff = min(param[1] / 100., param[2] / 2.)
        #
        # Store min, *UPDATED* max values and steps for all parameters.
        #
        # If diff is zero it means either the max or the step values are
        # zero for this parameter. In such case, use a very small value
        # instead to allow the ranges to be obtained and the 'Encode'
        # operator in the GA to work properly.
        param[1] = (param[1] + diff) if diff > 0. else 0.0001
        # Store all possible parameter values in array.
        param_ranges.append(np.arange(*param))

    return param_ranges, param_rs


def get_ages(met_file):
    '''
    Read all available ages in metallicity file.
    '''
    age_format = gif.age_f()

    # Open the metallicity file.
    with open(met_file, mode="r") as f_iso:
        regex = age_format  # Define regular exoresion.
        ages0 = re.findall(regex, f_iso.read())  # Find all instances.
        ages1 = np.asarray(map(float, ages0))  # Map to floats.
        ages2 = np.log10(ages1)  # Take log10
        isoch_a = np.around(ages2, 2)  # Round to 2 decimals.

    return isoch_a


def get_metals(iso_path):
    '''
    Read names of all metallicity files stored in isochrones path given and
    store them along with the z values they represent.
    '''

    metal_files = sorted(listdir(iso_path))
    # Iterate in order through all the metallicity files stored for the
    # selected set of isochrones.
    met_vals_all, met_files = [], []
    for met_file in metal_files:
        # Extract metallicity value from the name of the file.
        # *THE NAME OF THE FILE IS IMPORTANT*
        met_vals_all.append(float(met_file[:-4]))
        # Store full path to file.
        met_files.append(path.join(iso_path, met_file))

    return met_vals_all, met_files


def get_m_a_vls(iso_path):
    '''
    Run once to obtain the correct metallicities and ages to be used
    by the code.
    '''

    # Unpack.
    par_ranges = g.ps_params[1]

    # Read names of all metallicity files stored in isochrones path given.
    # I.e.: store all metallicity values available.
    met_vals_all, metal_files = get_metals(iso_path)

    # Read all ages from the first metallicity file defined.
    # *WE ASUME ALL METALLICITY FILES HAVE THE SAME NUMBER OF AGE VALUES*
    # (that's why we use the first metallicity file stored to obtain all
    # the age values)
    # I.e: store all age values available.
    age_vals_all = get_ages(metal_files[0])

    # Get parameters ranges stored in params_input.dat file.
    param_ranges, param_rs = get_ranges(par_ranges)

    # Match values in metallicity and age ranges with those available.
    z_range, a_range = param_ranges[:2]
    met_f_filter, met_values, age_values = match_ranges(met_vals_all,
        metal_files, age_vals_all, z_range, a_range)

    return param_ranges, param_rs, met_f_filter, met_values, age_values