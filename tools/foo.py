import random

class RandomNumberGenerator:
    def __init__(self, lower_bound=1, upper_bound=100):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def generate(self):
        return random.randint(self.lower_bound, self.upper_bound)
