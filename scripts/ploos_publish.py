#!/usr/bin/env python3
"""Ploos Publishing CLI."""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess, zipfile
from pathlib import Path
import yaml
from epub_qa import qa_epub

AUTHOR="Per Gustav Ousdal"
PUBLISHER="Ploos AS"

def load(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate_data(data):
    errors=[]
    for key in ("schema_version","project"):
        if key not in data: errors.append(f"missing {key}")
    pubs=data.get("publications",{})
    if not pubs: errors.append("missing publications")
    for lang,pub in pubs.items():
        if pub.get("author")!=AUTHOR: errors.append(f"{lang}: invalid author")
        if pub.get("publisher")!=PUBLISHER: errors.append(f"{lang}: invalid publisher")
        if not pub.get("title"): errors.append(f"{lang}: missing title")
        for fmt,product in pub.get("products",{}).items():
            if fmt!="web" and "isbn" not in product: errors.append(f"{lang}/{fmt}: missing isbn")
    return errors

def validate(path):
    errors=validate_data(load(path))
    for e in errors: print("ERROR:",e)
    if errors: return 1
    print("Publishing metadata validation OK")
    return 0

def epub_basic(path):
    p=Path(path); errors=[]
    if not p.is_file(): return [f"EPUB not found: {p}"]
    if not zipfile.is_zipfile(p): return ["EPUB is not a ZIP container"]
    with zipfile.ZipFile(p) as z:
        names=set(z.namelist())
        if "mimetype" not in names: errors.append("missing mimetype")
        else:
            if z.read("mimetype")!=b"application/epub+zip": errors.append("invalid mimetype")
        if "META-INF/container.xml" not in names: errors.append("missing META-INF/container.xml")
    return errors

def epubcheck(path):
    basic=epub_basic(path)
    if basic:
        for e in basic: print("ERROR:",e)
        return 1
    exe=shutil.which("epubcheck")
    if not exe:
        print("ERROR: epubcheck executable not found")
        return 2
    return subprocess.run([exe,str(path)],check=False).returncode

def manifest(metadata,out,artifacts):
    p=Path(metadata); data=load(p)
    doc={"schema_version":1,"project":data.get("project"),"metadata":{"path":str(p),"sha256":sha256(p)},"artifacts":[]}
    for item in artifacts:
        a=Path(item)
        if not a.is_file():
            print("ERROR: artifact not found:",a); return 1
        doc["artifacts"].append({"path":str(a),"bytes":a.stat().st_size,"sha256":sha256(a)})
    Path(out).write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(out); return 0

def qualify(metadata,epubs,out):
    data=load(metadata); checks=[]
    meta_errors=validate_data(data)
    checks.append({"check":"metadata","status":"PASS" if not meta_errors else "FAIL","details":meta_errors})
    for epub in epubs:
        basic=epub_basic(epub)
        checks.append({"check":f"epub-container:{epub}","status":"PASS" if not basic else "FAIL","details":basic})
        if not basic:
            errors,warnings=qa_epub(epub)
            checks.append({"check":f"epub-internal-qa:{epub}","status":"PASS" if not errors else "FAIL","details":errors,"warnings":warnings})
    report={"schema_version":1,"project":data.get("project"),"checks":checks}
    report["status"]="PASS" if all(c["status"]=="PASS" for c in checks) else "FAIL"
    Path(out).write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"{report['status']}: {out}")
    return 0 if report["status"]=="PASS" else 1

def main():
    ap=argparse.ArgumentParser(prog="ploos-publish")
    sub=ap.add_subparsers(dest="cmd",required=True)
    v=sub.add_parser("validate"); v.add_argument("metadata")
    e=sub.add_parser("epubcheck"); e.add_argument("epub")
    m=sub.add_parser("manifest"); m.add_argument("metadata"); m.add_argument("artifacts",nargs="*"); m.add_argument("-o","--output",default="release-manifest.json")
    q=sub.add_parser("qualify"); q.add_argument("metadata"); q.add_argument("--epub",action="append",default=[]); q.add_argument("-o","--output",default="qualification-report.json")
    a=ap.parse_args()
    if a.cmd=="validate": return validate(a.metadata)
    if a.cmd=="epubcheck": return epubcheck(a.epub)
    if a.cmd=="manifest": return manifest(a.metadata,a.output,a.artifacts)
    return qualify(a.metadata,a.epub,a.output)

if __name__=="__main__":
    raise SystemExit(main())
