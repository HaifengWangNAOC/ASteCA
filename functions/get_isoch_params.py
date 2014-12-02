# -*- coding: utf-8 -*-
"""
Created on Thu Jan  9 15:08:39 2014

@author: gabriel
"""

import os
import re
from os.path import join
import numpy as np
import get_in_params as g
import girardi_isochs_format as gif
from cmd_phot_systs import phot_wavelengths as pw
from get_CCM_coefs import ccm_model as gcc


def get_mag_idx(mi, phot_params):
    '''
    Return index of magnitude in stored isochrones columns.
    '''
    # Start on 2 to account for the initial and actual mass columns.
    main_mag_idx = 2
    for sys in phot_params[2]:
        for mag in sys[1]:
            if mag == mi:
                # Index of magnitude in stored theoretical values obtained.
                # Get wavelength in inverse microns for this magnitude.
                mw = pw(sys[0], mag)
                # Get CCM coeficient for this magnitude.
                ccm_c = gcc(mw)
                return main_mag_idx, ccm_c
            else:
                main_mag_idx += 1


def get_mc_order(phot_params, isochs_interp):
    '''
    Order the magnitudes and colors in the same way as those stored in the
    input photometric data file.
    '''

    isoch_order, ccm_coefs = [], [[], []]
    for _met in isochs_interp:
        met = []
        for _isoch in _met:
            # Append masses and make room for mags and colors.
            isoch = [_isoch[0], _isoch[1], [], []]
            # Search and append ordered magnitudes.
            for m in phot_params[1][0]:
                # Return index of this mag as stored in phot_params[2]
                mi, ccm_i = get_mag_idx(m[1:], phot_params)
                isoch[2].append(_isoch[mi])
                ccm_coefs[0].append(ccm_i)
            # Search and append ordered colors.
            for c in phot_params[1][1]:
                # Return index of this mag as stored in phot_params[2]
                c1, c2 = c[1:].split('-')
                # Search for indexes of each magnitude in the color.
                m1, ccm_1 = get_mag_idx(c1, phot_params)
                m2, ccm_2 = get_mag_idx(c2, phot_params)
                # Append color.
                isoch[3].append((_isoch[m1] - _isoch[m2]))
                ccm_coefs[1].append((ccm_1 - ccm_2))
            met.append(isoch)
        isoch_order.append(met)

    return isoch_order, ccm_coefs


def interp_isoch(isoch_list):
    '''
    Interpolate extra points into the theoretical isochrones passed.
    '''
    N = 2000
    t = np.linspace(0, 1, N)

    isochs_interp = [[] for _ in isoch_list]
    # For each metallicity value.
    for i, met in enumerate(isoch_list):
        # For each age value (ie: isochrone)
        for isoch in met:
            # Interpolate all magnitudes defined.
            xp = np.linspace(0, 1, len(isoch[0]))
            # Store isochrone's interpolated values.
            isochs_interp[i].append(np.asarray([np.interp(t, xp, _)
                for _ in isoch]))

    # *** DELETE ****
    #isoch_inter = np.asarray([np.array(_) for _ in isochrone])

    return isochs_interp


def read_met_file(met_f, age_values, line_start, mass_i, mass_a, mags_idx,
    age_format, sys_idx):
    '''
    Read a given metallicity file and return the isochrones for the ages
    within the age range.
    '''

    # Initialize list that will hold all the isochrones for this
    # metallicity value.
    met_i = []

    # Open the metallicity file.
    with open(met_f, mode="r") as f_iso:

        # Initial empty list for masses and magnitudes.
        isoch_mas_mag = []
        # Initial value for age to avoid 'not defined' error.
        age = -99.

        # Iterate through each line in the file.
        for line in f_iso:

            # Identify beginning of a defined isochrone.
            if line.startswith(line_start):

                # Save stored values if these exist.
                # Skip first age for which the lists will be empty.
                if isoch_mas_mag:
                    # Store magnitudes and masses for this isochrone.
                    met_i.append(isoch_mas_mag)
                    # Reset list.
                    isoch_mas_mag = []

                # Read age value for this isochrone.
                age0 = re.findall(age_format, line)  # Find age in line.
                age = np.around(np.log10(float(age0[0])), 2)

            # If age value falls inside the given range, store the
            # isochrone's data.
            if age in age_values:

                # Save mag, color and mass values for each isochrone.
                if not line.startswith("#"):
                    # Split line.
                    reader = line.split()
                    # Only save masses for one photometric system since
                    # its values are equivalent for the same metallicty and
                    # age across photometric systems.
                    if sys_idx == 0:
                        # Store masses.
                        isoch_mas_mag.append(float(reader[mass_i]))
                        isoch_mas_mag.append(float(reader[mass_a]))
                    # Store defined magnitudes.
                    for mag_i in mags_idx:
                        isoch_mas_mag.append(float(reader[mag_i]))

        # Save the last isochrone when EOF is reached.
        else:
            # If list is not empty.
            if isoch_mas_mag:
                # Store masses and magnitudes for this isochrone.
                met_i.append(isoch_mas_mag)

    # Number of columns stored. Add 2 to account for the 2 masses *only*
    # if this is the first run, ie: for the first photom system. The rest
    # of the phot systems (if more are used) do not have their masses read
    # since mass values are equivalent for equal metallicities and ages.
    n_cols = 2 + len(mags_idx) if sys_idx == 0 else len(mags_idx)
    # Split read values so that the resulting list looks like this:
    #
    # metal_isochs = [age_1, age_2, ..., age_N]
    # age_i = [mass_i, mass_a, mag_1, mag_2, ..., _mag_M]
    #
    # Each mass_x and mag_x are lists that hold all theoretical values
    # read from the metallicity file for that given age.
    metal_isochs = []
    for a_i in range(len(age_values)):
        met_i0 = np.split(np.asarray(met_i[a_i]), len(met_i[a_i]) / n_cols)
        metal_isochs.append(zip(*met_i0))

    return metal_isochs


