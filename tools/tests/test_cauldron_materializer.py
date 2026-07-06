# ast: allow-subprocess
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess

def run_smoke_test():
    print("=== SMOKE TEST: Cauldron Task Materializer ===")
    fixture_path = "tools/tests/fixtures/synthesis-cauldron.md"
    if not os.path.exists(fixture_path):
        print(f"Skipping: Fixture not found at {fixture_path}")
        return 0

    cmd = [sys.executable, "tools/cauldron_task_materializer.py", "plan", fixture_path, "--json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        import json
        data = json.loads(result.stdout)
        
        assert len(data) == 5, f"Expected 5 items, found {len(data)}"
        assert data[0]['title'] == "Task candidate 1"
        assert data[2]['type'] == "decision"
        assert data[3]['source'] == "route.ratify_build"
        assert data[4]['source'] == "route.divergence_detail"
        
        print("OK: Materializer parsed all fixture sections correctly.")
        return 0
    except Exception as e:
        print(f"FAIL: Materializer test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_smoke_test())
