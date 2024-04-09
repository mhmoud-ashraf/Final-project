import math
import gurobipy as gp
from gurobipy import GRB
import InstanceGenerator as ig
#%%
class ColGenSolver:
    def __init__ (self, instance):
        self.instance = instance
        self.v = instance.v_train
        self.I = instance.products
        self.S = instance.assortments
        self.M = instance.assortments.keys()
        self.K = [0]
        self.A_init = {(i,m,k): 0 for i in self.I for m in self.M for k in self.K}
        self.A = {}
        self.sigma = {}
    
    def build_mp (self, A):
        model = gp.Model('Assortment Optimization - RMS')
        model.setParam('OutputFlag', 0)
        
        # Decision Variables
        lmda = model.addVars(self.K, ub=1, vtype=GRB.CONTINUOUS, name='lmda')
        espilon_p = {(i,m): model.addVar(ub=1, vtype=GRB.CONTINUOUS, name='espilon_p[%d,%d]' %(i,m)) for m in self.M for i in self.S[m]}
        espilon_n = {(i,m): model.addVar(ub=1, vtype=GRB.CONTINUOUS, name='espilon_n[%d,%d]' %(i,m)) for m in self.M for i in self.S[m]}
        
        # Objective Function
        model.setObjective(gp.quicksum(espilon_p[i,m] + espilon_n[i,m] for m in self.M for i in self.S[m]), GRB.MINIMIZE)
        
        # Constraints
        constr1 = model.addConstrs((gp.quicksum(A[(i,m,k)]*lmda[k] for k in self.K) + espilon_p[i,m] - espilon_n[i,m] == self.v[(i,m)] for m in self.M for i in self.S[m]), name='constr1')
        constr2 = model.addConstr(gp.quicksum(lmda[k] for k in self.K) == 1, name='constr2')
        
        model.setParam('OutputFlag', 0)
        model.update()
        return model
    
    def build_sp (self, alpha, nu):
        model = gp.Model('Assortment Optimization - SP')
        model.setParam('OutputFlag', 0)
        
        # Decision Variables
        a = {(i,m): model.addVar(vtype=GRB.BINARY, name='a[%d,%d]' %(i,m)) for m in self.M for i in self.S[m]}
        z = {(i,j): model.addVar(vtype=GRB.BINARY, name='z[%d,%d]' %(i,j)) for i in self.I for j in self.I if i!= j}
        
        # Objective Function
        model.setObjective(gp.quicksum(alpha[(i,m)]*a[i,m] for m in self.M for i in self.S[m]) - nu[1], GRB.MAXIMIZE)
        
        # Constraints
        constr1 = model.addConstrs((gp.quicksum(a[i,m] for i in self.S[m]) == 1 for m in self.S), name='constr1')
        constr2 = model.addConstrs((a[i,m] <= z[i,j] for m in self.M for i in self.S[m] for j in self.S[m] if i!=j), name='constr2')
        constr3 = model.addConstrs((z[i,j] + z[j,i] == 1 for j in self.I for i in self.I if i!=j), name='constr3')
        constr4 = model.addConstrs((z[i,j] + z[j,k] - 1 <= z[i,k] for i in self.I for j in self.I for k in self.I if i!=j and i!=k and j!=k), name='constr4')
        
        model.update()
        return model
    
    def dual_vars (self, mp):
        alpha = {}
        for c in mp.getConstrs():
            if 'constr1' in c.ConstrName:
                m, i = tuple(c.ConstrName.split('[')[1].split(']')[0].split(','))
                alpha[(int(i),int(m))] = c.pi
        nu = {1: c.pi for c in mp.getConstrs() if 'constr2' in c.ConstrName}
        return alpha, nu
    
    def subproblem_primal_vars (self, sp):
        a, z = {}, {}
        for var in sp.getVars():
            idx, val = var.varName.split('[')[1].split(']')[0], var.x
            if 'a' in var.varName:
                a[(int(idx.split(',')[0]), int(idx.split(',')[-1]))] = int(val)
            if 'z' in var.varName:
                z[(int(idx.split(',')[0]), int(idx.split(',')[-1]))] = int(val)
        return a, z
    def column_generation(self, gap=1e-2):
        objVal_history = {}
        # Solve Restricted Master Problem
        mp = self.build_mp(self.A_init)
        mp.optimize()
        objVal_history[self.K[-1]] = mp.objVal
        # Obtain dual variables
        alpha, nu = self.dual_vars(mp)
        # Solve Subproblem
        sp = self.build_sp(alpha, nu)
        sp.optimize()
        # Obtain subproblem primal variables values
        a, z = self.subproblem_primal_vars(sp)
        
        # Iteratively solve Restricted Master Problem and Subproblem
        while sum(alpha[(i,m)]*a[(i,m)] for m in self.M for i in self.S[m]) + nu[1] > 0:
            # Update K
            self.K = range(1, self.K[-1]+1+1)
            # Obtain permutation for new column
            sigma_k = dict(sorted({i: sum(z[(j,i)] for j in self.I if i!=j) for i in self.I}.items(), key=lambda item: item[1]))
            self.sigma[self.K[-1]] = tuple(sigma_k.keys())
            # Update A matrix
            for i,m in a:
                self.A[(i,m,self.K[-1])] = a[(i,m)]
            # Solve Restricted Master Problem
            mp = self.build_mp(self.A)
            mp.optimize()
            objVal_history[self.K[-1]] = mp.objVal
            # Obtain dual variables
            alpha, nu = self.dual_vars(mp)
            # Solve Subproblem
            sp = self.build_sp(alpha, nu)
            sp.optimize()
            a, z = self.subproblem_primal_vars(sp)
        
        # Solve Restricted Master Problem
        mp = self.build_mp(self.A)
        mp.optimize()
        return objVal_history, self.sigma, mp
 #%%
if __name__ == '__main__':
    nProducts = 5
    nAssortments = 4
    instance = ig.Instance(nProducts, nAssortments).generate_instance()
    solver = ColGenSolver(instance)
    objVal_history, sigma, mp = solver.column_generation()
    
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
    print('Objective Value - Train:', mp.objVal)
    # for v in model.getVars():
    #     print(v.varName, v.x)
    
    lmda = {int(i.varName.split('[')[1].split(']')[0]): i.x for i in mp.getVars() if 'lmda' in i.varName and i.x > 0}
    objVal_val = 0
    for m in solver.M:
        for i in solver.S[m]:
            objVal_val += abs(sum(solver.A[(i,m,k)]*lmda[k] for k in lmda) - instance.v_val[(i,m)])
    print('Objective Value - Val:', objVal_val)
    print('Difference between train and validation:', abs(mp.objVal - objVal_val))
    
    print('Fitted permutations:', [instance.sigma[k] for k in lmda])