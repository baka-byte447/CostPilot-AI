import numpy as np

class CloudEnvironment:
    def __init__(self):
        self.state = np.array([0,0,0])

    def reset(self, cpu, memory,requests):
        self.state = np.array([cpu, memory, requests])
        return self.state

    def step(self, action):

        replicas = [1, 2, 4][action]
        cpu =self.state[0]
        cost=replicas*0.0416
        penalty=0
        if cpu>80:
            penalty=5

        reward = -cost - penalty
        return self.state, reward, replicas