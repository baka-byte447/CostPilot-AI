class CloudEnvironment:
    def __init__(self):
        self.state = [0.0, 0.0, 0.0]

    def reset(self, cpu, memory, requests):
        # Store a simple snapshot of the incoming load
        self.state = [float(cpu), float(memory), float(requests)]
        return tuple(self.state)

    def step(self, action):
        possible = [1, 2, 4]
        replicas = possible[action] if 0 <= action < len(possible) else possible[0]

        cpu_utilization = self.state[0]
        cost = replicas * 0.0416
        penalty = 5 if cpu_utilization > 80 else 0
        slo_bonus = 2.0 if cpu_utilization <= 80 else 0.0

        reward = slo_bonus - cost - penalty
        return tuple(self.state), reward, replicas