def get_isochs(mypath, met_f_filter, age_values, syst, sys_idx):
    '''
    Stores the available isochrones of different metallicities and
    ages, according to the ranges given to these parameters.
    '''

    # Read line start format and columns indexes for the selected set of
    # Girardi isochrones.
    line_start, mass_i, mass_a, mags_idx = gif.i_format(syst)
    age_format = gif.age_f()

    # Lists that store the masses and magnitudes of each isochrone.
    # isoch_list = [metal_1, ..., metal_M]
    # metal_i = [isoch_i1, ..., isoch_iN]
    # isoch_ij = [mass_i, mass_a, mag1, mag2, ..., magM]
    # isoch_list[i][j] --> i: metallicity index ; j: age index
    isoch_list = []

    # Iterate in order through all the metallicity files stored for the
    # selected set of isochrones.
    for met_file in met_f_filter:

        metal_isoch = read_met_file(met_file, age_values, line_start, mass_i,
            mass_a, mags_idx, age_format, sys_idx)

        # Store list holding all the isochrones with the same metallicity
        # in the final isochrone list.
        isoch_list.append(metal_isoch)

    return isoch_list


def match_ranges(met_vals_all, met_files, age_vals_all, z_range, a_range):
    '''
    Matches available matallicity and ages values with those stored in the
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

    metal_files = sorted(os.listdir(iso_path))
    # Iterate in order through all the metallicity files stored for the
    # selected set of isochrones.
    met_vals_all, met_files = [], []
    for met_file in metal_files:
        # Extract metallicity value from the name of the file.
        # *THE NAME OF THE FILE IS IMPORTANT*
        met_vals_all.append(float(met_file[:-4]))
        # Store full path to file.
        met_files.append(join(iso_path, met_file))

    return met_vals_all, met_files


def get_met_age_values(iso_path):
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


def ip(mypath, phot_params):
    '''
    Read isochrones and parameters if best fit function is set to run.
    '''

    ip_list = []
    # Only read files of best fit method is set to run.
    bf_flag = g.bf_params[0]
    if bf_flag is True:

        # Obtain allowed metallicities and ages. Use the first photometric
        # system defined.
        # *WE ASUME ALL PHOTOMETRIC SYSTEMS CONTAIN THE SAME NUMBER OF
        # METALLICITY FILES*
        iso_select = g.ps_params[0]
        iso_path = join(mypath + '/isochrones/' + iso_select + '_' +
            phot_params[2][0][0])
        param_ranges, param_rs, met_f_filter, met_values, age_values = \
        get_met_age_values(iso_path)

        print '\n', 'met_vals', met_values
        print 'age_vals', age_values, '\n'

        print 'Interpolating all isochrones for each photometric system.\n'
        # Get isochrones for every photometric system defined.
        isochs_interp = []
        for sys_idx, syst in enumerate(phot_params[2]):

        # *WE ASUME ALL ISOCHRONES OF EQUAL METALLICITY HAVE THE SAME NUMBER
        # OF MASS VALUES ACROSS PHOTOMETRIC SYSTEMS*

            # Get isochrones and their parameter values.
            isoch_list = get_isochs(mypath, met_f_filter, age_values, syst,
                sys_idx)
            # isoch_list = [met_1, met_2, ..., met_P]

            # Interpolate extra points into all isochrones.
            isochs_interp0 = interp_isoch(isoch_list)
            # For the first photometric system, store the masses that were
            # read.
            if sys_idx == 0:
                isochs_interp.extend(isochs_interp0)
            # For the rest of the systems, just append its magnitudes for
            # each isochrone since we assume the masses are equal.
            else:
                for m_i, _m in enumerate(isochs_interp0):
                    for a_i, _a in enumerate(_m):
                        for mag in _a:
                            isochs_interp[m_i][a_i] = np.append(
                                isochs_interp[m_i][a_i], [mag], 0)

        # isochs_interp = [metal_1, ..., metal_P]
        # metal_i =[age_i, ..., age_Q]
        # age_i = [mass_i, mass_a, mag1, ..., mag_N]
        #
        # mag_1, ..., mag_N are the magnitudes defined in *all* the photom
        # systems, stored in the order presented in photom_params[2]

        # Generate colors (if any) and order magnitudes/colors to match the
        # order of the input photometric data.
        isochs_order, ccm_coefs = get_mc_order(phot_params, isochs_interp)
        # isochs_order = [metal_1, ..., metal_P]
        # metal_i =[age_i, ..., age_Q]
        # age_i = [mass_i, mass_a, [mag1, ..., magN], [col1, ..., colM]

        # Pack params.
        param_values = [met_values, age_values] + param_ranges[2:]
        ip_list = [isochs_order, ccm_coefs, param_values, param_rs]

        iso_ver = {'10': '1.0', '11': '1.1', '12': '1.2S'}
        print ("PARSEC v{} theoretical isochrones read,".format(
            iso_ver[iso_select[-2:]]))
        lens = [len(_) for _ in param_values]
        total = reduce(lambda x, y: x * y, lens, 1)
        print ("interpolated and stored:\n"
        "  {} metallicity values (z),\n"
        "  {} age values (per z),\n"
        "  {} reddening values,\n"
        "  {} distance values,\n"
        "  {} mass values,\n"
        "  {} binary fraction values.".format(*lens))
        print "  = {:.1e} approx total models.".format(total)

    return ip_list