#!/usr/bin/env python3
import argparse
import json
import os

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "topics")
ACTIVE_STATUSES = {"open", "proposed", "needs-decision", "waiting", "blocked", "unknown"}

def read_topic(path):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as exc:
        return {"path": path, "title": os.path.basename(path), "status": "read-error"}
    
    title = os.path.basename(path)
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
            
    status = "unknown"
    if "status: " in text:
        try:
            status = text.split("status: ")[1].split("\n")[0].strip()
        except: pass
        
    return {
        "path": path,
        "title": title,
        "status": status,
        "kind": "topic-review"
    }

def scan_topics():
    items = []
    if not os.path.isdir(TOPICS_DIR): return items
    
    for filename in sorted(os.listdir(TOPICS_DIR)):
        if not filename.endswith(".md"): continue
        item = read_topic(os.path.join(TOPICS_DIR, filename))
        if item["status"] in ACTIVE_STATUSES:
            items.append(item)
            
    if len(items) > 1:
        try:
            from semantic_engine import AdvancedAlgorithms
            corpus = []
            for item in items:
                try:
                    with open(item["path"], "r", encoding="utf-8") as f:
                        corpus.append(f.read())
                except:
                    corpus.append(item["title"])
                    
            collocations = AdvancedAlgorithms.extract_pmi_collocations(corpus, min_count=2, top_n=5)
            
            for item, text in zip(items, corpus):
                item["cluster"] = "Other"
                text_lower = text.lower()
                for c in collocations:
                    if c in text_lower:
                        item["cluster"] = f"Concept: '{c}'"
                        break
                        
                # EXTRACTIVE SUMMARIZATION
                item["summary"] = AdvancedAlgorithms.extract_summary(text, max_sentences=2)
                
        except ImportError:
            pass
            
    return items

def render_text(items):
    print("=" * 60)
    print("  FRICTION ADVISOR 2.0: SEMANTIC RISK ROUTING + SUMMARIZATION")
    print("=" * 60)
    
    items.sort(key=lambda x: x.get("cluster", "Other"))
    current_cluster = None
    
    for idx, item in enumerate(items, 1):
        cluster = item.get("cluster", "Other")
        if cluster != current_cluster:
            print(f"\n+++ CLUSTER: {cluster} +++")
            current_cluster = cluster
            
        print("%d. [%s] %s" % (idx, item["status"], item["title"]))
        print("   path: %s" % item["path"])
        if "summary" in item:
            print(f"   summary: {item['summary']}")
        print("-" * 60)

if __name__ == "__main__":
    items = scan_topics()
    render_text(items)
