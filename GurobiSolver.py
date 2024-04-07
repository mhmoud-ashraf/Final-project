import math
import gurobipy as gp
from gurobipy import GRB
import InstanceGenerator as ig
#%%
class GurobiSolver:
    def __init__ (self, instance):
        self.instance = instance
        self.v = instance.v_train
        self.I = instance.products
        self.M = instance.assortments.keys()
        self.K = instance.sigma.keys()
        self.A = self.mat_A_generator()
    
    def mat_A_generator (self):
        # Initialize A matrix
        A = {(i,m,k): 0 for i in self.I for m in self.M for k in self.K}
        sigma = self.instance.sigma
        assortments = self.instance.assortments
        # Generate A matrix
        for k, sigma_k in sigma.items():
            for i in sigma_k:
                for m, s_m in assortments.items():
                    j, arg_min = float('inf'), float('inf')
                    # Find the minimum index of j in s_m
                    for j in s_m:
                        if sigma_k.index(j) < arg_min:
                            j, arg_min = j, sigma_k.index(j)
                    if i == j:
                        A[(i,m,k)] = 1
        return A
    
    def build_model (self):
        model = gp.Model('Assortment Optimization')
        
        # Decision Variables
        lmda = model.addVars(self.K, ub=1, vtype=GRB.CONTINUOUS, name='lmda')
        espilon_p = model.addVars(self.I, self.M, ub=1, vtype=GRB.CONTINUOUS, name='espilon_p')
        espilon_n = model.addVars(self.I, self.M, ub=1, vtype=GRB.CONTINUOUS, name='espilon_n')
        
        # Objective Function
        model.setObjective(gp.quicksum(espilon_p[i,m] + espilon_n[i,m] for i in self.I for m in self.M), GRB.MINIMIZE)
        
        # Constraints
        constr1 = model.addConstrs(gp.quicksum(self.A[(i,m,k)]*lmda[k] for k in self.K) + espilon_p[i,m] - espilon_n[i,m] == self.v[(i,m)] for i in self.I for m in self.M)
        constr2 = model.addConstr(gp.quicksum(lmda[k] for k in self.K) == 1)
        
        model.setParam('OutputFlag', 0)
        model.update()
        
        return model
 #%%
if __name__ == '__main__':
    nProducts = 2
    nAssortments = 2
    instance = ig.Instance(nProducts, nAssortments).generate_instance()
    solver = GurobiSolver(instance)
    model = solver.build_model()
    model.optimize()
    
    # print('Assortments')
    # print(instance.assortments)
    # print()
    # print('Permutations')
    # print(instance.sigma)
    # print()
    # print('v_vals')
    # for i, m in instance.v_train:
    #     print((i, m), instance.v_train[(i, m)])
    # print()
    # print('A matrix')
    # for i, m, k in solver.A:
    #     print((i,m,k), solver.A[(i,m,k)])
    # print()
    print('Objective Value - Train:', model.objVal)
    # for v in model.getVars():
    #     print(v.varName, v.x)
    
    lmda = {int(i.varName.split('[')[1].split(']')[0]): i.x for i in model.getVars() if 'lmda' in i.varName}
    objVal_val = 0
    for i in solver.I:
        for m in solver.M:
            objVal_val += abs(sum(solver.A[(i,m,k)]*lmda[k] for k in lmda) - instance.v_val[(i,m)])
    print('Objective Value - Val:', objVal_val)
    print('Difference between train and validation:', abs(model.objVal - objVal_val))