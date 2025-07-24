import numpy as np


class RandomGenerator:
    
    def __init__(self, n_symbols, smart=False, offset=2):
        
        self.n_symbols = n_symbols
        self.smart = smart
        self.offset = offset
    
    def next_symbols(self, n):
        
        if not self.smart:
            symbols = np.random.randint(0, self.n_symbols, n)
        else:
            symbols = list(range(self.n_symbols))
            np.random.shuffle(symbols)

            while len(symbols) < n:
                new_symbols = symbols[-self.n_symbols:-self.offset]
                np.random.shuffle(new_symbols)
                symbols += new_symbols
            
        return symbols[:n]
