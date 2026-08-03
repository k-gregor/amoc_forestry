import numpy as np
from scipy.optimize import linprog

LAMBDA = 0.00001

def get_mean_with_min_value(array, cutoff=100):
    """
    Calculates a mean value but "rounds down" values in excess of `cutoff` to the value of `cutoff`.
    Here's the reason. The following two species would have equal average performance (0.5), but obviously the second one is better for our case (a suitability of 50% is great).
    There is not much benefit of a suitability of 0.7 compared to 0.5, so we should not weight the 0.7 and the 0.9 so much. We consider 0.5 an optimal suitability already.
    0.9, 0.7, 0.5, 0.3, 0.1
    0.5, 0.5, 0.5, 0.5, 0.5
    >>> get_mean_with_min_value([0.9, 0.7, 0.5, 0.3, 0.1], cutoff=0.0)
    0.0
    >>> get_mean_with_min_value([0.9, 0.7, 0.5, 0.3, 0.1], cutoff=1.0)
    0.5
    >>> get_mean_with_min_value([0.9, 0.7, 0.5, 0.3, 0.1], cutoff=0.5)
    0.38
    >>> get_mean_with_min_value([90, 70, 50, 30, 10], cutoff=50)
    38.0
    """
    return np.mean(np.minimum(np.array(array), cutoff))


def optimize_gridcell(opt_scenarios, opt_species, row):

    n_scenarios = len(opt_scenarios)
    n_species = len(opt_species)
    
    # max_alpha min_sc P(alpha, sc)
    #        where P(alpha, sc) = SUM_sp alpha_sp P(sp, sc),   wo the suitability of a portfolio in scenario sc
    # z value represents min_sc P(alpha, sc)
    # minus value because linprog requires minimization objective, so max z <=> min -z
    # one alpha_sp for each species
    obj = [-1.0] + [0.0 for species in opt_species]

    # lhs <= rhs
    # z <= P(alpha, scenario) for all scenarios
    #       z is maximized, so that maximizes min_sc P(alpha, sc)
    # z - P(alpha, scenario) <= 0
    rhs_ineq = np.zeros((n_scenarios, 1))
    # for each row (scenario), put a 1 for z
    lhs_ineq = np.ones((n_scenarios, 1 + n_species))
    for scen_idx, scenario in enumerate(opt_scenarios):
        #gets all the values for the same scenario
        #sp1_sc1,sp1_sc2,sp1_sc3,...,sp2_sc1,sp2_sc2,...
        scenario_values_per_species = row.loc[[f'{species}-{scenario}' for species in opt_species]]
        # +1 because of the z value
        lhs_ineq[scen_idx, 1:] = -scenario_values_per_species

    for species_idx, species in enumerate(opt_species):
        species_prob_values = row.loc[[f'{species}-{scenario}' for scenario in opt_scenarios]]
        avg_species_prob = get_mean_with_min_value(species_prob_values, cutoff=100)
        obj[species_idx + 1] = -avg_species_prob * LAMBDA # +1 due to the z value, negative because we minimize, 0.0001 because the opt should focus on the worst case

    # z value >= 0, alpha_sp in [0, 1]
    # note, we keep the suitabilities in [0, 100] and not [0, 1.0] because of numerical issues
    bounds = [(0.0, 100.0)] + [(0.0, 1.0) for species in opt_species]

    # sum_sp alpha_sp = 1
    lhs_eq = np.ones((1, 1 + n_species))
    lhs_eq[0, 0] = 0.0 # z value
    rhs_eq = np.ones((1, 1))

    # note: this does not cover a special case when the probability for all species of a scenario is zero
    res = linprog(c=obj, A_ub=lhs_ineq, b_ub=rhs_ineq, A_eq=lhs_eq, b_eq=rhs_eq, bounds=bounds, method="highs")

    assert res.success == True, "Optimization did not succeed!"
    assert np.abs(np.sum(res.x[1:]) - 1.0) < 1e-5, "alpha does not sum up to 1!, value: " + str(np.sum(res.x[1:]))

    # Turning off presolve here! There is a bug in the solver, breaking on grid cell 6518211 (46.687361, 13.78736), when running with all SSPs plus present day data, and using cutoffs 20, 30, or 50.
    # It does work for cutoffs 10 and 100, though. Not using presolve makes it also work for any cutoff. So it must be a bug in the library, because in the end, the solution is feasible.
    res_int = linprog(c=obj, A_ub=lhs_ineq, b_ub=rhs_ineq, A_eq=lhs_eq, b_eq=rhs_eq, bounds=bounds, method="highs", integrality=[0] + [1 for species in opt_species], options={'presolve': False})

    assert res_int.success == True, "Integer optimization did not succeed!"
    assert np.abs(np.sum(res_int.x[1:]) - 1.0) < 1e-5, "alpha does not sum up to 1!, value: " + str(np.sum(res_int.x[1:]))

    return res, res_int



