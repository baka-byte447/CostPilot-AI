import json
import random
from pathlib import Path
from typing import Union


DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[3] / "rl_models" / "q_table.json"


class QLearningAgent:
    def __init__(self, model_path: Union[str, Path] = DEFAULT_MODEL_PATH):
        self.model_path = Path(model_path)
        self.action_space = [1, 2, 4]
        self.alpha = 0.25
        self.gamma = 0.85
        self.epsilon = 0.18
        self.q_table = self._load_table()

    def _load_table(self):
        try:
            if self.model_path.exists():
                with open(self.model_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            return {}
        return {}

    def _save_table(self):
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, "w", encoding="utf-8") as f:
            json.dump(self.q_table, f)

    def _get_state_key(self, cpu, memory, requests):
        cpu_bucket  = min(9, max(0, int(cpu) // 10))
        mem_bucket  = min(9, max(0, int(memory) // 10))
        req_bucket  = min(9, max(0, int(requests * 10)))
        return f"{cpu_bucket}_{mem_bucket}_{req_bucket}"

    def choose_action(self, cpu, memory, requests):
        state_key = self._get_state_key(cpu, memory, requests)
        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0 for _ in self.action_space]

        if random.random() < self.epsilon:
            return random.randrange(len(self.action_space))

        scores = self.q_table[state_key]
        best_index = max(range(len(scores)), key=lambda i: scores[i])
        return best_index

    def update(self, cpu, memory, requests, action_index, reward, next_cpu, next_memory, next_requests):
        state_key = self._get_state_key(cpu, memory, requests)
        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0 for _ in self.action_space]

        next_state_key = self._get_state_key(next_cpu, next_memory, next_requests)
        max_future_q = max(self.q_table.get(next_state_key, [0.0 for _ in self.action_space]))

        old_value = self.q_table[state_key][action_index]
        new_value = old_value + self.alpha * (reward + self.gamma * max_future_q - old_value)
        self.q_table[state_key][action_index] = new_value
        self._save_table()



