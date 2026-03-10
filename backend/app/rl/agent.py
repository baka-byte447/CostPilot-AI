import numpy as np
import os
MODEL_PATH = "app/rl/models/q_table.npy"



class QLearningAgent:

    def __init__(self):
        if os.path.exists(MODEL_PATH):
            self.q_table = np.load(MODEL_PATH)
        else:
            self.q_table = np.zeros((100, 3))

        self.alpha = 0.1
        self.gamma = 0.9
        self.epsilon = 0.2

    def save_model(self):
        np.save(MODEL_PATH, self.q_table)

    def get_state_index(self, cpu):
        return int(cpu)

    def choose_action(self, cpu):
        state = self.get_state_index(cpu)
        if np.random.rand() < self.epsilon:
            return np.random.randint(3)
        return np.argmax(self.q_table[state])

    def update(self, cpu, action, reward):
        state = self.get_state_index(cpu)
        old_value = self.q_table[state, action]
        new_value = old_value + self.alpha * (reward - old_value)
        self.q_table[state, action] = new_value
        self.save_model()



