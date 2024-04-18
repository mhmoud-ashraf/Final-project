import math
import gurobipy as gp
from gurobipy import GRB
from itertools import permutations
import InstanceGenerator as ig
#%%
class GurobiSolver:
    def __init__ (self, instance, *sigma):
        self.instance = instance
        self.v = instance.v_train
        self.S = instance.assortments
        if sigma:
            self.K, self.sigma = sigma.keys(), sigma
        else:
            self.K, self.sigma = self.permutations_generator()
        self.A = self.mat_A_generator()
    
    def permutations_generator (self):
        sigma = {k: sigma_k for k,sigma_k in enumerate(permutations(self.instance.options),start=1)}
        return sigma.keys(), sigma
    
    def mat_A_generator (self):
        # Initialize A matrix
        A = {(i,m,k): 0 for m in self.S for i in self.S[m]+[0] for k in self.K}
        # Generate A matrix
        # Iterate over all permutations
        for k,sigma_k in self.sigma.items():
            # Iterate over all assortments
            for m,s_m in self.S.items():
                i, rank_j = None, float('inf')
                # Iterate over all options for each assortment
                for j in s_m+[0]:
                    # Find the option with the lowest rank in the permutation
                    if sigma_k.index(j) < rank_j:
                        i, rank_j = j, sigma_k.index(j)
                # Update A matrix such that A[i,m,k] = 1 if the customer chooses option i from set of options S_m+[0] in assortment m
                A[(i,m,k)] = 1
        return A
    
    def build_model (self):
        model = gp.Model('Assortment Optimization')
        
        # Decision Variables
        lmda = model.addVars(self.K, ub=1, vtype=GRB.CONTINUOUS, name='lmda')
        espilon_p = {(i,m): model.addVar(ub=1, vtype=GRB.CONTINUOUS, name='espilon_p[%d,%d]' %(i,m)) for m in self.S for i in self.S[m]+[0]}
        espilon_n = {(i,m): model.addVar(ub=1, vtype=GRB.CONTINUOUS, name='espilon_n[%d,%d]' %(i,m)) for m in self.S for i in self.S[m]+[0]}
        
        # Objective Function
        model.setObjective(gp.quicksum(espilon_p[(i,m)] + espilon_n[(i,m)] for m in self.S for i in self.S[m]+[0]), GRB.MINIMIZE)
        
        # Constraints
        constr1 = model.addConstrs((gp.quicksum(self.A[(i,m,k)]*lmda[k] for k in self.K) + espilon_p[(i,m)] - espilon_n[(i,m)] == self.v[(i,m)] for m in self.S for i in self.S[m]+[0]), name='constr1')
        constr2 = model.addConstr(gp.quicksum(lmda[k] for k in self.K) == 1, name='constr2')
        
        model.setParam('OutputFlag', 0)
        # model.setParam('Method', 1) # Use Dual Simplex
        model.update()
        # model.write('RMS.lp')
        return model
 #%%
if __name__ == '__main__':
    nProducts = 6
    nAssortments = 20
    instance = ig.Instance(nProducts, nAssortments).generate_instance()
    solver = GurobiSolver(instance)
    model = solver.build_model()
    model.optimize()
    print('Time:', model.Runtime)
    
    # print('Assortments:', instance.assortments)
    # print('v_train:', instance.v_train)
    # print('v_val:', instance.v_val)
    
    # print('Permutations:', solver.sigma)
    # print('A matrix')
    # print(solver.A)
    # for i, m, k in solver.A:
    #     print((i,m,k), solver.A[(i,m,k)])
    
    print('Objective Value - Train:', model.objVal)
    # lmda = {int(i.varName.split('[')[1].split(']')[0]): i.x for i in model.getVars() if 'lmda' in i.varName and i.x > 0}
    # print('Lambdas:', lmda)
    # print('Fitted permutations:', {k: solver.sigma[k] for k in lmda})
    
    # for m,S_m in solver.S.items():
    #     for i in S_m+[0]:
    #         print('Choice Probability - (%d,%d):' %(i,m), sum(solver.A[(i,m,k)]*lmda[k] for k in lmda))
    
    # objVal_val = 0
    # for m,S_m in solver.S.items():
    #     for i in solver.S[m]+[0]:
    #         objVal_val += abs(sum(solver.A[(i,m,k)]*lmda[k] for k in lmda) - instance.v_val[(i,m)])
    # print('Objective Value - Val:', objVal_val)
    # print('Difference between train and validation:', abs(model.objVal - objVal_val))