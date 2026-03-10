from app.rl.environment import CloudEnvironment
from app.rl.agent import QLearningAgent

env = CloudEnvironment()
agent = QLearningAgent()

def decide_scaling_with_rl(cpu, memory, request_load):
    env.reset(cpu, memory, request_load)
    action = agent.choose_action(cpu)
    _,reward, replicas =env.step(action)
    agent.update(cpu, action, reward)
    return replicas