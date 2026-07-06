import subprocess
import sys
import os

def run_cmd(cmd, desc):
    print(f"=== {desc} ===")
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if result.returncode == 0:
        print("OK\n")
    else:
        print("FAILED\n")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)

def main():
    print("Starting pre-commit smoke tests...\n")
    
    # 1. Validate canon
    run_cmd(f"{sys.executable} tools/validate.py", "Validate Canon")
    
    # 2. Check index generation drift
    run_cmd(f"{sys.executable} tools/generate.py --check", "Check Generate Indexes Drift")
    
    # 3. Drift check
    run_cmd(f"{sys.executable} tools/drift_check.py", "Check Drift")
    
    # 4. Critical self-running tests (subset)
    critical_tests = [
        "tools/tests/test_validate.py",
        "tools/tests/test_pipeline_fencing.py",
        "tools/tests/test_permissions.py",
        "tools/tests/test_safe_write.py",
        "tools/tests/test_commit_queue.py"
    ]
    for test in critical_tests:
        if os.path.exists(test):
            run_cmd(f"{sys.executable} {test}", f"Run {test}")
            
    print("Smoke tests passed successfully. The environment is healthy.")

if __name__ == "__main__":
    main()
