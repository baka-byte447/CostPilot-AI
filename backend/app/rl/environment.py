import numpy as np
from app.optimizer.aws_scaling_executor import aws_executor
import os

AWS_MODE = os.getenv("AWS_MODE", "false").lower() == "true"


class CloudEnvironment:
    def __init__(self):
        self.state            = np.array([0.0, 0.0, 0.0])
        self.current_replicas = 2
        self.forecast         = None

    def reset(self, cpu: float, memory: float, requests: float,
              forecast: dict = None):
        self.state    = np.array([cpu, memory, requests])
        self.forecast = forecast
        return self.state

    def step(self, action: int):
        cpu      = self.state[0]
        memory   = self.state[1]
        requests = self.state[2]

        if action == 0:
            self.current_replicas = min(self.current_replicas + 1, 8)
        elif action == 2:
            self.current_replicas = max(self.current_replicas - 1, 1)

        cost = self.current_replicas * 0.0416

        over_provision_penalty = 0
        if action == 0 and cpu < 40 and memory < 50 and requests < 0.2:
            over_provision_penalty = 10
        if action == 2 and (cpu > 70 or memory > 75 or requests > 0.5):
            over_provision_penalty = 12

        under_provision_penalty = 0
        if cpu > 80 and action != 0:
            under_provision_penalty += 6
        if memory > 85 and action != 0:
            under_provision_penalty += 4
        if requests > 0.5 and action != 0:
            under_provision_penalty += 5

        efficiency_bonus = 0
        if action == 2 and cpu < 30 and memory < 40 and requests < 0.1:
            efficiency_bonus = 2

        forecast_bonus = 0
        if self.forecast and self.forecast.get("forecast_available"):
            worst_cpu = self.forecast.get("worst_case_cpu", cpu)
            worst_mem = self.forecast.get("worst_case_memory", memory)
            worst_req = self.forecast.get("worst_case_requests", requests)

            high_load_incoming = worst_cpu > 75 or worst_mem > 80 or worst_req > 0.6

            if high_load_incoming and action == 0:
                forecast_bonus = 3
            elif high_load_incoming and action == 2:
                forecast_bonus = -5

            low_load_forecast = worst_cpu < 30 and worst_mem < 40 and worst_req < 0.1
            if low_load_forecast and action == 2:
                forecast_bonus = 2

        reward = (
            -cost
            - over_provision_penalty
            - under_provision_penalty
            + efficiency_bonus
            + forecast_bonus
        )

        if AWS_MODE:
            decision = self._map_action_to_aws(action)
            result   = aws_executor.execute(decision)
            if not result.get("success"):
                reward -= 10

        return self.state, reward, self.current_replicas

    def _map_action_to_aws(self, action: int) -> dict:
        action_map = {
            0: {"action": "scale_up",   "resource_type": "ecs",
                "target": {"cluster": os.getenv("ECS_CLUSTER", "nimbusopt-cluster"),
                           "service": os.getenv("ECS_SERVICE", "nimbusopt-service")},
                "params": {"increment": 1}},
            1: {"action": "maintain",   "resource_type": "ecs",
                "target": {"cluster": os.getenv("ECS_CLUSTER", "nimbusopt-cluster"),
                           "service": os.getenv("ECS_SERVICE", "nimbusopt-service")},
                "params": {}},
            2: {"action": "scale_down", "resource_type": "ecs",
                "target": {"cluster": os.getenv("ECS_CLUSTER", "nimbusopt-cluster"),
                           "service": os.getenv("ECS_SERVICE", "nimbusopt-service")},
                "params": {"decrement": 1}},
        }
        return action_map.get(action, action_map[1])
    

    