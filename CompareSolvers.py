import math
import pandas as pd
import InstanceGenerator as ig
import GurobiSolver as gs
import ColumnGenerationSolver as cgs
#%%
nProducts_list = [2, 3, 4, 5, 6, 8]
nAssortments_list = [2, 3, 4, 5, 10, 15, 20, 25]
summary = {}
instance_id = 0
print('-'*10, 'Comparisons starting', '-'*10)
for nProducts in nProducts_list:
    for nAssortments in nAssortments_list:
        if sum(int(math.factorial(nProducts)/(math.factorial(nProducts-i))) for i in range(1, nProducts+1)) >= nAssortments:
            # Generate instance
            instance_id += 1
            print('-'*10, 'Instance: %d with %d products and %d assortments' %(instance_id, nProducts, nAssortments), '-'*10)
            instance = ig.Instance(nProducts, nAssortments).generate_instance()
            # Solve using Gurobi
            gb_solve = gs.GurobiSolver(instance)
            gb_model = gb_solve.build_model()
            gb_model.optimize()
            gb_objVal, gb_time = gb_model.objVal, gb_model.Runtime
            # Solve using Column Generation
            cg_solve = cgs.ColGenSolver(instance)
            cg_mp = cg_solve.column_generation()
            cg_objVal, cg_time = cg_mp.objVal, cg_solve.Runtime
            # Compare results
            print('GB - Objective Value: %.6f - Time: %.6f with %d permutations' %(gb_objVal, gb_time, len(gb_solve.sigma)))
            print('CG - Objective Value: %.6f - Time: %.6f with %d permutations' %(cg_objVal, cg_time, len(cg_solve.sigma)))
            print('Difference in Objective Value (GB - CG): %.6f' %(gb_objVal-cg_objVal))
            summary[instance_id] = {'nProducts': nProducts, 'nAssortments': nAssortments, 'ObjValGB': gb_objVal, 'TimeGB': gb_time, 'nPermutationsGB': len(gb_solve.sigma), 'ObjValCG': cg_objVal, 'TimeCG': cg_time, 'nPermutationsCG': len(cg_solve.sigma), 'Gap': gb_objVal-cg_objVal}
print('-'*10, 'Comparisons finished', '-'*10)
# Save summary to csv
summary_df = pd.DataFrame.from_dict(summary, orient='index')
summary_df.to_csv('Summary.csv')
# Print summary of non-zero gap instances
non_zero_gap = [i for i in summary.keys() if abs(summary[i]['Gap']) > 1e-6]
print('Instances with non-zero gap:', non_zero_gap if non_zero_gap!=[] else 'None')