#!/usr/bin/env python3
import os
import time
import json
from datetime import datetime

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTBOX_DIR = os.path.join(ROOT, "queues", "outbox")
INBOX_DIR = os.path.join(ROOT, "queues", "inbox")
TOPICS_DIR = os.path.join(ROOT, "topics")

def get_stress_level():
    """
    Biological Homeostasis: Calculate the system's stress level based on pending work.
    Returns a stress score between 0.0 (total calm) and 1.0 (panic).
    """
    outbox_count = len([f for f in os.listdir(OUTBOX_DIR) if f.endswith(".md")]) if os.path.isdir(OUTBOX_DIR) else 0
    inbox_count = len([f for f in os.listdir(INBOX_DIR) if f.endswith(".md")]) if os.path.isdir(INBOX_DIR) else 0
    topics_count = len([f for f in os.listdir(TOPICS_DIR) if f.endswith(".md")]) if os.path.isdir(TOPICS_DIR) else 0
    
    # Simple biological model
    # High outbox/inbox count = acute stress
    # High topics count = chronic stress
    acute_stress = min(1.0, (outbox_count + inbox_count) / 10.0)
    chronic_stress = min(1.0, topics_count / 100.0)
    
    total_stress = (acute_stress * 0.7) + (chronic_stress * 0.3)
    return min(1.0, total_stress)

def main():
    print("="*50)
    print("🦋 Butterfly Cron: Biological Homeostasis Engine")
    print("="*50)
    print("Starting autonomous heartbeat...")
    
    while True:
        try:
            stress = get_stress_level()
            
            # Map stress (0.0 - 1.0) to breathing interval (60s - 5s)
            # Low stress -> slow breathing (hibernation)
            # High stress -> fast breathing (hyperactivity)
            min_interval = 5.0
            max_interval = 60.0
            
            current_interval = max_interval - (stress * (max_interval - min_interval))
            
            print(f"[{datetime.now().isoformat()}] System Stress: {stress:.2f} | Heartbeat interval: {current_interval:.1f}s")
            
            # Here we would normally call butterfly_graph_builder.py and butterfly_alchemist.py
            # os.system("python tools/butterfly_graph_builder.py --apply")
            
            time.sleep(current_interval)
            
        except KeyboardInterrupt:
            print("\nShutting down homeostasis engine.")
            break
        except Exception as e:
            print(f"Error in biological loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Usually this would be run continuously, but for testing we can just run it once.
    # To run once for test:
    stress = get_stress_level()
    print(f"Homeostasis Test -> Stress: {stress:.2f}")
    
    # Only loop if specifically requested, else just print status and exit for safety in AI environment
    import sys
    if "--loop" in sys.argv:
        main()
