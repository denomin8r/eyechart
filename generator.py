import numpy as np


class RandomGenerator:
    
    def __init__(self, n_symbols, smart=False, offset=2):
        
        self.n_symbols = n_symbols
        self.smart = smart
        self.offset = offset
    
    def next_symbols(self, num_symbols):
        return np.random.randint(0, self.n_symbols, num_symbols)
