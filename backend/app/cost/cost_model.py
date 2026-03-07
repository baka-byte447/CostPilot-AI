



INSTANCE_COST_PER_HOUR = 0.0416

CPU_THRESHOLD = 70
MEMORY_THRESHOLD = 70

REQUEST_THRESHOLD = 100


def estimate_instances(cpu, memory, request_load):

    cpu_instances = cpu / CPU_THRESHOLD
    memory_instances = memory / MEMORY_THRESHOLD
    request_instances = request_load / REQUEST_THRESHOLD
    required_instances = max(cpu_instances, memory_instances, request_instances)

    return max(1, int(required_instances) + 1)

def calculate_cost(instances):
    return instances * INSTANCE_COST_PER_HOUR


