import math
from itertools import permutations
import pandas as pd
import InstanceGenerator as ig
import GurobiSolver as gs
import ColumnGenerationSolver as cgs
import CG_MultiplePricingSols as mpcg
#%%
nProducts_list = [2, 3, 4, 5, 6, 8]
nAssortments_list = [2, 3, 4, 5, 10, 15, 20, 25]
summary = {}
instance_id = 0
print('-'*10, 'Comparisons starting', '-'*10)
for nProducts in nProducts_list:
    # Generate all permutations of options
    sigma = {k: sigma_k for k,sigma_k in enumerate(permutations(range(nProducts+1)),start=1)}
    for nAssortments in nAssortments_list:
        if sum(int(math.factorial(nProducts)/(math.factorial(nProducts-i))) for i in range(1, nProducts+1)) >= nAssortments:
            # Generate instance
            instance_id += 1
            print('-'*10, 'Instance: %d with %d products and %d assortments' %(instance_id, nProducts, nAssortments), '-'*10)
            instance = ig.Instance(nProducts, nAssortments).generate_instance()
            # Solve using Gurobi
            gb_solve = gs.GurobiSolver(instance, sigma)
            gb_model = gb_solve.build_model()
            gb_model.optimize()
            gb_objVal, gb_time = gb_model.objVal, gb_model.Runtime
            print('GB - Objective Value: %.6f - Time: %.6f with %d permutations' %(gb_objVal, gb_time, len(gb_solve.sigma)))
            # Solve using Column Generation - Single Pricing
            cg_solve = cgs.ColGenSolver(instance)
            cg_mp = cg_solve.column_generation()
            cg_objVal, cg_time = cg_mp.objVal, cg_solve.Runtime
            print('SP_CG - Objective Value: %.6f - Time: %.6f with %d permutations in %d iterations' %(cg_objVal, cg_time, len(cg_solve.sigma), len(cg_solve.sigma)))
            # Solve using Column Generation - Multiple Pricing
            mpcg_solve = mpcg.MultiplePricingCG(instance)
            mpcg_mp = mpcg_solve.column_generation()
            mpcg_objVal, mpcg_time = mpcg_mp.objVal, mpcg_solve.Runtime
            print('MP_CG - Objective Value: %.6f - Time: %.6f with %d permutations in %d iterations' %(mpcg_objVal, mpcg_time, len(mpcg_solve.sigma), mpcg_solve.iter))
            # Print difference in objectives
            print('Difference in Objective Value (GB - SP_CG): %.6f' %(gb_objVal-cg_objVal))
            print('Difference in Objective Value (GB - MP_CG): %.6f' %(gb_objVal-mpcg_objVal))
            summary[instance_id] = {'nProducts': nProducts, 'nAssortments': nAssortments, 'ObjValGB': gb_objVal, 'TimeGB': gb_time, 'nPermutationsGB': len(gb_solve.sigma), 'ObjValCG-SP': cg_objVal, 'TimeCG-SP': cg_time, 'nPermutationsCG-SP': len(cg_solve.sigma), 'nItersCG-SP': len(cg_solve.sigma), 'ObjValCG-MP': mpcg_objVal, 'TimeCG-MP': mpcg_time, 'nPermutationsCG-MP': len(mpcg_solve.sigma), 'nItersCG-MP': mpcg_solve.iter, 'GapGB-SP': gb_objVal-cg_objVal, 'GapGB-MP': gb_objVal-mpcg_objVal}
print('-'*10, 'Comparisons finished', '-'*10)
# Save summary to csv
summary_df = pd.DataFrame.from_dict(summary, orient='index')
summary_df.to_csv('Summary.csv', index_label = 'Instance')
# Print summary of non-zero gap instances
non_zero_gap = [i for i in summary.keys() if abs(summary[i]['GapGB-SP']) > 1e-6 or abs(summary[i]['GapGB-MP']) > 1e-6]
print('Instances with non-zero gap:', non_zero_gap if non_zero_gap!=[] else 'None')