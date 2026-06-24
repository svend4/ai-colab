#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.sandbox_schema_validator
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Валидатор JSON-манифестов во входящей песочнице (read-only)
# ==========================================
"""

import json
import sys
import os

REQUIRED_KEYS = {"name", "version", "entrypoint", "schema_version"}

def validate_manifest(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {"file": filepath, "status": "error", "message": f"Invalid JSON: {e}"}

    if not isinstance(data, dict):
        return {"file": filepath, "status": "error", "message": "Manifest is not a JSON object"}

    missing_keys = REQUIRED_KEYS - set(data.keys())
    if missing_keys:
        return {
            "file": filepath,
            "status": "error", 
            "message": f"Missing required keys: {', '.join(missing_keys)}"
        }

    return {"file": filepath, "status": "ok"}

def scan_directory(target_dir):
    results = []
    for root, dirs, files in os.walk(target_dir):
        if "manifest.json" in files:
            manifest_path = os.path.join(root, "manifest.json")
            res = validate_manifest(manifest_path)
            results.append(res)
    return results

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No directory provided"}))
        sys.exit(1)
        
    target = sys.argv[1]
    if not os.path.isdir(target):
        print(json.dumps({"error": f"Not a directory: {target}"}))
        sys.exit(1)
        
    results = scan_directory(target)
    print(json.dumps({"scanned_manifests": len(results), "results": results}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()