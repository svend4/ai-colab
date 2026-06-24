#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.sandbox_runner
# TYPE: active-script
# DOMAIN: portals.execute
# DEPTH_LEVEL: 3
# SUMMARY: Ядро песочницы. Инкапсулирует вызовы docker, применяет лимиты.
# ==========================================

Sandbox Runner Core (Gate 3 + связывание Этапов 1-10).
Единая точка входа для исполнения внешнего кода.

Использование:
    python tools/sandbox_runner.py execute <driver_id> <image> -- <command...>
"""
import os
import sys
import subprocess
import time
from _ioutil import configure_output
from _cli import help_guard

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

configure_output()

from execute_audit import AuditLogger

def run_sandbox(driver_id, image, command):
    logger = AuditLogger(ROOT)
    work_dir, out_dir = logger.prepare_workspace()
    
    # Формируем жесткую команду Docker (на основе docs/execute-sandbox-preflight.md)
    # Запрещаем любые другие опции, кроме заданных политикой
    docker_cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", "2g",
        "--cpus", "2",
        "--pids-limit", "256",
        "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=256m",
        "-v", f"{work_dir}:/work:ro",
        "-v", f"{out_dir}:/out:rw",
        "--workdir", "/work",
        image
    ] + command
    
    # 1. Preflight Check
    preflight_script = os.path.join(HERE, "execute_preflight.py")
    check_cmd = [sys.executable, preflight_script, "check-all", driver_id, "docker"] + docker_cmd
    
    p_check = subprocess.run(check_cmd, capture_output=True, text=True)
    if p_check.returncode != 0:
        logger.rollback()
        print("ERROR: Preflight checks failed!")
        print(p_check.stdout)
        print(p_check.stderr, file=sys.stderr)
        return p_check.returncode
        
    # 2. Execution
    logger.record_start(docker_cmd)
    
    start_t = time.time()
    try:
        # Для безопасности запускаем docker без shell
        p = subprocess.run(docker_cmd, capture_output=True, text=True)
        exit_code = p.returncode
        stdout = p.stdout
        stderr = p.stderr
    except Exception as e:
        exit_code = -1
        stdout = ""
        stderr = str(e)
        
    duration = time.time() - start_t
    
    # 3. Audit & Rollback
    logger.record_finish(exit_code, stdout, stderr, duration)
    logger.collect_diff()
    logger.rollback()
    
    # Output the result
    print(stdout, end="")
    if stderr:
        print(stderr, file=sys.stderr, end="")
        
    return exit_code

def main():
    help_guard(__doc__)
    args = sys.argv[1:]
    if not args or args[0] != "execute":
        print(__doc__)
        return 2
        
    if len(args) < 4:
        print("Usage: sandbox_runner.py execute <driver_id> <image> -- <command...>")
        return 2
        
    driver_id = args[1]
    image = args[2]
    
    sep_idx = args.index("--") if "--" in args else -1
    if sep_idx == -1:
        print("Error: command must be separated by --")
        return 2
        
    command = args[sep_idx+1:]
    
    return run_sandbox(driver_id, image, command)

if __name__ == "__main__":
    sys.exit(main())
