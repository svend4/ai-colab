#!/usr/bin/env python3
import os
import sys
import argparse

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUES_DONE = os.path.join(ROOT, "queues", "done")
TASKS_DIR = os.path.join(ROOT, "tasks")

try:
    from semantic_engine import AdvancedAlgorithms
except ImportError:
    # If not run from tools directory
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from semantic_engine import AdvancedAlgorithms

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def search_memoized_thoughts(target_text, threshold=5):
    """
    Scans queues/done for tasks that are conceptually identical
    (LSH Hamming Distance < threshold).
    """
    target_hash = AdvancedAlgorithms.simhash(target_text)
    
    if not os.path.isdir(QUEUES_DONE):
        return []
        
    matches = []
    for filename in os.listdir(QUEUES_DONE):
        if not filename.endswith(".done.md"): continue
        
        filepath = os.path.join(QUEUES_DONE, filename)
        content = read_file(filepath)
        
        # If the file is very small, skip
        if len(content) < 50: continue
            
        candidate_hash = AdvancedAlgorithms.simhash(content)
        distance = AdvancedAlgorithms.hamming_distance(target_hash, candidate_hash)
        
        if distance <= threshold:
            # We found a conceptual duplicate!
            matches.append({
                "file": filename,
                "distance": distance,
                "summary": AdvancedAlgorithms.extract_summary(content, max_sentences=1)
            })
            
    matches.sort(key=lambda x: x["distance"])
    return matches

def main():
    parser = argparse.ArgumentParser(description="Thought Memoization (LSH Engine)")
    parser.add_argument("target_file", help="Path to the new task file to check")
    parser.add_argument("--threshold", type=int, default=5, help="Hamming distance threshold")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.target_file):
        print(f"Error: {args.target_file} not found.")
        return 1
        
    target_text = read_file(args.target_file)
    print("="*60)
    print("THOUGHT MEMOIZATION ENGINE (SimHash LSH)")
    print("="*60)
    print(f"Target: {args.target_file}")
    
    matches = search_memoized_thoughts(target_text, threshold=args.threshold)
    
    if not matches:
        print("No memoized thoughts found. This is a novel task.")
    else:
        print(f"\n[!] CACHE HIT: Found {len(matches)} similar closed tasks!")
        for idx, match in enumerate(matches, 1):
            print(f"\n{idx}. {match['file']} (Hamming Distance: {match['distance']})")
            print(f"   Memoized Core: {match['summary']}")

if __name__ == "__main__":
    sys.exit(main())
