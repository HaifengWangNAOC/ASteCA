
import numpy as np
import obs_clust_prepare
import genetic_algorithm
import brute_force_algor
import bootstrap
from ..errors import error_round
from ..synth_clust import extin_coefs
from ..synth_clust import imf
from ..synth_clust import synth_cl_plot


def params_errors(ip_list, ga_params, err_lst, memb_prob_avrg_sort,
                  completeness, st_dist_mass, isoch_fit_params, cmd_sel,
                  e_max, best_fit_algor, N_b, lkl_method, bin_method,
                  bin_mass_ratio):
    '''
    Obtain errors for the fitted parameters.
    '''
    if best_fit_algor == 'brute':
        isoch_fit_errors = []
        # Assign errors as the largest step in each parameter.
        par_vals = ip_list[1]
        for pv in par_vals:
            # If any parameter has a single valued range, assign an error
            # of -1.
            if len(pv) > 1:
                # Find largest delta in this parameter used values.
                largest_delta = np.diff(pv).max()
                # Store the maximum value.
                isoch_fit_errors.append(largest_delta)
            else:
                isoch_fit_errors.append(-1.)

    elif best_fit_algor == 'genet':
        if N_b >= 2:
            # Call bootstrap function with resampling to get the uncertainty
            # in each parameter.
            isoch_fit_errors = bootstrap.main(
                ga_params, cmd_sel, e_max, err_lst, memb_prob_avrg_sort,
                completeness, ip_list, st_dist_mass, best_fit_algor, N_b,
                lkl_method, bin_method, bin_mass_ratio)
        else:
            print('Skipping bootstrap process.')
            # No error assignment.
            isoch_fit_errors = [-1.] * len(isoch_fit_params[0])

    return isoch_fit_errors


def main(clp, bf_flag, er_params, bf_params, IMF_name, m_high, bin_mr,
         ga_params, param_values, cmd_systs, all_syst_filters, filters, colors,
         theor_tracks, **kwargs):
    '''
    Perform a best fitting process to find the cluster's fundamental
    parameters.
    '''
    err_lst, memb_prob_avrg_sort, completeness = clp['err_lst'],\
        clp['memb_prob_avrg_sort'], clp['completeness']
    best_fit_algor, lkl_method, bin_method, N_b = bf_params
    e_max = er_params[1]

    # Check if algorithm should run.
    if bf_flag:

        print('Searching for optimal parameters.')

        obs_clust = obs_clust_prepare.main(
            memb_prob_avrg_sort, lkl_method, bin_method)
        # Store for plotting purposes.
        syn_b_edges = obs_clust[1] if lkl_method == 'dolphin' else []

        # Obtain extinction coefficients.
        ext_coefs = extin_coefs.main(
            cmd_systs, all_syst_filters, filters, colors)

        # Obtain mass distribution using the selected IMF. We run it once
        # because the array only depends on the IMF selected.
        st_dist_mass = imf.main(IMF_name, m_high)

        # Call algorithm to calculate the likelihoods for the set of
        # isochrones and return the best fitting parameters.
        if best_fit_algor == 'brute':

            print('Using Brute Force algorithm ({}).'.format(
                lkl_method + '; ' + bin_method if lkl_method == 'dolphin'
                else lkl_method))
            # Brute force algorithm.
            isoch_fit_params = brute_force_algor.main(
                lkl_method, e_max, bin_mr, err_lst, obs_clust, ext_coefs,
                completeness, param_values, theor_tracks, st_dist_mass)

        elif best_fit_algor == 'genet':

            print('Using Genetic Algorithm ({}).'.format(
                lkl_method + '; ' + bin_method if lkl_method == 'dolphin'
                else lkl_method))
            # Genetic algorithm.
            # Let the GA algor know this call comes from the main function
            # so it will print percentages to screen.
            flag_print_perc = True
            isoch_fit_params = genetic_algorithm.main(
                flag_print_perc, err_lst, obs_clust, ext_coefs, completeness,
                ip_list, st_dist_mass, ga_params, lkl_method, e_max, bin_mr)

        print("Best fit parameters obtained.")

        # Assign errors for each parameter.
        isoch_fit_errors = params_errors(
            ip_list, ga_params, err_lst, memb_prob_avrg_sort, completeness,
            st_dist_mass, isoch_fit_params, cmd_sel, e_max, best_fit_algor,
            N_b, lkl_method, bin_method, bin_mr)

        # Round errors to 1 significant digit and round params values
        # to the corresponding number of significant digits given by
        # the errors.
        isoch_fit_params[0], isoch_fit_errors = error_round.round_sig_fig(
            isoch_fit_params[0], isoch_fit_errors)

    else:
        # Pass empty lists to make_plots.
        print('Skipping parameters fitting process.')
        isoch_fit_params, isoch_fit_errors, syn_b_edges =\
            [[-1., -1., -1., -1., -1., -1.]], \
            [-1., -1., -1., -1., -1., -1.], []

    clp['isoch_fit_params'], clp['isoch_fit_errors'], clp['syn_b_edges'] =\
        isoch_fit_params, isoch_fit_errors, syn_b_edges
    return clp
