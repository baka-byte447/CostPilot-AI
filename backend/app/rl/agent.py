import numpy as np
import os

MODEL_PATH = "app/rl/models/q_table.npy"

CPU_BINS     = 10
MEMORY_BINS  = 10
REQUEST_BINS = 10
N_ACTIONS    = 3

REQUEST_THRESHOLDS = [0.0, 0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0, 2.0, 5.0]


class QLearningAgent:
    def __init__(self):
        if os.path.exists(MODEL_PATH):
            loaded = np.load(MODEL_PATH)
            if loaded.shape == (CPU_BINS, MEMORY_BINS, REQUEST_BINS, N_ACTIONS):
                self.q_table = loaded
            else:
                self.q_table = self._initialize_q_table()
        else:
            self.q_table = self._initialize_q_table()

        self.alpha   = 0.1
        self.gamma   = 0.9
        self.epsilon = 0.2

    def _initialize_q_table(self) -> np.ndarray:
        q = np.zeros((CPU_BINS, MEMORY_BINS, REQUEST_BINS, N_ACTIONS))
        for cpu_b in range(CPU_BINS):
            for mem_b in range(MEMORY_BINS):
                for req_b in range(REQUEST_BINS):
                    if cpu_b >= 7 or mem_b >= 7 or req_b >= 7:
                        q[cpu_b, mem_b, req_b, 0] = 0.4
                    elif cpu_b <= 2 and mem_b <= 3 and req_b <= 2:
                        q[cpu_b, mem_b, req_b, 2] = 0.3
                    else:
                        q[cpu_b, mem_b, req_b, 1] = 0.2
        return q

    def save_model(self):
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        np.save(MODEL_PATH, self.q_table)

    def get_state_index(self, cpu: float, memory: float, request_load: float) -> tuple:
        # Azure VMSS does not expose memory % by default — treat None as 0.0
        cpu          = max(0.0, float(cpu)          if cpu          is not None else 0.0)
        memory       = max(0.0, float(memory)       if memory       is not None else 0.0)
        request_load = max(0.0, float(request_load) if request_load is not None else 0.0)

        cpu_bucket = min(int(cpu / 10), CPU_BINS - 1)
        mem_bucket = min(int(memory / 10), MEMORY_BINS - 1)

        req_bucket = REQUEST_BINS - 1
        for i, threshold in enumerate(REQUEST_THRESHOLDS):
            if request_load <= threshold:
                req_bucket = i
                break

        return (cpu_bucket, mem_bucket, req_bucket)

    def choose_action(self, cpu: float, memory: float, request_load: float) -> int:
        if np.random.rand() < self.epsilon:
            return np.random.randint(N_ACTIONS)
        state = self.get_state_index(cpu, memory, request_load)
        return int(np.argmax(self.q_table[state]))

    def update(self, cpu: float, memory: float, request_load: float,
               action: int, reward: float,
               next_cpu: float = None, next_memory: float = None,
               next_request_load: float = None):
        state = self.get_state_index(cpu, memory, request_load)

        if next_cpu is not None:
            next_state = self.get_state_index(next_cpu, next_memory, next_request_load)
        else:
            next_state = state

        old_value = self.q_table[state][action]
        next_max  = np.max(self.q_table[next_state])
        self.q_table[state][action] = old_value + self.alpha * (
            reward + self.gamma * next_max - old_value
        )
        self.save_model()

    def get_q_table_stats(self) -> dict:
        return {
            "shape":           list(self.q_table.shape),
            "total_states":    CPU_BINS * MEMORY_BINS * REQUEST_BINS,
            "nonzero_entries": int(np.count_nonzero(self.q_table)),
            "coverage_pct":    round(
                100 * np.count_nonzero(self.q_table) /
                (CPU_BINS * MEMORY_BINS * REQUEST_BINS * N_ACTIONS), 2
            ),
            "max_q_value":  round(float(np.max(self.q_table)), 4),
            "min_q_value":  round(float(np.min(self.q_table)), 4),
            "mean_q_value": round(float(np.mean(self.q_table)), 4),
        }