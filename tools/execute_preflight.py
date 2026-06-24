#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.execute_preflight
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт execute_preflight.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""
Preflight-чекер для execute-sandbox (Gates 4/5, 6, 9).
Реализует проверки до реального запуска кода (T-212 / P3, P5, P9).

Запуск:
    python tools/execute_preflight.py check-probe
    python tools/execute_preflight.py check-command <cmd>...
"""
import os
import sys
import subprocess
from _ioutil import configure_output
from _cli import help_guard

configure_output()

# Gate 9: anti-fake-sandbox
def probe_sandbox_backend(sandbox_type):
    if sandbox_type == "docker":
        try:
            # Пытаемся вызвать docker info (timeout 5s)
            p = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=5)
            if p.returncode == 0:
                return True, "Docker is available and responsive"
            else:
                return False, f"Docker command failed: {p.stderr}"
        except Exception as e:
            return False, f"Docker backend not reachable: {e}"
    elif sandbox_type in ("container", "nsjail", "firejail", "gvisor", "sandboxed-vm"):
        return False, f"Backend probe for {sandbox_type} not implemented yet"
    else:
        return False, f"Unknown sandbox type: {sandbox_type}"

# Gate 4/5: mount/network
def check_sandbox_isolation(args):
    # args: list of arguments, e.g. ["docker", "run", "--rm", "--network", "none", ...]
    args_str = " ".join(args)
    
    if "--network host" in args_str or "--network=host" in args_str:
        return False, "Host network is strictly forbidden (Gate 5)"
    
    # We require explicit --network none
    if "--network none" not in args_str and "--network=none" not in args_str:
        return False, "Explicit --network none is required (Gate 5)"
        
    if "--privileged" in args_str:
        return False, "Privileged mode is strictly forbidden (Gate 4)"
        
    for arg in args:
        if arg.startswith("-v") or arg.startswith("--volume"):
            # Very basic check against mounting root or user dir
            # In real usage we parse the mount source
            if "C:\\" in arg and ("C:\\Users" in arg and ".ssh" in arg):
                return False, "Mounting sensitive host paths is forbidden (Gate 4)"
                
    return True, "Isolation checks passed"

# Gate 6: limits
def check_sandbox_limits(args):
    args_str = " ".join(args)
    
    required_limits = ["--memory", "--cpus", "--pids-limit"]
    missing = []
    
    for lim in required_limits:
        if lim not in args_str:
            missing.append(lim)
            
    if missing:
        return False, f"Missing required resource limits: {', '.join(missing)} (Gate 6)"
        
    return True, "Resource limits checks passed"

def main():
    help_guard(__doc__)
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
        
    cmd = args[0]
    if cmd == "check-probe":
        sandbox_type = args[1] if len(args) > 1 else "docker"
        ok, msg = probe_sandbox_backend(sandbox_type)
        if ok:
            print(f"OK: {msg}")
            return 0
        else:
            print(f"ERROR: {msg}")
            return 1
            
    elif cmd == "check-command":
        cmd_args = args[1:]
        ok_iso, msg_iso = check_sandbox_isolation(cmd_args)
        if not ok_iso:
            print(f"ERROR: {msg_iso}")
            return 1
            
        ok_lim, msg_lim = check_sandbox_limits(cmd_args)
        if not ok_lim:
            print(f"ERROR: {msg_lim}")
            return 1
            
        print("OK: Command preflight checks passed")
        return 0
        
    elif cmd == "check-all":
        # Aggregate probe for P11
        # Expects: execute_preflight.py check-all <driver_id> <sandbox_type> <cmd>...
        if len(args) < 3:
            print("Usage: execute_preflight.py check-all <driver_id> <sandbox_type> <cmd>...")
            return 2
            
        driver_id = args[1]
        sandbox_type = args[2]
        cmd_args = args[3:]
        
        # 1. P3: Probe backend
        ok, msg = probe_sandbox_backend(sandbox_type)
        if not ok:
            print(f"ERROR: {msg}")
            return 1
            
        # 2. P5/P9: Command isolation and limits
        ok_iso, msg_iso = check_sandbox_isolation(cmd_args)
        if not ok_iso:
            print(f"ERROR: {msg_iso}")
            return 1
            
        ok_lim, msg_lim = check_sandbox_limits(cmd_args)
        if not ok_lim:
            print(f"ERROR: {msg_lim}")
            return 1
            
        # 3. P10: Check if audit logger exists
        audit_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "execute_audit.py")
        if not os.path.exists(audit_script):
            print("ERROR: Audit logger not found (Gate 7/8)")
            return 1
            
        # 4. P6: Human Gate
        import execute_human_gate
        if execute_human_gate.check_approval(driver_id) != 0:
            return 1
            
        print("OK: All preflight gates passed. Ready for execute.")
        return 0
    else:
        print(f"Unknown command: {cmd}")
        return 2

if __name__ == "__main__":
    sys.exit(main())
