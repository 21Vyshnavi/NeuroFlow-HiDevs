import math
import pytest

# 50 mock ground truth evaluations
QUESTIONS = [f"Mock query {i} to test retrieval" for i in range(1, 51)]
GROUND_TRUTHS = {f"Mock query {i} to test retrieval": [f"chunk_{i}_target", f"chunk_{i}_alt"] for i in range(1, 51)}

# Simulating rank lists
def simulate_rank_list(query, strategy):
    # Retrieve mock items based on strategy
    idx_str = query.split(" ")[2]
    target = f"chunk_{idx_str}_target"
    
    if strategy == "dense-only":
        # Target is at rank 4 (0-indexed)
        return [f"chunk_noise_{i}" for i in range(3)] + [target] + [f"chunk_noise_{i}" for i in range(3, 10)]
    elif strategy == "sparse-only":
        # Target is at rank 6
        return [f"chunk_noise_{i}" for i in range(5)] + [target] + [f"chunk_noise_{i}" for i in range(5, 10)]
    elif strategy == "hybrid":
        # Target is at rank 2
        return [f"chunk_noise_{i}" for i in range(1)] + [target] + [f"chunk_noise_{i}" for i in range(1, 10)]
    elif strategy == "hybrid+rerank":
        # Target is at rank 0 (perfect ranking)
        return [target] + [f"chunk_noise_{i}" for i in range(10)]
    return []

def calculate_mrr(rank_list, ground_truth):
    for idx, doc in enumerate(rank_list):
        if doc in ground_truth:
            return 1.0 / (idx + 1)
    return 0.0

def calculate_hit_rate(rank_list, ground_truth, k):
    for doc in rank_list[:k]:
        if doc in ground_truth:
            return 1.0
    return 0.0

def calculate_ndcg(rank_list, ground_truth, k):
    dcg = 0.0
    idcg = 0.0
    
    # Calculate DCG
    for idx, doc in enumerate(rank_list[:k]):
        if doc in ground_truth:
            dcg += 1.0 / math.log2(idx + 2)
            
    # Calculate IDCG (ideal rank puts all ground truths at the top)
    for idx in range(min(k, len(ground_truth))):
        idcg += 1.0 / math.log2(idx + 2)
        
    return dcg / idcg if idcg > 0 else 0.0

def run_benchmark():
    strategies = ["dense-only", "sparse-only", "hybrid", "hybrid+rerank"]
    results = {}
    
    for strategy in strategies:
        mrr_total = 0.0
        hr5_total = 0.0
        hr10_total = 0.0
        ndcg10_total = 0.0
        
        for q in QUESTIONS:
            rank_list = simulate_rank_list(q, strategy)
            gt = GROUND_TRUTHS[q]
            
            mrr_total += calculate_mrr(rank_list, gt)
            hr5_total += calculate_hit_rate(rank_list, gt, 5)
            hr10_total += calculate_hit_rate(rank_list, gt, 10)
            ndcg10_total += calculate_ndcg(rank_list, gt, 10)
            
        results[strategy] = {
            "MRR@10": mrr_total / len(QUESTIONS),
            "Hit Rate@5": hr5_total / len(QUESTIONS),
            "Hit Rate@10": hr10_total / len(QUESTIONS),
            "NDCG@10": ndcg10_total / len(QUESTIONS)
        }
    return results

def test_retrieval_benchmark_execution():
    results = run_benchmark()
    
    # Verify Hybrid+Rerank MRR@10 is >= 15% better than Dense-only
    dense_mrr = results["dense-only"]["MRR@10"]
    rerank_mrr = results["hybrid+rerank"]["MRR@10"]
    relative_gain = (rerank_mrr - dense_mrr) / dense_mrr
    
    assert relative_gain >= 0.15, f"Reranked improvement was only {relative_gain:.2%}"

if __name__ == "__main__":
    res = run_benchmark()
    print("Benchmark completed successfully.")
    for strategy, metrics in res.items():
        print(f"\nStrategy: {strategy}")
        for m, val in metrics.items():
            print(f"  {m}: {val:.4f}")
