import random
from typing import Dict

from app.rl.agent import QLearningAgent
from app.rl.environment import CloudEnvironment


class RLOptimizationAgent:
    """Small RL helper for scaling decisions."""

    def __init__(self):
        self.agent = QLearningAgent()
        self.env = CloudEnvironment()
        self.last_decision: Dict[str, float] = {}

    def train(self, env=None, timesteps: int = 300):
        active_env = env or self.env
        for _ in range(timesteps):
            cpu = random.randint(10, 90)
            memory = random.randint(10, 90)
            requests = random.randint(10, 120)

            active_env.reset(cpu, memory, requests)
            action_idx = self.agent.choose_action(cpu)
            _, reward, _ = active_env.step(action_idx)
            self.agent.update(cpu, action_idx, reward)

        return True

    def decide_action(self, state: Dict[str, float]):
        cpu = state.get("cpu", 0)
        memory = state.get("memory", 0)
        requests = state.get("requests", 0)

        self.env.reset(cpu, memory, requests)
        action_idx = self.agent.choose_action(cpu)
        _, reward, replicas = self.env.step(action_idx)
        self.agent.update(cpu, action_idx, reward)

        self.last_decision = {
            "cpu": cpu,
            "memory": memory,
            "requests": requests,
            "replicas": replicas,
            "reward": reward,
            "action_index": action_idx,
        }

        return {
            "replicas": replicas,
            "action_index": action_idx,
            "estimated_reward": reward,
        }

    def get_action_rationale(self):
        if not self.last_decision:
            return "No RL decision made yet."

        return (
            f"cpu ~{self.last_decision['cpu']}% with mem {self.last_decision['memory']}% "
            f"and load {self.last_decision['requests']} led to {self.last_decision['replicas']} replicas "
            f"(reward {self.last_decision['reward']:.2f})."
        )
