import os
import psutil

def get_optimal_process_count(workload_type='cpu'):
    cpu_count= len(psutil.Process().cpu_affinity())  

    if workload_type == 'cpu':
        return cpu_count
    
    elif workload_type == 'io':
        return cpu_count * 2
    
    else:
        raise ValueError("workload_type must be 'cpu' or 'io'")
