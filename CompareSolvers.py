import math
from itertools import permutations
import pandas as pd
import InstanceGenerator as ig
import GurobiSolver as gs
import CG_SinglePricing as CGSP
import CG_MultiplePricing as CGMP
import OptColSelect as CGMPSub
#%%
# seed_list = [0, 42, 68, 84, 100]
nProducts_list = [2, 3, 4, 5, 6, 8]
nAssortments_list = [2, 3, 4, 5, 10, 15, 20, 25]
summary = {}
instance_id = 0

print('-'*10, 'Comparisons starting', '-'*10)

# for seed in seed_list:
#     gb_objVals, gb_times, gp_K = [], [], []
#     CGSP_objVals, CGSP_times, CGSP_K, CGSP_nCols = [], [], [], []
#     CGMP_objVals, CGMP_times, CGSP_K, CGMP_nCols = [], [], [], []
#     CGMPSub_objVals, CGMPSub_times, CGSP_K, CGMPSub_nCols = [], [], [], []
    
for nProducts in nProducts_list:
    # Generate all permutations of options
    sigma = {k: sigma_k for k,sigma_k in enumerate(permutations(range(nProducts+1)),start=1)}
    for nAssortments in nAssortments_list:
        if sum(int(math.factorial(nProducts)/(math.factorial(nProducts-i))) for i in range(1, nProducts+1)) >= nAssortments:
            # Generate instance
            instance_id += 1
            print('-'*10, 'Instance: %d with %d products and %d assortments' %(instance_id, nProducts, nAssortments), '-'*10)
            # instance = ig.Instance(nProducts, nAssortments, seed=seed).generate_instance()
            instance = ig.Instance(nProducts, nAssortments).generate_instance()
            
            # Solve using Gurobi
            gb_solve = gs.GurobiSolver(instance, sigma)
            gb_model = gb_solve.build_model()
            gb_model.optimize()
            gb_objVal, gb_time = gb_model.objVal, gb_model.Runtime
            print('GB -- ObjVal: %.6f - Time: %.6f with K: %d ' %(gb_objVal, gb_time, len(gb_solve.sigma)))
            
            # Solve using Column Generation - Single Pricing
            CGSP_solve = CGSP.ColGenSP(instance)
            CGSP_mp = CGSP_solve.CG_solve()
            CGSP_objVal, cg_time = CGSP_mp.objVal, CGSP_solve.Runtime
            print('CGSP -- ObjVal: %.6f - Time: %.6f with K: %d in %d iterations' %(CGSP_objVal, cg_time, len(CGSP_solve.sigma), len(CGSP_solve.sigma)))
            
            # Solve using Column Generation - Multiple Pricing = nPricing
            CGMP_solve = CGMP.ColGenMP(instance, nPricing=5) # add nPricing columns at each iteration
            CGMP_mp = CGMP_solve.CG_solve()
            CGMP_objVal, CGMP_time = CGMP_mp.objVal, CGMP_solve.Runtime
            print('CGMP -- ObjVal: %.6f - Time: %.6f with K: %d in %d iterations' %(CGMP_objVal, CGMP_time, len(CGMP_solve.sigma), CGMP_solve.iter))
            
            # Solve using Column Generation - Multiple Pricing = nPricing with optimal subset a col_penality
            CGMPSub_solve = CGMPSub.CGColSelect(instance, nPricing=5, new_col_penality=1e-3)
            CGMPSub_mp = CGMPSub_solve.CG_solve()
            CGMPSub_objVal, CGMPSub_time = CGMPSub_mp.objVal, CGMPSub_solve.Runtime
            print('CGMPSub -- ObjVal: %.6f - Time: %.6f with K: %d in %d iterations' %(CGMPSub_objVal, CGMPSub_time, len(CGMPSub_solve.sigma), CGMPSub_solve.iter))
            
            # Print difference in objectives
            print('Difference in ObjVal (GB-CGSP): %.6f' %(gb_objVal-CGSP_objVal))
            print('Difference in ObjVal (GB-CGMP): %.6f' %(gb_objVal-CGMP_objVal))
            print('Difference in ObjVal (GB-CGMPSub): %.6f' %(gb_objVal-CGMPSub_objVal))
            
            summary[instance_id] = {'N': nProducts, 'M': nAssortments, 
                                    'ObjVal(GB)': gb_objVal, 'ObjVal(CGSP)': CGSP_objVal, 'ObjVal(CGMP)': CGMP_objVal, 'ObjVal(CGMPSub)': CGMPSub_objVal, 
                                    'nCols(GB)': len(gb_solve.sigma), 'nCols(CGSP)': len(CGSP_solve.sigma), 'nCols(CGMP)': len(CGMP_solve.sigma), 'nCols(CGMPSub)': len(CGMPSub_solve.sigma), 
                                    'K(CGSP)': len(CGSP_solve.sigma), 'K(CGMP)': CGMP_solve.iter, 'K(CGMPSub)': CGMPSub_solve.iter, 
                                    'Time(GB)': gb_time, 'Time(CGSP)': cg_time, 'Time(CGMP)': CGMP_time, 'Time(CGMPSub)': CGMPSub_time, 
                                    'Gap(GB-CGSP)': gb_objVal-CGSP_objVal, 'Gap(GB-CGMP)': gb_objVal-CGMP_objVal, 'Gap(GB-CGMPSub)': gb_objVal-CGMPSub_objVal}

print('-'*10, 'Comparisons finished', '-'*10)

# Save summary to csv
summary_df = pd.DataFrame.from_dict(summary, orient='index')
summary_df.to_csv('Summary.csv', index_label = 'Instance')

# Print summary of non-zero gap instances
non_zero_gap = [i for i in summary.keys() if abs(summary[i]['Gap(GB-CGSP)']) > 1e-6 or abs(summary[i]['Gap(GB-CGMP)']) > 1e-6 or abs(summary[i]['Gap(GB-CGMPSub)']) > 1e-6]
print('Instances with non-zero gap:', non_zero_gap if non_zero_gap!=[] else 'None')