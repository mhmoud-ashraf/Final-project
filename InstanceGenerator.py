from itertools import permutations
import random
#%%
class Instance:
    def __init__ (self, nProducts, nAssortments, nCustomers=1000, seed=42):
        self.nProducts = nProducts
        # self.products = range(nProducts+1)
        self.products = range(1, nProducts+1)
        self.nAssortments = nAssortments
        self.nCustomers = nCustomers
        random.seed(seed)
        
    def transaction_data (self):
        # self.assortments = {m: random.sample(self.products[1::], random.randint(1, self.nProducts)) for m in range(1, self.nAssortments+1)}
        # self.v = {(i,m): 0 for i in self.products[1::] for m in range(1, self.nAssortments+1)}
        self.assortments = {m: random.sample(self.products, random.randint(1, self.nProducts)) for m in range(1, self.nAssortments+1)}
        self.v = {(i,m): 0 for i in self.products for m in range(1, self.nAssortments+1)}
        for m, assortment in self.assortments.items():
            # purchased_item = {product: 0 for product in self.products[1::]}
            purchased_item = {product: 0 for product in self.products}
            for c in range(1, self.nCustomers+1):
                purchased_item[random.sample(assortment, 1)[0]] += 1
            
            for product, count in purchased_item.items():
                self.v[(product, m)] = count/self.nCustomers
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
                    # for j in [0]+assortment:
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