"""
Program Name: event_equalize.py
"""

import itertools

import numpy as np
import pandas as pd

__author__ = 'Tatiana Burek'
__version__ = '0.1.0'
__email__ = 'met_help@ucar.edu'


def event_equalize(series_data, indy_var, indy_vals, series_var_vals, fix_vars,
                   fix_vals_permuted, equalize_by_indep, multi):
    """Performs event equalisation.

    event_equalize assumes that the input series_data contains data indexed by fcst_valid_beg,
    series values and the independent variable values.  It builds a new dataframe which
    contains the same data except for records that don't have corresponding fcst_valid_beg
    values in each other series record with the same independent variable value.
    For example, if the series_a has data valid at 20111010_000000 for F12 and series_b does not,
    the series_a record is removed.

    Args:
        series_data: data frame containing the records to equalize, including fcst_valid_beg, series
                values and independent variable values
        indy_var: name of the independent variable
        indy_vals: independent variable values to equalize over
                - not used. Keep for now for the consistency with R function
        series_var_vals: series variable names and values
        fix_vars: name of the fixed variable
        fix_vals_permuted:  fixed variable values to equalize over
        equalize_by_indep:  include or not the independent variable to EE
        multi: FALSE for normal event equalization, TRUE for equalization of mulitple events
                at each combination of fcst_valid_beg, series values and independent value
                - for example with MODE objects
    Returns:
        A data frame that contains equalized records
    """
    warning_detected = "WARNING: eventEqualize() detected non-unique events for {}" \
                       " using [fcst_valid_beg,fcst_lead)]"
    warning_discarding = "WARNING: discarding series member with case {} for {}"
    warning_remove = "WARNING: event equalization removed {} rows"

    column_names = list(series_data)
    exception_columns = ["fcst_valid_beg", 'fcst_lead', 'fcst_valid', 'fcst_init', 'fcst_init_beg']
    if isinstance(fix_vars, str):
        fix_vars = [fix_vars]

    if 'fcst_valid_beg' in column_names:
        series_data['equalize'] = series_data["fcst_valid_beg"].astype(str) \
                                  + ' ' + series_data["fcst_lead"].astype(str)
    elif 'fcst_valid' in column_names:
        series_data['equalize'] = series_data["fcst_valid"].astype(str) + ' ' \
                                  + series_data["fcst_lead"].astype(str)

    # add independent variable if needed
    if equalize_by_indep and not indy_var and indy_var not in exception_columns:
        series_data['equalize'] = series_data['equalize'].astype(str) + " " \
                                  + series_data[indy_var].astype(str)

    vars_for_ee = dict()

    # add series variables
    for series_var, series_vals in series_var_vals.items():
        if series_var not in exception_columns:
            series_vals_no_groups = []
            if isinstance(series_vals, str):
                series_vals = [series_vals]
            for series_val in series_vals:
                actual_vals = series_val.split(',')
                series_vals_no_groups.extend(actual_vals)
            vars_for_ee[series_var] = series_vals_no_groups

    # add fixed variables if present
    if fix_vars:
        for var_for_ee_ind, fix_var in enumerate(fix_vars):
            if fix_var not in exception_columns:
                vals = fix_vals_permuted[var_for_ee_ind]
                if isinstance(vals, str):
                    vals = [vals]
                else:
                    vars_for_ee[fix_var] = vals

    # create a list of permutations representing the all variables for EE
    vars_for_ee_permuted = list(itertools.product(*vars_for_ee.values()))

    equalization_cases = []

    # for each permutation
    for permutation_index, permutation in enumerate(vars_for_ee_permuted):
        permutation_data = series_data.copy()
        for var_for_ee_ind, var_for_ee in enumerate(list(vars_for_ee)):
            if represents_int(permutation[var_for_ee_ind]):
                permutation_data = permutation_data[permutation_data[var_for_ee]
                                                    == int(permutation[var_for_ee_ind])]
            else:
                permutation_data = permutation_data[permutation_data[var_for_ee]
                                                    == permutation[var_for_ee_ind]]

        # if the list contains repetitive values, show a warning
        if not multi and len(permutation_data['equalize']) \
                != len(set(permutation_data['equalize'])):
            print(warning_detected.format(permutation))

        if permutation_index == 0:
            # init the equalization list
            equalization_cases = permutation_data['equalize']
        else:
            # if there is an equalization list, equalize the current series data

            # find indexes of common cases that are on the current cases list
            common_cases_ind = \
                pd.Series(equalization_cases, dtype=np.str).isin(set(permutation_data['equalize']))

            # identify discarded cases for this permutation
            discarded_cases = equalization_cases[~common_cases_ind]

            # add cases that are in current permutation
            # but not in the common cases and add them to the discarded list
            permutation_cases_not_in_common_cases_ind = \
                pd.Series(permutation_data['equalize'], dtype=np.str).isin(equalization_cases)
            permutation_cases_not_in_common_cases = \
                permutation_data['equalize'][~permutation_cases_not_in_common_cases_ind]

            discarded_cases.append(permutation_cases_not_in_common_cases)
            # report the discarded records
            for discarded_case in discarded_cases:
                print(warning_discarding.format(discarded_case, permutation))

            # update the equalization list by removing records
            equalization_cases = equalization_cases[common_cases_ind]

    # remove data with discarded cases from the main frame
    equalization_cases_ind = \
        pd.Series(series_data['equalize'], dtype=np.str).isin(equalization_cases)
    series_data_ee = series_data[equalization_cases_ind]

    if len(series_data_ee) != len(series_data):
        print(warning_remove.format(len(series_data) - len(series_data_ee)))

    return series_data_ee


def represents_int(possible_int):
    """Checks if the value is integer.

     Args:
         possible_int: value to check

    Returns:
        True - if the input value is an integer
        False - if the input value is not an integer
    """
    return isinstance(possible_int, int)