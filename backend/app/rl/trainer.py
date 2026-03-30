from app.rl.environment import CloudEnvironment
from app.rl.agent import QLearningAgent

env = CloudEnvironment()
agent = QLearningAgent()


def decide_scaling_with_rl(cpu, memory, request_load):
    env.reset(cpu, memory, request_load)
    action_index = agent.choose_action(cpu)
    _, reward, replicas = env.step(action_index)
    agent.update(cpu, action_index, reward)
    return replicas