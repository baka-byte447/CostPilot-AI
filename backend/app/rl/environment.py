import numpy as np
from app.optimizer.aws_scaling_executor import aws_executor
import os

AWS_MODE = os.getenv("AWS_MODE", "false").lower() == "true"


class CloudEnvironment:
    def __init__(self):
        self.state = np.array([0.0, 0.0, 0.0])  # [cpu, memory, requests]
        self.current_replicas = 2                 # track current scale level

    def reset(self, cpu: float, memory: float, requests: float):
        self.state = np.array([cpu, memory, requests])
        return self.state

    def step(self, action: int):
        """
        action: 0=scale_up, 1=maintain, 2=scale_down

        Reward function considers all three metrics:
        - Cost penalty: more replicas = higher cost
        - Over-provision penalty: scaling up when all metrics are low = waste
        - Under-provision penalty: not scaling when metrics are high = risk
        - Request-aware: high request load is a strong signal to scale up
        """
        cpu      = self.state[0]
        memory   = self.state[1]
        requests = self.state[2]

        # Update replica count
        if action == 0:   # scale_up
            self.current_replicas = min(self.current_replicas + 1, 8)
        elif action == 2:  # scale_down
            self.current_replicas = max(self.current_replicas - 1, 1)

        # Base cost — proportional to replicas running
        cost = self.current_replicas * 0.0416

        # ── Over-provisioning penalties ───────────────────────────────────
        over_provision_penalty = 0

        # Scaling up when everything is low — pure waste
        if action == 0 and cpu < 40 and memory < 50 and requests < 0.2:
            over_provision_penalty = 10

        # Scaling down when load is high — dangerous
        if action == 2 and (cpu > 70 or memory > 75 or requests > 0.5):
            over_provision_penalty = 12

        # ── Under-provisioning penalties ──────────────────────────────────
        under_provision_penalty = 0

        # CPU overloaded and not scaling up
        if cpu > 80 and action != 0:
            under_provision_penalty += 6

        # Memory pressure and not scaling up
        if memory > 85 and action != 0:
            under_provision_penalty += 4

        # High request load and not scaling up
        if requests > 0.5 and action != 0:
            under_provision_penalty += 5

        # ── Efficiency bonus ──────────────────────────────────────────────
        # Small reward for scaling down when it's genuinely safe to do so
        efficiency_bonus = 0
        if action == 2 and cpu < 30 and memory < 40 and requests < 0.1:
            efficiency_bonus = 2  # good cost-saving decision

        reward = (
            -cost
            - over_provision_penalty
            - under_provision_penalty
            + efficiency_bonus
        )

        # Execute on AWS if enabled
        if AWS_MODE:
            decision = self._map_action_to_aws(action)
            result = aws_executor.execute(decision)
            if not result.get("success"):
                reward -= 10

        return self.state, reward, self.current_replicas

    def _map_action_to_aws(self, action: int) -> dict:
        action_map = {
            0: {"action": "scale_up",   "resource_type": "ecs",
                "target": {
                    "cluster": os.getenv("ECS_CLUSTER", "nimbusopt-cluster"),
                    "service": os.getenv("ECS_SERVICE", "nimbusopt-service")
                },
                "params": {"increment": 1}},
            1: {"action": "maintain",   "resource_type": "ecs",
                "target": {
                    "cluster": os.getenv("ECS_CLUSTER", "nimbusopt-cluster"),
                    "service": os.getenv("ECS_SERVICE", "nimbusopt-service")
                },
                "params": {}},
            2: {"action": "scale_down", "resource_type": "ecs",
                "target": {
                    "cluster": os.getenv("ECS_CLUSTER", "nimbusopt-cluster"),
                    "service": os.getenv("ECS_SERVICE", "nimbusopt-service")
                },
                "params": {"decrement": 1}},
        }
        return action_map.get(action, action_map[1])