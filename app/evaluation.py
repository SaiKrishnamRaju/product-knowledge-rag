def recall_at_k(relevant, retrieved, k=5):
    relevant = set(relevant)
    return len(relevant.intersection(retrieved[:k])) / len(relevant) if relevant else 0.0

def hit_at_k(relevant, retrieved, k=5):
    return float(bool(set(relevant).intersection(retrieved[:k])))

def faithfulness(supported: int, evaluated: int) -> float:
    if evaluated <= 0 or supported < 0 or supported > evaluated:
        raise ValueError("Invalid claim counts")
    return supported / evaluated
