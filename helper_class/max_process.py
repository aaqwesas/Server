import os

def get_optimal_process_count(workload_type='cpu'):
    cpu_count = os.cpu_count() or 1

    if workload_type == 'cpu':
        return cpu_count
    
    elif workload_type == 'io':
        return cpu_count * 2
    
    else:
        raise ValueError("workload_type must be 'cpu' or 'io'")
