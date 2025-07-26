import numpy as np


class RandomGenerator:
    
    def __init__(self, n_symbols):
        
        self.n_symbols = n_symbols

    def next_symbols(self, num_symbols):
        return np.random.randint(0, self.n_symbols, num_symbols)
