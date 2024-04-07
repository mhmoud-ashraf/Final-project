import math
import gurobipy as gp
from gurobipy import GRB
import InstanceGenerator as ig
#%%
class Solver:
    def __init__ (self, instance):
        self.instance = instance
        self.K = instance.sigma.keys()
        self.I = range(instance.nProducts+1)
        self.M = range(1, instance.nAssortments+1)
        self.A = instance.A
        self.v_train = instance.v_train
        self.v_val = instance.v_val
    
    def build_model (self):
        model = gp.Model('Assortment Optimization')
        
        # Decision Variables
        lmda = model.addVars(self.K, ub=1, vtype=GRB.CONTINUOUS, name='lmda')
        espilon_p = model.addVars(self.I, self.M, ub=1, vtype=GRB.CONTINUOUS, name='espilon_p')
        espilon_n = model.addVars(self.I, self.M, ub=1, vtype=GRB.CONTINUOUS, name='espilon_n')
        
        # Objective Function
        model.setObjective(gp.quicksum(espilon_p[i,m] + espilon_n[i,m] for i in self.I for m in self.M), GRB.MINIMIZE)
        
        # Constraints
        constr1 = model.addConstrs(gp.quicksum(self.A[(i,m,k)]*lmda[k] for k in self.K) + espilon_p[i,m] - espilon_n[i,m] == self.v_train[(i,m)] for i in self.I for m in self.M)
        constr2 = model.addConstr(gp.quicksum(lmda[k] for k in self.K) == 1)
        
        model.setParam('OutputFlag', 0)
        model.update()
        
        return model
 #%%
if __name__ == '__main__':
    nProducts = 2
    nAssortments = 2
    instance = ig.Instance(nProducts, nAssortments).generate_instance()
    solver = Solver(instance)
    model = solver.build_model()
    model.optimize()
    
    # print('Assortments')
    # print(instance.assortments)
    # print()
    # print('Permutations')
    # print(instance.sigma)
    # print()
    # print('A matrix')
    # for i, m, k in instance.A:
    #     print((i, m, k), instance.A[(i, m, k)])
    # print()
    # print('v_vals')
    # for i, m in instance.v_train:
    #     print((i, m), instance.v_train[(i, m)])
    # print()
    print('Objective Value - Train:', model.objVal)
    # for v in model.getVars():
    #     print(v.varName, v.x)
    
    lmda = {int(i.varName.split('[')[1].split(']')[0]): i.x for i in model.getVars() if 'lmda' in i.varName}
    objVal_val = 0
    for i in range(instance.nProducts+1):
        for m in range(1, instance.nAssortments+1):
            objVal_val += abs(sum(instance.A[(i,m,k)]*lmda[k] for k in lmda) - instance.v_val[(i,m)])
    print('Objective Value - Val:', objVal_val)
    print('Difference:', abs(model.objVal - objVal_val))