from itertools import permutations
import random
#%%
class Instance:
    def __init__ (self, nProducts, nAssortments, nCustomers=10000, seed=42):
        self.nProducts = nProducts
        self.products = range(nProducts+1)
        self.assortments = {m: [] for m in range(1, nAssortments+1)}
        self.nCustomers = nCustomers
        random.seed(seed)
    
    def assortments_generator (self):
        assortments = self.assortments
        # Generate subset of products for each assortment
        s_m = random.sample(self.products, random.randint(1, self.nProducts))
        # Ensure that no assortment is empty
        while s_m == [0]:
            s_m = random.sample(self.products, random.randint(1, self.nProducts))
        # Ensure that no two assortments are the same
        for m,s in assortments.items():
            while s in assortments.values():
                s = random.sample(self.products, random.randint(1, self.nProducts))
                if s == [0]:
                    s = random.sample(self.products, random.randint(1, self.nProducts))
            assortments[m] = s
        return assortments
    
    def transaction_data_generator (self, train_prop=0.8):
        # Initialize v_train and v_val
        v_train = {(i,m): 0 for i in self.products for m in self.assortments}
        v_val = {(i,m): 0 for i in self.products for m in self.assortments}
        # Calculate number of customers for training and validation
        n_customers_train = int(train_prop*self.nCustomers)
        n_customers_val = self.nCustomers - n_customers_train
        # Generate transaction data
        for m, assortment in self.assortments.items():
            choices_train = {product: 0 for product in self.products}
            choices_val = {product: 0 for product in self.products}
            # Generate choices for each customer
            for _ in range(n_customers_train):
                choices_train[random.sample(assortment, 1)[0]] += 1
            for _ in range(n_customers_val):
                choices_val[random.sample(assortment, 1)[0]] += 1
            # Calculate v_train and v_val
            for i, sales in choices_train.items():
                v_train[(i, m)] = sales/n_customers_train
            for i, sales in choices_val.items():
                v_val[(i, m)] = sales/n_customers_val
        return v_train, v_val
    
    def permutations_generator (self):
        return {k: sigma_k for k,sigma_k in enumerate(permutations(self.products),start=1)}
    
    def generate_instance (self):
        self.assortments = self.assortments_generator()
        self.v_train, self.v_val = self.transaction_data_generator()
        self.sigma = self.permutations_generator()
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
    # print('v_train')
    # print(instance.v_train)