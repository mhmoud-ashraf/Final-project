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
        self.M = instance.assortments.keys()
        self.K = [1]
        self.A = {(i,m,k): 0 for i in self.I for m in self.M for k in self.K}
    
    def mat_A_generator (self, sigma):
        # Initialize A matrix
        A = self.A
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
    
    # def initialize_permutations (ins_:Instance):
    #     patterns = []
    #     for i in range(ins_.n):
    #         pattern_ = list(np.zeros(ins_.n).astype(int))
    #         pattern_[i] = int(ins_.roll_len/ins_.order_lens[i])
    #         patterns.append(pattern_)
    #     return patterns
    
    # def define_master_problem(self, permutations):
    #     n_pattern = len(patterns)
    #     pattern_range = range(n_pattern)
    #     order_range = range(ins_.n)
    #     patterns = np.array(patterns, dtype=int)
    #     master_problem = gp.Model("master problem")
        
    #     # decision variables
    #     lambda_ = master_problem.addVars(pattern_range,
    #                                     vtype=GRB.CONTINUOUS,
    #                                     obj=np.ones(n_pattern),
    #                                     name="lambda")
        
    #     # direction of optimization (min or max)
    #     master_problem.modelSense = GRB.MINIMIZE
        
    #     # demand satisfaction constraint
    #     for i in order_range:
    #         master_problem.addConstr(sum(patterns[p,i]*lambda_[p] for p in pattern_range) == ins_.demands[i],
    #                                 "Demand[%d]" %i)
    #     # solve
    #     return master_problem
    
    
    # def define_subproblem(ins_:Instance, duals):
        # order_range = range(ins_.n)
        # subproblem = gp.Model("subproblem")
        
        # # decision variables
        # x = subproblem.addVars(order_range,
        #                        vtype=GRB.INTEGER,
        #                        obj=duals,
        #                        name="x")
        
        # # direction of optimization (min or max)
        # subproblem.modelSense = GRB.MAXIMIZE
            
        # # Length constraint
        # subproblem.addConstr(sum(ins_.order_lens[i] * x[i] for i in order_range) <= ins_.roll_len)
        # return subproblem
    
    # def print_solution(master, patterns):
    #     use = [math.ceil(i.x) for i in master.getVars()]
    #     for i, p in enumerate(patterns):
    #         if use[i]>0:
    #             print('Pattern ', i, ': how often we should cut: ', use[i])
    #             print('----------------------')
    #             for j,order in enumerate(p):
    #                 if order >0:
    #                     print('order ', j, ' how much: ', order)
    #             print()
    
    # def column_generation(ins_:Instance):
        # patterns = generate_initial_patterns(ins_)
        # objVal_history = []
        # while True:
        #     master_problem = define_master_problem(ins_, patterns)
        #     master_problem.optimize()
        #     objVal_history.append(master_problem.objVal)
        #     dual_variables = np.array([constraint.pi for constraint in master_problem.getConstrs()])
        #     subproblem = define_subproblem(ins_, dual_variables)
        #     subproblem.optimize()
        #     if subproblem.objVal < 1 + 1e-2:
        #         break
        #     patterns.append([i.x for i in subproblem.getVars()])
        # print_solution(master_problem, patterns)
        # print('Total number of rolls used: ', int(np.array([math.ceil(i.x) for i in master_problem.getVars()]).sum()))
        # return objVal_history
    
    
    # import matplotlib.pyplot as plt
    # plt.plot(list(range(len(history))), history,c='r')
    # plt.scatter(list(range(len(history))), history, c='r')
    # plt.xlabel('history')
    # plt.ylabel('objective function value')
    # title = 'solution: ' + str(history[-1])
    # plt.title(title)
    # plt.show()
    
    def build_mp (self):
        model = gp.Model('Assortment Optimization - RMS')
        
        # Decision Variables
        lmda = model.addVars(self.K, ub=1, vtype=GRB.CONTINUOUS, name='lmda')
        espilon_p = model.addVars(self.I, self.M, ub=1, vtype=GRB.CONTINUOUS, name='espilon_p')
        espilon_n = model.addVars(self.I, self.M, ub=1, vtype=GRB.CONTINUOUS, name='espilon_n')
        
        # Objective Function
        model.setObjective(gp.quicksum(espilon_p[i,m] + espilon_n[i,m] for i in self.I for m in self.M), GRB.MINIMIZE)
        
        # Constraints
        constr1 = model.addConstrs((gp.quicksum(self.A[(i,m,k)]*lmda[k] for k in self.K) + espilon_p[i,m] - espilon_n[i,m] == self.v[(i,m)] for i in self.I for m in self.M), name='constr1')
        constr2 = model.addConstr((gp.quicksum(lmda[k] for k in self.K) == 1), name='constr2')
        
        model.setParam('OutputFlag', 0)
        model.update()
        
        return model
    
    def build_sp (self, duals):
        alpha, nu = duals
        
        model = gp.Model('Assortment Optimization - SP')
        
        # Decision Variables
        a = model.addVars(self.I, self.M, vtype=GRB.BINARY, name='a')
        z = {(i,j): model.addVar(vtype=GRB.BINARY, name='z[%d,%d]' %(i,j)) for i in self.I for j in self.I if i!= j}
        
        # Objective Function
        model.setObjective(0 - gp.quicksum(alpha[(i,m)]*a[i,m] for i in self.I for m in self.M) - nu[1], GRB.MINIMIZE)
        
        # Constraints
        constr1 = model.addConstrs((gp.quicksum(a[i,m] for i in self.I) == 1 for m in self.M), name='constr1')
        constr2 = model.addConstrs((a[i,m] <= z[i,j] for m in self.M for i in self.I for j in self.I if i!=j), name='constr2')
        constr3 = model.addConstrs((z[i,j] + z[j,i] == 1 for j in self.I for i in self.I if i!=j), name='constr3')
        constr4 = model.addConstrs((z[i,j] + z[j,k] - 1 <= z[i,k] for i in self.I for j in self.I for k in self.I if i!=j and i!=k and j!=k), name='constr4')
        
        model.setParam('OutputFlag', 0)
        model.update()
        
        return model
    
    
    
    def column_generation(self, gap=1e-2):
        objVal_history = []
        while True:
            mp = self.build_mp()
            mp.optimize()
            objVal_history.append(mp.objVal)
            alpha = {}
            for c in mp.getConstrs():
                if 'constr1' in c.ConstrName:
                    i, j = tuple(c.ConstrName.split('[')[1].split(']')[0].split(','))
                    alpha[(int(i),int(j))] = c.pi
            nu = {1: c.pi for c in mp.getConstrs() if 'constr2' in c.ConstrName}
            sp = self.build_sp((alpha, nu))
            sp.optimize()
            break
        #     if sp.objVal < 1 + gap:
        #         break
        #     patterns.append([i.x for i in subproblem.getVars()])
        # print_solution(master_problem, patterns)
        # print('Total number of rolls used: ', int(np.array([math.ceil(i.x) for i in master_problem.getVars()]).sum()))
        return objVal_history
 #%%
if __name__ == '__main__':
    nProducts = 2
    nAssortments = 2
    instance = ig.Instance(nProducts, nAssortments).generate_instance()
    solver = ColGenSolver(instance)
    objVal_history = solver.column_generation()
    
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
    # print('Objective Value - Train:', mp.objVal)
    # for v in model.getVars():
    #     print(v.varName, v.x)
    
    # lmda = {int(i.varName.split('[')[1].split(']')[0]): i.x for i in mp.getVars() if 'lmda' in i.varName}
    # objVal_val = 0
    # for i in solver.I:
    #     for m in solver.M:
    #         objVal_val += abs(sum(solver.A[(i,m,k)]*lmda[k] for k in lmda) - instance.v_val[(i,m)])
    # print('Objective Value - Val:', objVal_val)
    # print('Difference between train and validation:', abs(mp.objVal - objVal_val))