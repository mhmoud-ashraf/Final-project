import time
import gurobipy as gp
from gurobipy import GRB
import InstanceGenerator as ig
#%%
class ColGenSolver:
    def __init__ (self, instance):
        self.instance = instance
        self.v = instance.v_train
        self.S = instance.assortments
        self.I = instance.options
        self.S = instance.assortments
        self.K, self.sigma = [0], {}
        self.A_init = {(i,m,k): 0 for m in self.S for i in self.S[m]+[0] for k in self.K}
        self.A = {}
        self.objVal_history = {}
        self.Runtime = 0
        self.P = len(self.v)
        
    def build_mp (self, A):
        model = gp.Model('Assortment Optimization - RMP')
        
        # Decision Variables
        lmda = model.addVars(self.K, ub=1, vtype=GRB.CONTINUOUS, name='lmda')
        espilon_p = {(i,m): model.addVar(ub=1, vtype=GRB.CONTINUOUS, name='espilon_p[%d,%d]' %(i,m)) for m in self.S for i in self.S[m]+[0]}
        espilon_n = {(i,m): model.addVar(ub=1, vtype=GRB.CONTINUOUS, name='espilon_n[%d,%d]' %(i,m)) for m in self.S for i in self.S[m]+[0]}
        
        # Objective Function
        model.setObjective(gp.quicksum(espilon_p[(i,m)] + espilon_n[(i,m)] for m in self.S for i in self.S[m]+[0]), GRB.MINIMIZE)
        
         # Constraints
        constr1 = model.addConstrs((gp.quicksum(A[(i,m,k)]*lmda[k] for k in self.K) + espilon_p[(i,m)] - espilon_n[(i,m)] == self.v[(i,m)] for m in self.S for i in self.S[m]+[0]), name='constr1')
        constr2 = model.addConstr(gp.quicksum(lmda[k] for k in self.K) == 1, name='constr2')
        
        model.setParam('OutputFlag', 0)
        # model.setParam('Method', 1) # Use Dual Simplex
        model.update()
        # model.write('RMS_{%s}.lp'%self.K[-1])
        return model
    
    def build_sp (self, alpha, nu):
        model = gp.Model('Assortment Optimization - SP')
        
        # Decision Variables
        a = {(i,m): model.addVar(vtype=GRB.BINARY, name='a[%d,%d]' %(i,m)) for m in self.S for i in self.S[m]+[0]}
        z = {(i,j): model.addVar(vtype=GRB.BINARY, name='z[%d,%d]' %(i,j)) for i in self.I for j in self.I if i!= j}
        
        # Objective Function
        model.setObjective(gp.quicksum(alpha[(i,m)]*a[(i,m)] for m in self.S for i in self.S[m]+[0]) + nu[1], GRB.MAXIMIZE)
        
        # Constraints
        constr1 = model.addConstrs((gp.quicksum(a[(i,m)] for i in self.S[m]+[0]) == 1 for m in self.S), name='constr1')
        constr2 = model.addConstrs((a[(i,m)] <= z[(i,j)] for m in self.S for i in self.S[m]+[0] for j in self.S[m]+[0] if i!=j), name='constr2')
        constr3 = model.addConstrs((z[(i,j)] + z[(j,i)] == 1 for j in self.I for i in self.I if i!=j), name='constr3')
        constr4 = model.addConstrs((z[(i,j)] + z[(j,k)] - 1 <= z[i,k] for i in self.I for j in self.I for k in self.I if i!=j and i!=k and j!=k), name='constr4')
        
        model.setParam('OutputFlag', 0)
        # model.setParam('Method', 1) # Use Dual Simplex
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
    
    def column_generation(self, gap=1e-4):
        start = time.time() # Start timer
        # Solve Restricted Master Problem
        mp = self.build_mp(self.A_init)
        mp.optimize()
        self.objVal_history[self.K[-1]] = mp.objVal
        # Obtain dual variables
        alpha, nu = self.dual_vars(mp)
        # Solve Subproblem
        sp = self.build_sp(alpha, nu)
        sp.optimize()
        # Obtain subproblem primal variables values
        a, z = self.subproblem_primal_vars(sp)
        
        # Iteratively solve Restricted Master Problem and Subproblem
        while sum(alpha[(i,m)]*a[(i,m)] for m in self.S for i in self.S[m]+[0]) + nu[1] > 0:
            # print('Iteration: %d, Objective Value: %.6f' %(self.K[-1], mp.objVal))
            # Update K
            self.K = range(1, self.K[-1]+1+1)
            # Obtain permutation for new column
            sigma_k = dict(sorted({i: sum(z[(j,i)] for j in self.I if i!=j) for i in self.I}.items(), key=lambda item: item[1]))
            # print('Is it new sigma?', sigma_k not in self.sigma.values())
            self.sigma[self.K[-1]] = tuple(sigma_k.keys())
            # Update A matrix
            for i,m in a:
                self.A[(i,m,self.K[-1])] = a[(i,m)]
            # Solve Restricted Master Problem
            mp = self.build_mp(self.A)
            mp.optimize()
            self.objVal_history[self.K[-1]] = mp.objVal
            # # Check if optimality gap is reached
            # if mp.objVal <= self.P*gap:
            #     print('Optimality Gap reached')
            #     break
            # Obtain dual variables
            alpha, nu = self.dual_vars(mp)
            # Solve Subproblem
            sp = self.build_sp(alpha, nu)
            sp.optimize()
            a, z = self.subproblem_primal_vars(sp)
        end = time.time() # End timer
        self.Runtime = end-start # Calculate runtime
        return mp
 #%%
if __name__ == '__main__':
    nProducts = 6
    nAssortments = 10
    instance = ig.Instance(nProducts, nAssortments).generate_instance()
    solver = ColGenSolver(instance)
    mp = solver.column_generation()
    # print('Objective Value History', solver.objVal_history)
    print('Time:', solver.Runtime)
    
    # print('Assortments:', instance.assortments)
    # print('v_train:', instance.v_train)
    # print('v_val:', instance.v_val)
    
    # print('Permutations:', solver.sigma)
    # print('A matrix')
    # print(solver.A)
    # for i, m, k in solver.A:
    #     print((i,m,k), solver.A[(i,m,k)])
    
    print('Objective Value - Train:', mp.objVal)    
    # lmda = {int(i.varName.split('[')[1].split(']')[0]): i.x for i in mp.getVars() if 'lmda' in i.varName and i.x > 0}
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
    # print('Difference between train and validation:', abs(mp.objVal - objVal_val))