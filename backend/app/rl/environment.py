import numpy as np

from app.optimizer.aws_scaling_executor import aws_executor
import os

AWS_MODE= os.getenv("AWS_MODE", "false").lower() =="true"

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

        if AWS_MODE:
            decision=self._map_action_to_aws(action)
            result = aws_executor.execute(decision)

            if not result.get("success"):
                reward-= 10

        return self.state, reward, replicas
    
    def _map_action_to_aws(self, action: int) -> dict:
        action_map = {
            0: {"action": "scale_up",   "resource_type": "ecs",
                "target": {"cluster": os.getenv("ECS_CLUSTER"), "service": os.getenv("ECS_SERVICE")},
                "params": {"increment": 1}},
            1: {"action": "maintain",   "resource_type": "ecs",
                "target": {"cluster": os.getenv("ECS_CLUSTER"), "service": os.getenv("ECS_SERVICE")},
                "params": {}},
            2: {"action": "scale_down", "resource_type": "ecs",
                "target": {"cluster": os.getenv("ECS_CLUSTER"), "service": os.getenv("ECS_SERVICE")},
                "params": {"decrement": 1}},
        }
        return action_map.get(action, action_map[1])