import time
import gurobipy as gp
from gurobipy import GRB
import InstanceGenerator as ig
#%%
class CGColSelect:
    def __init__ (self, instance, nPricing=10, new_col_penality=0.01):
        self.instance = instance
        self.v = instance.v_train
        self.S = instance.assortments
        self.I = instance.options
        self.S = instance.assortments
        self.K, self.sigma = [0], {}
        self.A = {}
        self.objVal_history = {}
        self.Runtime = 0
        self.P = len(self.v)
        self.nPricing = nPricing
        self.new_col_penality = new_col_penality
        
    def build_mp (self):
        model = gp.Model('Assortment Optimization - RMP')
        
        # Decision Variables
        lmda = model.addVars(self.K, ub=1, vtype=GRB.CONTINUOUS, name='lmda')
        espilon_p = {(i,m): model.addVar(ub=1, vtype=GRB.CONTINUOUS, name='espilon_p[%d,%d]' %(i,m)) for m in self.S for i in self.S[m]+[0]}
        espilon_n = {(i,m): model.addVar(ub=1, vtype=GRB.CONTINUOUS, name='espilon_n[%d,%d]' %(i,m)) for m in self.S for i in self.S[m]+[0]}
        
        # Objective Function
        model.setObjective(gp.quicksum(espilon_p[(i,m)] + espilon_n[(i,m)] for m in self.S for i in self.S[m]+[0]), GRB.MINIMIZE)
        
        # Constraints
        if self.A == {}:
            constr1 = model.addConstrs((espilon_p[(i,m)] - espilon_n[(i,m)] == self.v[(i,m)] for m in self.S for i in self.S[m]+[0]), name='constr1')
        else:
            constr1 = model.addConstrs((gp.quicksum(self.A[(i,m,k)]*lmda[k] for k in self.K) + espilon_p[(i,m)] - espilon_n[(i,m)] == self.v[(i,m)] for m in self.S for i in self.S[m]+[0]), name='constr1')
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
        # model.setParam('PoolSearchMode', 1) # Enable PoolSearch with no guarantee on the quality
        model.setParam('PoolSearchMode', 2) # Enable PoolSearch with n best solutions
        model.setParam('PoolSolutions', self.nPricing) # Output multiple solutions
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
        a, z = {sol+1:{} for sol in range(sp.SolCount)}, {sol+1:{} for sol in range(sp.SolCount)}
        for sol in range(sp.SolCount):
            sp.setParam('SolutionNumber', sol)
            for var in sp.getVars():
                idx, val = var.varName.split('[')[1].split(']')[0], var.Xn
                if 'a' in var.varName:
                    a[sol+1][(int(idx.split(',')[0]), int(idx.split(',')[-1]))] = int(val)
                if 'z' in var.varName:
                    z[sol+1][(int(idx.split(',')[0]), int(idx.split(',')[-1]))] = int(val)
        return a, z
    
    def new_columns (self, a, z):
        # Initialize new K, sigma, and A matrix
        K = self.K.copy()
        sigma = self.sigma.copy()
        A = self.A.copy()
        # Iterate over all solutions for the pricing problem
        for sol in range(self.nPricing):
            # Update K
            if 0 in K:
                K += [1]
                K.remove(0)
            else:
                K += [K[-1]+1]
            # Obtain permutation for new column
            sigma_k = dict(sorted({i: sum(z[sol+1][(j,i)] for j in self.I if i!=j) for i in self.I}.items(), key=lambda item: item[1]))
            # print('Is it new sigma?', sigma_k not in sigma.values())
            sigma[K[-1]] = tuple(sigma_k.keys())
            # Update A matrix
            for i,m in a[sol+1]:
                A[(i,m,K[-1])] = a[sol+1][(i,m)]
        return K, sigma, A
    
    def subset_new_columns (self, K, sigma, A):
        # Find candidate columns
        new_cols = list(set(K).difference(set(self.K)))
        # Solve Subset MILP to find the best subset of columns
        subset_milp = self.build_subset_mp(A, new_cols)
        subset_milp.optimize()
        # Determine which columns to keep/remove
        y = {int(i.varName.split('[')[1].split(']')[0]): int(i.x) for i in subset_milp.getVars() if 'y' in i.varName}
        # print('New Columns to keep/remove:', y)
        for k,val in y.items():
            if val == 0:
                K.remove(k)
        sigma = {k: sigma[k] for k in K}
        A = {(i,m,k): A[(i,m,k)] for i,m,k in A if k in K}
        return K, sigma, A
    
    def build_subset_mp (self, A, K_prime):
        # Update K and set new column penality
        K = self.K+K_prime
        delta = self.new_col_penality
        
        # Initialize model
        model = gp.Model('Assortment Optimization - RMP - Column Selection')
        
        # Decision Variables
        lmda = model.addVars(K, ub=1, vtype=GRB.CONTINUOUS, name='lmda')
        espilon_p = {(i,m): model.addVar(ub=1, vtype=GRB.CONTINUOUS, name='espilon_p[%d,%d]' %(i,m)) for m in self.S for i in self.S[m]+[0]}
        espilon_n = {(i,m): model.addVar(ub=1, vtype=GRB.CONTINUOUS, name='espilon_n[%d,%d]' %(i,m)) for m in self.S for i in self.S[m]+[0]}
        y = model.addVars(K_prime, vtype=GRB.BINARY, name='y')
        
        # Objective Function
        model.setObjective(gp.quicksum(espilon_p[(i,m)] + espilon_n[(i,m)] for m in self.S for i in self.S[m]+[0]) + delta*gp.quicksum(y[k] for k in K_prime), GRB.MINIMIZE)
        
        # Constraints
        if self.A == {}:
            constr1 = model.addConstrs((gp.quicksum(A[(i,m,k)]*lmda[k] for k in K_prime) + espilon_p[(i,m)] - espilon_n[(i,m)] == self.v[(i,m)] for m in self.S for i in self.S[m]+[0]), name='constr1')
        else:
            constr1 = model.addConstrs((gp.quicksum(A[(i,m,k)]*lmda[k] for k in K) + espilon_p[(i,m)] - espilon_n[(i,m)] == self.v[(i,m)] for m in self.S for i in self.S[m]+[0]), name='constr1')
        constr2 = model.addConstr(gp.quicksum(lmda[k] for k in K) == 1, name='constr2')
        constr3 = model.addConstrs((lmda[k] <= y[k] for k in K_prime), name='constr3')
        
        model.setParam('OutputFlag', 0)
        # model.setParam('Method', 1) # Use Dual Simplex
        model.update()
        # model.write('RMS_SS_{%s}.lp'%self.K[-1])
        return model
    
    def CG_solve(self, gap=1e-4):
        self.iter = 0 # Initialize iteration counter to zero
        start = time.time() # Start timer
        # Solve Restricted Master Problem
        mp = self.build_mp()
        mp.optimize()
        self.objVal_history[self.iter] = mp.objVal
        # Obtain dual variables
        alpha, nu = self.dual_vars(mp)
        # Solve Subproblem
        sp = self.build_sp(alpha, nu)
        sp.optimize()
        # Obtain subproblem primal variables values
        a, z = self.subproblem_primal_vars(sp)
        
        # Iteratively solve Restricted Master Problem and Subproblem
        while True in [sum(alpha[(i,m)]*a[sol+1][(i,m)] for m in self.S for i in self.S[m]+[0]) + nu[1] > 0 for sol in range(sp.SolCount)]:
            self.iter += 1
            # print('Iteration: %d, Objective Value: %.6f' %(self.iter, mp.objVal))
            
            # Generate new columns
            K, sigma, A = (_.copy() for _ in self.new_columns(a, z))
            # Add a subset of the new columns
            K, sigma, A = (_.copy() for _ in self.subset_new_columns(K, sigma, A))
            # Break if none of the new columns to be added, otherwise update K, sigma, and A
            if len(K) == len(self.K):
                break
            else:
                self.K, self.sigma, self.A = (_.copy() for _ in (K, sigma, A))
            
            # Solve Restricted Master Problem
            mp = self.build_mp()
            mp.optimize()
            self.objVal_history[self.iter] = mp.objVal
            # Break if objective value does not change
            if self.objVal_history[self.iter] == self.objVal_history[self.iter-1]:
                break
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
    nProducts = 5
    nAssortments = 5
    instance = ig.Instance(nProducts, nAssortments).generate_instance()
    solver = CGColSelect(instance, nPricing=3, new_col_penality=1e-3)
    mp = solver.CG_solve()
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