

MIN_REPLICAS = 1
MAX_REPLICAS = 6  
MAX_SCALE_STEP = 2  


def apply_safety(current_replicas, proposed_replicas):

    proposed_replicas=max(MIN_REPLICAS, proposed_replicas)
    proposed_replicas=min(MAX_REPLICAS, proposed_replicas)

    if abs(proposed_replicas-current_replicas) > MAX_SCALE_STEP:

        if proposed_replicas > current_replicas:
            proposed_replicas=current_replicas + MAX_SCALE_STEP
        else:
            proposed_replicas = current_replicas- MAX_SCALE_STEP
    return proposed_replicas

