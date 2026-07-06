#!/usr/bin/env python3
import os
import shutil
import sys

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "topics")
ARCHIVE_DIR = os.path.join(TOPICS_DIR, "archive")

try:
    from semantic_engine import AdvancedAlgorithms
except ImportError:
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from semantic_engine import AdvancedAlgorithms

def digital_sleep():
    print("="*60)
    print("💤 DIGITAL SLEEP: Memory Consolidation Engine")
    print("="*60)
    
    if not os.path.isdir(TOPICS_DIR):
        print("Topics directory not found.")
        return
        
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    processed = 0
    for filename in os.listdir(TOPICS_DIR):
        if not filename.endswith(".md"): continue
        if filename.startswith("crystal_"): continue
        
        filepath = os.path.join(TOPICS_DIR, filename)
        if not os.path.isfile(filepath): continue
        
        size = os.path.getsize(filepath)
        # Sleep processes large, complex memories (files > 10KB)
        if size > 10240:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            print(f"[*] Dreaming about {filename} (Size: {size/1024:.1f} KB)...")
            
            # Extract the core crystal of knowledge
            crystal = AdvancedAlgorithms.extract_summary(content, max_sentences=5)
            
            # Write the lightweight crystal side-by-side (non-destructive)
            crystal_filename = f"crystal_{filename}"
            crystal_filepath = os.path.join(TOPICS_DIR, crystal_filename)
            
            with open(crystal_filepath, 'w', encoding='utf-8') as f:
                f.write(f"# [КРИСТАЛЛ ЗНАНИЙ] {filename}\n")
                f.write(f"status: consolidated\n")
                f.write(f"raw_log: [{filename}]({filename})\n\n")
                f.write("## Консолидированная Суть (Extractive Summary)\n")
                f.write(crystal + "\n")
                
            print(f"    -> Consolidated into {crystal_filename} (Reduced context bloat)")
            processed += 1
            
    if processed == 0:
        print("No heavy memories needed consolidation tonight.")
    else:
        print(f"Consolidated {processed} topics.")

if __name__ == "__main__":
    digital_sleep()