def run_optimization_and_combine_with_row_index(task):

    row_idx, scenarios, species_list, row = task
    result = optimize_gridcell(scenarios, species_list, row)
    return row_idx, result


def optimize_dataframe(df_final, opt_scenarios, opt_species, verbose=False):
    print('0')
    assert 'historical' not in opt_scenarios # we can optimize for SSPs and for present

    df_final = df_final.copy()

    df_final['opt_single_species'] = 0
    df_final['opt_single_species_min_prob'] = 0.0
    df_final['opt_portfolio'] = None
    df_final['opt_portfolio'] = df_final['opt_portfolio'].astype(object)
    df_final['opt_portfolio_min_prob'] = 0.0

    i = 0
    for row_idx, row in df_final.iterrows():

        if i % 1000 == 0 and verbose:
            print(i/len(df_final))
        i+=1

        opt_result = optimize_gridcell(opt_scenarios, opt_species, row)

        set_results_into_dataframe(df_final, opt_scenarios, opt_species, opt_result, row_idx)

    return df_final


def set_results_into_dataframe(df_final, opt_scenarios, opt_species, opt_result, row_idx):
    res, res_int = opt_result
    opt_portfolio = get_opt_portfolio_from_opt_result(res)

    # set portfolio results
    portfolio_avg_prob = 0.0
    portfolio_max_prob = 0.0
    for scenario in opt_scenarios:
        scenario_prob = 0.0
        for species_id, species in enumerate(opt_species):
            if species_id in opt_portfolio:
                scenario_prob += opt_portfolio[species_id] * df_final.loc[row_idx, species + '-' + scenario]
        portfolio_avg_prob += scenario_prob
        portfolio_max_prob = scenario_prob if scenario_prob > portfolio_max_prob else portfolio_max_prob
        df_final.loc[row_idx, 'opt_portfolio_prob_' + scenario] = scenario_prob
    df_final.loc[row_idx, 'opt_portfolio_min_prob'] = res.x[0]
    df_final.at[row_idx, 'opt_portfolio'] = opt_portfolio
    df_final.loc[row_idx, 'opt_portfolio_avg_prob'] = portfolio_avg_prob / len(opt_scenarios)
    df_final.loc[row_idx, 'opt_portfolio_max_prob'] = portfolio_max_prob
    # set single species results
    df_final.loc[row_idx, 'opt_single_species_min_prob'] = res_int.x[0]
    opt_species_id = np.argmax(res_int.x[1:])
    opt_species_name = opt_species[opt_species_id]

    opt_int_portfolio = list(get_opt_portfolio_from_opt_result(res_int).keys())
    assert(len(opt_int_portfolio) == 1), "Integer solution has more than one species: " + str(len(opt_int_portfolio)) + ', ' + str(df_final.loc[row_idx, ['y', 'x']])

    df_final.loc[row_idx, 'opt_single_species'] = opt_int_portfolio[0]
    single_species_avg_prob = 0.0
    single_species_max_prob = 0.0
    for scenario in opt_scenarios:
        single_species_prob_for_scenario = df_final.loc[row_idx, opt_species_name + '-' + scenario]
        single_species_avg_prob += single_species_prob_for_scenario
        single_species_max_prob = single_species_prob_for_scenario if single_species_prob_for_scenario > single_species_max_prob else single_species_max_prob
        df_final.loc[row_idx, 'opt_single_species_prob_' + scenario] = df_final.loc[
            row_idx, opt_species_name + '-' + scenario]
    df_final.loc[row_idx, 'opt_single_species_avg_prob'] = single_species_avg_prob / len(opt_scenarios)
    df_final.loc[row_idx, 'opt_single_species_max_prob'] = single_species_max_prob

TOLERANCE=1e-6
def get_opt_portfolio_from_opt_result(res):
    return {species: prob for species, prob in enumerate(res.x[1:]) if prob > TOLERANCE}


if __name__ == '__main__':
    pass
