import json
import os
import random

MODEL_PATH = "rl_models/q_table.json"


class QLearningAgent:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self.action_space = [1, 2, 4]
        self.alpha = 0.25
        self.gamma = 0.85
        self.epsilon = 0.18
        self.q_table = self._load_table()

    def _load_table(self):
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_table(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, "w", encoding="utf-8") as f:
            json.dump(self.q_table, f)

    def _get_state_key(self, cpu):
        try:
            idx = int(cpu)
        except Exception:
            idx = 0
        idx = max(0, min(99, idx))
        return str(idx)

    def choose_action(self, cpu):
        state_key = self._get_state_key(cpu)
        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0 for _ in self.action_space]

        if random.random() < self.epsilon:
            return random.randrange(len(self.action_space))

        scores = self.q_table[state_key]
        best_index = max(range(len(scores)), key=lambda i: scores[i])
        return best_index

    def update(self, cpu, action_index, reward):
        state_key = self._get_state_key(cpu)
        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0 for _ in self.action_space]

        old_value = self.q_table[state_key][action_index]
        new_value = old_value + self.alpha * (reward - old_value)
        self.q_table[state_key][action_index] = new_value
        self._save_table()



