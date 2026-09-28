#!/usr/bin/env python3
"""Ploos Publishing CLI."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import yaml

def load(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}

def validate(path):
    data=load(path)
    errors=[]
    for key in ("schema_version","project"):
        if key not in data: errors.append(f"missing {key}")
    pubs=data.get("publications",{})
    if not pubs: errors.append("missing publications")
    for lang,pub in pubs.items():
        if pub.get("author")!="Per Gustav Ousdal": errors.append(f"{lang}: invalid author")
        if pub.get("publisher")!="Ploos AS": errors.append(f"{lang}: invalid publisher")
        if not pub.get("title"): errors.append(f"{lang}: missing title")
        for fmt,product in pub.get("products",{}).items():
            if fmt!="web" and "isbn" not in product: errors.append(f"{lang}/{fmt}: missing isbn")
    if errors:
        for e in errors: print("ERROR:",e)
        return 1
    print("Publishing metadata validation OK")
    return 0

def manifest(path,out):
    p=Path(path)
    data=load(p)
    manifest={"project":data.get("project"),"metadata":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
    Path(out).write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(out)
    return 0

def main():
    ap=argparse.ArgumentParser(prog="ploos-publish")
    sub=ap.add_subparsers(dest="cmd",required=True)
    v=sub.add_parser("validate"); v.add_argument("metadata")
    m=sub.add_parser("manifest"); m.add_argument("metadata"); m.add_argument("-o","--output",default="release-manifest.json")
    a=ap.parse_args()
    return validate(a.metadata) if a.cmd=="validate" else manifest(a.metadata,a.output)

if __name__=="__main__":
    raise SystemExit(main())
