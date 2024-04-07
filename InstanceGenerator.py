from itertools import permutations
import random
#%%
class Instance:
    def __init__ (self, nProducts, nAssortments, nCustomers=10000, seed=42):
        self.nProducts = nProducts
        self.products = range(nProducts+1)
        self.nAssortments = nAssortments
        self.nCustomers = nCustomers
        random.seed(seed)
        
    def transaction_data (self):
        self.assortments = {m: [] for m in range(1, self.nAssortments+1)}
        subset = random.sample(self.products, random.randint(1, self.nProducts))
        while subset == [0]:
            subset = random.sample(self.products, random.randint(1, self.nProducts))
        for m in range(1, self.nAssortments+1):
            while subset in self.assortments.values():
                subset = random.sample(self.products, random.randint(1, self.nProducts))
                if subset == [0]:
                    subset = random.sample(self.products, random.randint(1, self.nProducts))
            self.assortments[m] = subset
        self.v_train = {(i,m): 0 for i in self.products for m in range(1, self.nAssortments+1)}
        self.v_val = {(i,m): 0 for i in self.products for m in range(1, self.nAssortments+1)}
        for m, assortment in self.assortments.items():
            choices_train = {product: 0 for product in self.products}
            choices_val = {product: 0 for product in self.products}
            train_prop, val_prop = 0.8, 0.2
            for _ in range(1, int(train_prop*self.nCustomers+1)):
                choices_train[random.sample(assortment, 1)[0]] += 1
            for _ in range(1, int(val_prop*self.nCustomers+1)):
                choices_val[random.sample(assortment, 1)[0]] += 1
            
            for product, count in choices_train.items():
                self.v_train[(product, m)] = count/(train_prop*self.nCustomers)
            for product, count in choices_val.items():
                self.v_val[(product, m)] = count/(val_prop*self.nCustomers)
        return self
    
    def generate_sigma (self):
        sigma_vals = list(permutations(self.products))
        self.sigma = {i: sigma_vals[i-1] for i in range(1, len(sigma_vals)+1)}
        return self
    
    def transfrom_to_A (self):
        self.A = {(i,m,k): 0 for i in self.products for m in self.assortments for k in self.sigma}
        
        for k, permutation in self.sigma.items():
            for i in permutation:
                for m, assortment in self.assortments.items():
                    j, arg_min = float('inf'), float('inf')
                    for j in assortment:
                        if permutation.index(j) < arg_min:
                            arg_min = permutation.index(j)
                            j = j
                    if i == j:
                        self.A[(i,m,k)] = 1
        return self
    
    def generate_instance (self):
        self.transaction_data()
        self.generate_sigma()
        self.transfrom_to_A()
        return self
#%%
if __name__ == '__main__':
    nProducts = 3
    nAssortments = 2
    instance = Instance(nProducts, nAssortments).generate_instance()
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
    # print('v_train')
    # print(instance.v_train)