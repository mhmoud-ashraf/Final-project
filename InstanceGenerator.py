import math
import random
from collections import Counter
#%%
class Instance:
    def __init__ (self, nProducts, nAssortments, nCustomers=10000, seed=42):
        self.nProducts = nProducts
        self.products = range(1, nProducts+1)
        self.options = range(nProducts+1)
        self.nAssortments = nAssortments
        self.nCustomers = nCustomers
        random.seed(seed)
    
    def assortments_generator (self):
        # Check if number of assortments is too large
        assert sum(int(math.factorial(self.nProducts)/(math.factorial(self.nProducts-i))) for i in range(1, self.nProducts+1)) >= self.nAssortments, 'Number of assortments is too large'
        # Generate subset of products for each assortment such that no two assortments are the same
        assortments = []
        while len(assortments) < self.nAssortments:
            assoertment = random.sample(self.products, random.randint(1, self.nProducts))
            if assoertment not in assortments:
                assortments.append(assoertment)
        return dict(zip(range(1, self.nAssortments+1), assortments))
    
    def transaction_data_generator (self, train_prop=0.8):
        # Initialize v_train and v_val
        v_train = {(i, m): 0 for m,S_m in self.assortments.items() for i in S_m+[0]}
        v_val = {(i, m): 0 for m,S_m in self.assortments.items() for i in S_m+[0]}
        # Calculate number of customers for training and validation
        n_customers_train = int(train_prop*self.nCustomers)
        n_customers_val = self.nCustomers - n_customers_train
        # Generate transaction data
        for m, S_m in self.assortments.items():
            # Generate choices for each customer
            choices_train = [random.choice(S_m+[0]) for _ in range(n_customers_train)]
            choices_val = [random.choice(S_m+[0]) for _ in range(n_customers_val)]
            # Calculate v_train and v_val
            for i, v in Counter(choices_train).items():
                v_train[(i, m)] = round(v/n_customers_train, 4)
            for i, v in Counter(choices_val).items():
                v_val[(i, m)] = round(v/n_customers_val, 4)
        return v_train, v_val
    
    def generate_instance (self):
        self.assortments = self.assortments_generator()
        self.v_train, self.v_val = self.transaction_data_generator()
        return self
#%%
if __name__ == '__main__':
    nProducts = 2
    nAssortments = 2
    instance = Instance(nProducts, nAssortments).generate_instance()
    # print('Assortments:', instance.assortments)
    # print('v_train:', instance.v_train)
    # print('v_val:', instance.v_val)