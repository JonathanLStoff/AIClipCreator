import math
from clip_creator.conf import LOGGER, RED_COM_DELAY
from typing import List, Dict

def start_times_per_chunk(chunks:dict)->dict:
    next_start = 0
    new_chunks = {}
    for i in range(len(chunks.items())):
        
        for k, v in chunks.items():
                
            if v['idx'] == i:
                LOGGER.info(f"Starting time for chunk {i} is {v['audio_length']}")
                v['start'] = next_start
                next_start += v['audio_length'] + RED_COM_DELAY
                new_chunks[k]= v
    
    return new_chunks

def get_88_percentile(dicts: List[Dict]):
    """
    Returns a list of dictionaries whose 'upvotes' value is strictly greater than the
    88th percentile value of the upvotes in the input list.
    
    Each dictionary is expected to have an 'upvotes' key with a numerical value.
    
    Raises:
        ValueError: If the input list is empty.
    """
    if not dicts:
        raise ValueError("The list of dictionaries is empty.")

    # Extract the upvotes values and sort them in ascending order.
    upvotes = sorted(item.get("best_reply", {}).get("upvotes", 0) for item in dicts)
    n = len(upvotes)
    
    # Calculate the index corresponding to the 88th percentile.
    index = math.ceil(n * 0.88) - 1
    index = max(0, min(index, n - 1))
    
    threshold_rpl = upvotes[index]
    

    upvotes = sorted(item.get("upvotes", 0) for item in dicts)
    n = len(upvotes)
    
    # Calculate the index corresponding to the 88th percentile.
    index = math.ceil(n * 0.88) - 1
    index = max(0, min(index, n - 1))
    
    threshold = upvotes[index]
    # Return all dictionaries whose upvotes are strictly above the threshold.
    return threshold, threshold_rpl

# Example usage:
if __name__ == "__main__":
    sample_data = [
        {"upvotes": 10},
        {"upvotes": 50},
        {"upvotes": 20},
        {"upvotes": 80},
        {"upvotes": 30},
        {"upvotes": 60},
        {"upvotes": 90},
        {"upvotes": 40},
        {"upvotes": 70},
        {"upvotes": 100}
    ]
    
    threshold = get_88_percentile(sample_data)
    print(f"The 88th percentile upvotes value is: {threshold}")