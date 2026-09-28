#!/usr/bin/env python3
"""Validate Ploos publishing metadata and ISBN registry."""
from __future__ import annotations
import re, sys
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"isbn"/"registry.yaml"
EXAMPLE=ROOT/"metadata"/"book.example.yaml"

def isbn13_ok(value: str) -> bool:
    digits=re.sub(r"[- ]","",value)
    if not re.fullmatch(r"\d{13}",digits): return False
    nums=list(map(int,digits))
    check=(10-(sum(nums[i]*(1 if i%2==0 else 3) for i in range(12))%10))%10
    return nums[-1]==check

def main() -> int:
    errors=[]
    registry=yaml.safe_load(REGISTRY.read_text()) or {}
    example=yaml.safe_load(EXAMPLE.read_text()) or {}
    if not example.get("project"): errors.append("book.example.yaml: missing project")
    if not example.get("titles",{}).get("nb"): errors.append("book.example.yaml: missing Norwegian title")
    if not example.get("titles",{}).get("en"): errors.append("book.example.yaml: missing English title")

    seen={}
    for item in registry.get("publications",[]):
        value=str(item.get("isbn","PENDING"))
        if value=="PENDING": continue
        if not isbn13_ok(value): errors.append(f"invalid ISBN-13: {value}")
        canonical=re.sub(r"[- ]","",value)
        if canonical in seen: errors.append(f"duplicate ISBN: {value}")
        seen[canonical]=item

    if errors:
        print("\n".join("ERROR: "+e for e in errors))
        return 1
    print("Publishing metadata validation OK")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
