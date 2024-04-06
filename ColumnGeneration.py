import math
import gurobipy as gp
from gurobipy import GRB
import InstanceGenerator as ig
#%%
class Solver:
    def __init__ (self, instance):
        self.instance = instance
        self.K = instance.sigma.keys()
        self.I = range(1, instance.nProducts+1)
        self.M = range(1, instance.nAssortments+1)
        self.A = instance.A
        self.v = instance.v
    
    # def initialize_permutations (ins_:Instance):
    #     patterns = []
    #     for i in range(ins_.n):
    #         pattern_ = list(np.zeros(ins_.n).astype(int))
    #         pattern_[i] = int(ins_.roll_len/ins_.order_lens[i])
    #         patterns.append(pattern_)
    #     return patterns
    
    # def define_master_problem(ins_:Instance, patterns):
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
        
        return model
 #%%
if __name__ == '__main__':
    nProducts = 2
    nAssortments = 2
    instance = ig.Instance(nProducts, nAssortments).generate_instance()
    solver = Solver(instance)
    model = solver.build_model()
    model.optimize()
    
    print('Assortments')
    print(instance.assortments)
    print()
    print('Permutations')
    print(instance.sigma)
    print()
    print('A matrix')
    for i, m, k in instance.A:
        print((i, m, k), instance.A[(i, m, k)])
    print()
    print('v_vals')
    for i, m in instance.v:
        print((i, m), instance.v[(i, m)])
    print()
    print('Objective Value:', model.objVal)
    for v in model.getVars():
        print(v.varName, v.x)