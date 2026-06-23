#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit & Rollback Logger для execute-sandbox (Gates 7/8).
Обеспечивает изоляцию, логирование (audit) и откат (rollback) для будущего sandbox-runner.

Использование (CLI для тестирования):
    python tools/execute_audit.py wrap --workspace path/to/dir -- <command>
"""
import os
import sys
import time
import json
import shutil
import subprocess
from datetime import datetime

class AuditLogger:
    def __init__(self, base_dir):
        self.base_dir = os.path.abspath(base_dir)
        self.sandbox_work = os.path.join(self.base_dir, ".sandbox_work")
        self.sandbox_out = os.path.join(self.base_dir, ".sandbox_out")
        self.reports_dir = os.path.join(self.base_dir, "reports")
        self.audit_file = None
        self.audit_data = {}

    def prepare_workspace(self):
        """Создает изолированные директории для запуска."""
        os.makedirs(self.sandbox_work, exist_ok=True)
        os.makedirs(self.sandbox_out, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.audit_file = os.path.join(self.reports_dir, f"audit_{timestamp}.json")
        return self.sandbox_work, self.sandbox_out

    def record_start(self, command_args):
        """Фиксирует начало выполнения."""
        self.audit_data = {
            "start_time": datetime.now().isoformat(),
            "command": command_args,
            "workspace": self.base_dir,
            "status": "running"
        }
        self._write_audit()

    def record_finish(self, exit_code, stdout, stderr, duration):
        """Фиксирует завершение выполнения."""
        self.audit_data["end_time"] = datetime.now().isoformat()
        self.audit_data["duration_seconds"] = duration
        self.audit_data["exit_code"] = exit_code
        self.audit_data["status"] = "finished" if exit_code == 0 else "failed"
        
        # Save stdout/stderr into separate files to avoid huge JSONs
        if stdout or stderr:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_file = os.path.join(self.reports_dir, f"output_{timestamp}.log")
            with open(out_file, "w", encoding="utf-8") as f:
                f.write("=== STDOUT ===\n")
                f.write(stdout)
                f.write("\n=== STDERR ===\n")
                f.write(stderr)
            self.audit_data["output_file"] = out_file

        self._write_audit()

    def collect_diff(self):
        """Собирает список измененных или созданных файлов в sandbox_out."""
        if not os.path.exists(self.sandbox_out):
            return []
            
        diff = []
        for root, dirs, files in os.walk(self.sandbox_out):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.sandbox_out)
                size = os.path.getsize(full_path)
                diff.append({"file": rel_path, "size": size})
                
        self.audit_data["diff"] = diff
        self._write_audit()
        return diff

    def rollback(self):
        """Удаляет временные директории (rollback)."""
        if os.path.exists(self.sandbox_work):
            shutil.rmtree(self.sandbox_work)
        if os.path.exists(self.sandbox_out):
            shutil.rmtree(self.sandbox_out)
        self.audit_data["rollback_completed"] = True
        self._write_audit()

    def _write_audit(self):
        if self.audit_file:
            with open(self.audit_file, "w", encoding="utf-8") as f:
                json.dump(self.audit_data, f, ensure_ascii=False, indent=2)

def wrap_and_execute(base_dir, command):
    """Обертка для безопасного локального запуска команды (для тестов)."""
    logger = AuditLogger(base_dir)
    work_dir, out_dir = logger.prepare_workspace()
    logger.record_start(command)
    
    start_t = time.time()
    try:
        p = subprocess.run(command, cwd=work_dir, capture_output=True, text=True)
        exit_code = p.returncode
        stdout = p.stdout
        stderr = p.stderr
    except Exception as e:
        exit_code = -1
        stdout = ""
        stderr = str(e)
        
    duration = time.time() - start_t
    logger.record_finish(exit_code, stdout, stderr, duration)
    logger.collect_diff()
    logger.rollback()
    
    return logger.audit_data

def main():
    args = sys.argv[1:]
    if not args or args[0] != "wrap":
        print(__doc__)
        return 2
        
    if "--workspace" not in args:
        print("Error: --workspace is required")
        return 2
        
    ws_idx = args.index("--workspace")
    workspace = args[ws_idx+1]
    
    sep_idx = args.index("--") if "--" in args else -1
    if sep_idx == -1:
        print("Error: command must be separated by --")
        return 2
        
    command = args[sep_idx+1:]
    
    audit_data = wrap_and_execute(workspace, command)
    print(json.dumps(audit_data, indent=2))
    return audit_data.get("exit_code", 1)

if __name__ == "__main__":
    sys.exit(main())
