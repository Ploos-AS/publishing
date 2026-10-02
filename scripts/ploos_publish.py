#!/usr/bin/env python3
"""Ploos Publishing CLI."""
from __future__ import annotations
import argparse, hashlib, html, json, os, shutil, subprocess, zipfile
from datetime import date
from xml.etree import ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse
import yaml
from PIL import Image, ImageOps
from epub_qa import qa_epub

AUTHOR="Per Gustav Ousdal"
PUBLISHER="Ploos AS"
COPYRIGHT_HOLDER="Ploos AS"
LICENSE="CC-BY-4.0"
LIFECYCLE_STATES=("draft","candidate","qualified","published","archived")
LIFECYCLE_TRANSITIONS={"draft":{"candidate"},"candidate":{"draft","qualified"},"qualified":{"draft","published"},"published":{"archived"},"archived":set()}

def normalize_isbn(value):
    return str(value).replace("-","").replace(" ","")

def isbn13_valid(value):
    s=normalize_isbn(value)
    if len(s)!=13 or not s.isdigit() or not s.startswith(("978","979")): return False
    total=sum((1 if i%2==0 else 3)*int(d) for i,d in enumerate(s[:12]))
    return (10-(total%10))%10==int(s[12])

def isbn_registry_validate(path):
    data=load(path); errors=[]; seen={}; targets={}
    publisher=data.get("publisher",{})
    if publisher.get("name")!=PUBLISHER: errors.append("invalid publisher")
    prefix_status=publisher.get("prefix_status")
    if prefix_status not in ("pending","assigned"): errors.append(f"invalid publisher prefix_status: {prefix_status}")
    if prefix_status=="pending" and publisher.get("publisher_prefix") is not None:
        errors.append("publisher_prefix must be null while prefix_status is pending")
    if prefix_status=="assigned" and not publisher.get("publisher_prefix"):
        errors.append("publisher_prefix required when prefix_status is assigned")
    pool=data.get("isbn_pool",[])
    if prefix_status=="pending" and pool: errors.append("isbn_pool must be empty while prefix_status is pending")
    for i,isbn in enumerate(pool):
        if not isbn13_valid(isbn): errors.append(f"isbn_pool {i}: invalid ISBN-13: {isbn}")
        else:
            normalized=normalize_isbn(isbn)
            if normalized in seen: errors.append(f"isbn_pool {i}: duplicate ISBN-13: {isbn}")
            else: seen[normalized]="pool"
    publications={x.get("project"):x for x in data.get("publications",[]) if x.get("project")}
    for i,a in enumerate(data.get("allocations",[])):
        isbn=a.get("isbn")
        if not isbn or isbn=="PENDING": errors.append(f"allocation {i}: ISBN must be assigned")
        elif not isbn13_valid(isbn): errors.append(f"allocation {i}: invalid ISBN-13: {isbn}")
        else:
            normalized=normalize_isbn(isbn)
            if normalized in seen and seen[normalized]!="pool": errors.append(f"allocation {i}: duplicate ISBN-13: {isbn}")
            else: seen[normalized]=f"allocation {i}"
        target=tuple(a.get(k) for k in ("project","edition","language","product"))
        for key,value in zip(("project","edition","language","product"),target):
            if not value: errors.append(f"allocation {i}: missing {key}")
        if all(target):
            if target in targets: errors.append(f"allocation {i}: duplicate target: {'/'.join(str(x) for x in target)}")
            targets[target]=i
        project,edition,language,product=target
        publication=publications.get(project)
        if publication is None: errors.append(f"allocation {i}: unknown project: {project}")
        else:
            if language not in publication.get("titles",{}): errors.append(f"allocation {i}: unsupported language for {project}: {language}")
        if not isinstance(edition,int) or edition < 1: errors.append(f"allocation {i}: edition must be a positive integer")
        if product not in ("epub","pdf","kindle"): errors.append(f"allocation {i}: unsupported ISBN product: {product}")
    for e in errors: print("ERROR:",e)
    if errors: return 1
    print(f"ISBN registry validation OK: {len(data.get('allocations',[]))} allocations, {len(pool)} pool entries"); return 0

def isbn_import(registry,isbn_file,write=False):
    p=Path(registry); data=load(p)
    publisher=data.get("publisher",{})
    if publisher.get("prefix_status")!="assigned" or not publisher.get("publisher_prefix"):
        print("ERROR: official publisher prefix must be assigned before ISBN import"); return 1
    raw=Path(isbn_file).read_text(encoding="utf-8").splitlines()
    incoming=[line.strip() for line in raw if line.strip() and not line.lstrip().startswith("#")]
    bad=[x for x in incoming if not isbn13_valid(x)]
    if bad:
        for x in bad: print("ERROR: invalid ISBN-13:",x)
        return 1
    normalized=[x.replace("-","").replace(" ","") for x in incoming]
    if len(normalized)!=len(set(normalized)):
        print("ERROR: duplicate ISBN in import"); return 1
    allocated={str(a.get("isbn")).replace("-","").replace(" ","") for a in data.get("allocations",[])}
    pool=[str(x).replace("-","").replace(" ","") for x in data.get("isbn_pool",[])]
    merged=pool+[x for x in normalized if x not in pool and x not in allocated]
    print(f"ISBN import: {len(normalized)} supplied, {len(merged)-len(pool)} new")
    if write:
        data["isbn_pool"]=merged
        p.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding="utf-8")
        print(p)
    return 0

def isbn_allocate(registry,project,edition,language,product,write=False):
    p=Path(registry); data=load(p)
    if edition < 1:
        print("ERROR: edition must be a positive integer"); return 1
    publication=next((x for x in data.get("publications",[]) if x.get("project")==project),None)
    if publication is None:
        print(f"ERROR: unknown project: {project}"); return 1
    if language not in publication.get("titles",{}):
        print(f"ERROR: unsupported language for {project}: {language}"); return 1
    if product not in ("epub","pdf"):
        print(f"ERROR: unsupported ISBN product: {product}"); return 1
    target=(project,edition,language,product)
    for a in data.get("allocations",[]):
        if tuple(a.get(k) for k in ("project","edition","language","product"))==target:
            print(f"ERROR: target already allocated: {a.get('isbn')}"); return 1
    allocated={str(a.get("isbn")).replace("-","").replace(" ","") for a in data.get("allocations",[])}
    available=[str(x).replace("-","").replace(" ","") for x in data.get("isbn_pool",[]) if str(x).replace("-","").replace(" ","") not in allocated]
    if not available:
        print("ERROR: no unallocated ISBNs in registry pool"); return 1
    isbn=available[0]
    if not isbn13_valid(isbn): print("ERROR: next ISBN in pool is invalid:",isbn); return 1
    print(f"{project}/{edition}/{language}/{product} -> {isbn}")
    if write:
        data.setdefault("allocations",[]).append({"isbn":isbn,"project":project,"edition":edition,"language":language,"product":product})
        p.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding="utf-8")
        print(p)
    return 0

def isbn_metadata_check(registry,metadata):
    reg=load(registry); meta=load(metadata); errors=[]
    project=meta.get("project")
    edition=meta.get("edition",{}).get("number")
    allocations={(a.get("project"),a.get("edition"),a.get("language"),a.get("product")):normalize_isbn(a.get("isbn"))
                 for a in reg.get("allocations",[]) if a.get("isbn") and a.get("isbn")!="PENDING"}
    for language,pub in meta.get("publications",{}).items():
        for product,details in pub.get("products",{}).items():
            if product=="web": continue
            value=details.get("isbn")
            allocated=allocations.get((project,edition,language,product))
            if allocated:
                if value=="PENDING": errors.append(f"{language}/{product}: registry has allocated ISBN {allocated} but metadata is PENDING")
                elif not isbn13_valid(value) or normalize_isbn(value)!=allocated:
                    errors.append(f"{language}/{product}: metadata ISBN does not match registry allocation")
            elif value not in (None, "PENDING"):
                errors.append(f"{language}/{product}: metadata has ISBN but registry has no allocation")
    for e in errors: print("ERROR:",e)
    if errors: return 1
    print("ISBN metadata cross-check OK"); return 0

def load(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate_data(data):
    errors=[]
    for key in ("schema_version","project"):
        if key not in data: errors.append(f"missing {key}")
    edition=data.get("edition",{})
    if edition and "revision" in edition and (not isinstance(edition["revision"],int) or edition["revision"] < 1): errors.append("edition: revision must be a positive integer")
    if edition and "number" in edition and (not isinstance(edition["number"],int) or edition["number"] < 1): errors.append("edition: number must be a positive integer")
    supersedes=edition.get("supersedes")
    if supersedes is not None:
        if not isinstance(supersedes,dict): errors.append("edition: supersedes must be an object")
        else:
            if not supersedes.get("work_id"): errors.append("edition: supersedes.work_id required")
            if not isinstance(supersedes.get("edition"),int) or supersedes.get("edition",0)<1: errors.append("edition: supersedes.edition must be a positive integer")
            if supersedes.get("work_id")==data.get("work",{}).get("id") and supersedes.get("edition")==edition.get("number"):
                errors.append("edition: cannot supersede itself")
    lifecycle=data.get("lifecycle",{})
    if lifecycle and lifecycle.get("status") not in LIFECYCLE_STATES: errors.append("lifecycle: invalid status")
    pubs=data.get("publications",{})
    if not pubs: errors.append("missing publications")
    for lang,pub in pubs.items():
        if pub.get("author")!=AUTHOR: errors.append(f"{lang}: invalid author")
        if pub.get("publisher")!=PUBLISHER: errors.append(f"{lang}: invalid publisher")
        if pub.get("copyright_holder")!=COPYRIGHT_HOLDER: errors.append(f"{lang}: invalid copyright holder")
        if pub.get("license")!=LICENSE: errors.append(f"{lang}: invalid license")
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


def provenance(metadata,git_commit,qualification,artifacts,output):
    meta=Path(metadata); qual=Path(qualification)
    if not meta.is_file(): print("ERROR: metadata not found:",meta); return 1
    if not qual.is_file(): print("ERROR: qualification report not found:",qual); return 1
    if len(git_commit)!=40 or any(ch not in "0123456789abcdefABCDEF" for ch in git_commit):
        print("ERROR: git commit must be a 40-character SHA-1"); return 1
    try: qdoc=json.loads(qual.read_text(encoding="utf-8"))
    except Exception as exc: print("ERROR: invalid qualification report:",exc); return 1
    if qdoc.get("status")!="PASS": print("ERROR: provenance requires PASS qualification"); return 1
    data=load(meta); records=[]
    for item in artifacts:
        p=Path(item)
        if not p.is_file(): print("ERROR: provenance artifact not found:",p); return 1
        records.append({"path":str(p),"bytes":p.stat().st_size,"sha256":sha256(p)})
    records.sort(key=lambda x:x["path"])
    doc={"schema_version":1,"project":data.get("project"),"work_id":data.get("work",{}).get("id"),
         "edition":data.get("edition"),"git_commit":git_commit.lower(),
         "metadata":{"path":str(meta),"bytes":meta.stat().st_size,"sha256":sha256(meta)},
         "qualification":{"path":str(qual),"bytes":qual.stat().st_size,"sha256":sha256(qual),"status":"PASS"},
         "artifacts":records}
    out=Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(doc,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(out); return 0

def provenance_verify(manifest_path):
    p=Path(manifest_path)
    try: doc=json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc: print("ERROR: invalid provenance manifest:",exc); return 1
    failures=[]
    commit=str(doc.get("git_commit",""))
    if len(commit)!=40 or any(ch not in "0123456789abcdef" for ch in commit.lower()): failures.append("invalid git_commit")
    records=[("metadata",doc.get("metadata",{})),("qualification",doc.get("qualification",{}))]
    records += [(f"artifact:{r.get('path')}",r) for r in doc.get("artifacts",[])]
    for label,record in records:
        fp=Path(record.get("path",""))
        if not fp.is_file(): failures.append(f"{label}: missing {fp}"); continue
        if fp.stat().st_size!=record.get("bytes"): failures.append(f"{label}: size mismatch")
        if sha256(fp)!=record.get("sha256"): failures.append(f"{label}: sha256 mismatch")
    q=doc.get("qualification",{})
    if q.get("status")!="PASS": failures.append("qualification: status is not PASS")
    else:
        try:
            live=json.loads(Path(q.get("path","")).read_text(encoding="utf-8"))
            if live.get("status")!="PASS": failures.append("qualification: live report is not PASS")
        except Exception as exc: failures.append(f"qualification: unreadable report: {exc}")
    for failure in failures: print("ERROR:",failure)
    if failures: return 1
    print(f"Provenance verification PASS: {len(records)} files, commit {commit}"); return 0


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

def build(config,target=None):
    data=load(config); spec=data.get("build",{})
    targets=spec.get("targets",{})
    selected={target:targets[target]} if target else targets
    if target and target not in targets:
        print("ERROR: unknown build target:",target); return 1
    for command in spec.get("clean",[]):
        print("+",command)
        if subprocess.run(command,shell=True,check=False).returncode: return 1
    for name,item in selected.items():
        command=item.get("command")
        if not command:
            print(f"ERROR: {name}: missing command"); return 1
        print(f"[{name}] + {command}")
        if subprocess.run(command,shell=True,check=False).returncode:
            print(f"ERROR: {name}: build command failed"); return 1
        missing=[p for p in item.get("outputs",[]) if not Path(p).exists()]
        if missing:
            for p in missing: print(f"ERROR: {name}: missing output {p}")
            return 1
        print(f"PASS: {name}")
    return 0

def package(metadata,config,channel,language,epub=None,pdf=None,cover=None):
    data=load(metadata); cfg=load(config).get("package",{})
    state=data.get("lifecycle",{}).get("status","draft")
    if state not in ("qualified","published"):
        print(f"ERROR: store packaging requires qualified/published lifecycle, got: {state}"); return 1
    channels=cfg.get("channels",{})
    if channel not in channels:
        print("ERROR: unknown channel:",channel); return 1
    pub=data.get("publications",{}).get(language)
    if not pub:
        print("ERROR: unknown publication language:",language); return 1
    supplied={"epub":epub,"pdf":pdf,"cover":cover}
    profile=channels[channel]
    required=profile.get("artifacts",[])
    optional=profile.get("optional_artifacts",[])
    allowed=set(required)|set(optional)
    missing=[kind for kind in required if not supplied.get(kind)]
    if missing:
        print("ERROR: missing required artifacts:",", ".join(missing)); return 1
    unexpected=[kind for kind,path in supplied.items() if path and kind not in allowed]
    if unexpected:
        print("ERROR: artifacts not allowed for channel:",", ".join(unexpected)); return 1
    supplied={kind:path for kind,path in supplied.items() if kind in allowed}
    root=Path(cfg.get("output_dir","packages"))/channel/language
    if root.exists(): shutil.rmtree(root)
    root.mkdir(parents=True)
    copied=[]
    for kind,path in supplied.items():
        if not path: continue
        src=Path(path)
        if not src.is_file():
            print(f"ERROR: {kind} not found: {src}"); return 1
        dst=root/src.name; shutil.copyfile(src,dst)
        os.utime(dst,(0,0))
        copied.append({"kind":kind,"file":dst.name,"bytes":dst.stat().st_size,"sha256":sha256(dst)})
    meta={"project":data.get("project"),"language":language,"channel":channel,
          "title":pub.get("title"),"subtitle":pub.get("subtitle"),"author":pub.get("author"),"publisher":pub.get("publisher"),
          "copyright_holder":pub.get("copyright_holder"),"license":pub.get("license"),
          "edition":data.get("edition"),"products":pub.get("products",{})}
    copied.sort(key=lambda x:(x["kind"],x["file"]))
    package_manifest={"schema_version":1,"channel":channel,"language":language,"artifacts":copied}
    (root/"manifest.json").write_text(json.dumps(package_manifest,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    (root/"metadata.json").write_text(json.dumps(meta,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    for generated in (root/"metadata.json",root/"manifest.json"): os.utime(generated,(0,0))
    print(root); return 0


def lifecycle(metadata,to_status,write=False):
    p=Path(metadata); data=load(p)
    current=data.get("lifecycle",{}).get("status","draft")
    if to_status not in LIFECYCLE_STATES:
        print("ERROR: invalid lifecycle status:",to_status); return 1
    if to_status not in LIFECYCLE_TRANSITIONS.get(current,set()):
        print(f"ERROR: invalid lifecycle transition: {current} -> {to_status}"); return 1
    print(f"{current} -> {to_status}")
    if write:
        data.setdefault("lifecycle",{})["status"]=to_status
        p.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding="utf-8")
        print(p)
    return 0


def cover_check(image,config):
    cfg=load(config).get("master",{}); p=Path(image)
    if not p.is_file(): print("ERROR: cover not found:",p); return 1
    errors=[]
    try:
        with Image.open(p) as im:
            fmt=im.format; w,h=im.size
            if fmt not in cfg.get("formats",["JPEG","PNG"]): errors.append(f"unsupported format: {fmt}")
            if w < cfg.get("min_width",1): errors.append(f"width {w} below minimum")
            if h < cfg.get("min_height",1): errors.append(f"height {h} below minimum")
            target=float(cfg.get("aspect_ratio",w/h)); tol=float(cfg.get("aspect_tolerance",0.03))
            if abs((w/h)-target)>tol: errors.append(f"aspect ratio {w/h:.4f} outside tolerance")
    except Exception as exc: errors.append(f"cannot read image: {exc}")
    for e in errors: print("ERROR:",e)
    if errors: return 1
    print(f"Cover validation OK: {w}x{h} {fmt}"); return 0

def cover_build(image,config,output_dir):
    if cover_check(image,config): return 1
    cfg=load(config); root=Path(output_dir); root.mkdir(parents=True,exist_ok=True)
    with Image.open(image) as src:
        src=src.convert("RGB")
        for channel,spec in cfg.get("channels",{}).items():
            size=(int(spec["width"]),int(spec["height"]))
            out=ImageOps.fit(src,size,method=Image.Resampling.LANCZOS,centering=(0.5,0.5))
            fmt=spec.get("format","JPEG").upper(); ext=".jpg" if fmt=="JPEG" else ".png"
            dst=root/f"{channel}{ext}"
            kwargs={"quality":int(spec.get("quality",92)),"optimize":True} if fmt=="JPEG" else {"optimize":True}
            out.save(dst,format=fmt,**kwargs); print(dst)
    return 0







def archive_manifest(metadata,artifacts,output):
    meta=Path(metadata)
    if not meta.is_file(): print("ERROR: metadata not found:",meta); return 1
    files=[]
    for item in artifacts:
        p=Path(item)
        if not p.is_file(): print("ERROR: archive artifact not found:",p); return 1
        files.append({"path":str(p),"bytes":p.stat().st_size,"sha256":sha256(p)})
    files.sort(key=lambda x:x["path"])
    data=load(meta)
    doc={"schema_version":1,"project":data.get("project"),"work_id":data.get("work",{}).get("id"),
         "edition":data.get("edition"),"metadata":{"path":str(meta),"bytes":meta.stat().st_size,"sha256":sha256(meta)},
         "artifacts":files}
    out=Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(doc,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(out); return 0

def audit_archive(manifest):
    p=Path(manifest)
    if not p.is_file(): print("ERROR: archive manifest not found:",p); return 1
    try: doc=json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc: print("ERROR: invalid archive manifest:",exc); return 1
    failures=[]
    records=[("metadata",doc.get("metadata",{}))]
    records += [(f"artifact:{r.get('path')}",r) for r in doc.get("artifacts",[])]
    for label,record in records:
        path=Path(record.get("path",""))
        if not path.is_file(): failures.append(f"{label}: missing {path}"); continue
        if path.stat().st_size!=record.get("bytes"): failures.append(f"{label}: size mismatch")
        if sha256(path)!=record.get("sha256"): failures.append(f"{label}: sha256 mismatch")
    for failure in failures: print("ERROR:",failure)
    if failures: return 1
    print(f"Archive audit PASS: {len(records)} files verified")
    return 0

ONIX_LANG={"nb":"nor","nn":"nno","en":"eng"}
ONIX_PRODUCT_FORM={"epub":"ED","pdf":"ED"}
ONIX_PRODUCT_DETAIL={"epub":"E101","pdf":"E107"}

def onix_schema_bundle_verify(manifest_path):
    manifest_path=Path(manifest_path)
    if not manifest_path.is_file():
        print("ERROR: ONIX schema manifest not found:",manifest_path); return 1
    try: manifest=yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except Exception as exc: print("ERROR: invalid ONIX schema manifest:",exc); return 1
    files=manifest.get("files")
    if not isinstance(files,list) or not files:
        print("ERROR: ONIX schema manifest has no files"); return 1
    failures=[]
    if manifest.get("manifest_version")!=1: failures.append("manifest_version must be 1")
    if manifest.get("entry_point")!="ONIX_BookProduct_3.0_reference.xsd": failures.append("entry_point must be ONIX_BookProduct_3.0_reference.xsd")
    required_files={
        "ONIX_BookProduct_3.0_reference.xsd",
        "ONIX_BookProduct_CodeLists.xsd",
        "ONIX_XHTML_Subset.xsd",
        "ONIX_BookProduct_3.0_short.xsd",
    }
    recorded_paths=[str(record.get("path")) for record in files if isinstance(record,dict) and record.get("path")]
    normalized_paths=[Path(p).as_posix().removeprefix("./") for p in recorded_paths]
    recorded_files=set(normalized_paths)
    if len(normalized_paths)!=len(recorded_files): failures.append("duplicate schema file record")
    for required in sorted(required_files-recorded_files):
        failures.append(f"required schema file not recorded: {required}")
    schema=manifest.get("schema",{})
    if str(schema.get("release"))!="3.0": failures.append("schema.release must be 3.0")
    if schema.get("revision")!=7: failures.append("schema.revision must be 7")
    if str(schema.get("revised"))!="2020-05-18": failures.append("schema.revised must be 2020-05-18")
    codelists=manifest.get("codelists",{})
    if codelists.get("issue")!=74: failures.append("codelists.issue must be 73")
    sources=manifest.get("sources",{})
    authoritative=sources.get("authoritative",{}) if isinstance(sources,dict) else {}
    if authoritative.get("authority")!="EDItEUR": failures.append("authoritative source must be EDItEUR")
    location=authoritative.get("location")
    if not location:
        failures.append("authoritative source location required")
    else:
        parsed=urlparse(str(location))
        host=(parsed.hostname or "").lower()
        if parsed.scheme!="https": failures.append("authoritative source location must use HTTPS")
        if host!="editeur.org" and not host.endswith(".editeur.org"):
            failures.append("authoritative source location must be hosted by EDItEUR")
    downstream=sources.get("downstream_verification") if isinstance(sources,dict) else None
    if downstream is not None:
        if not isinstance(downstream,dict):
            failures.append("downstream verification must be a mapping")
        else:
            if downstream.get("authority")!="Bokbasen": failures.append("downstream verification authority must be Bokbasen")
            downstream_location=downstream.get("location")
            if not downstream_location:
                failures.append("downstream verification location required")
            else:
                parsed=urlparse(str(downstream_location)); host=(parsed.hostname or "").lower()
                if parsed.scheme!="https": failures.append("downstream verification location must use HTTPS")
                if host!="api.boknett.no": failures.append("downstream verification location must use api.boknett.no")
            downstream_digest=str(downstream.get("sha256",""))
            if len(downstream_digest)!=64 or any(ch not in "0123456789abcdefABCDEF" for ch in downstream_digest):
                failures.append("downstream verification sha256 invalid")
            downstream_file=downstream.get("file")
            if not downstream_file:
                failures.append("downstream verification file required")
            elif downstream_file!="ONIX_BookProduct_3.0_reference.xsd":
                failures.append("downstream verification must target ONIX reference schema entry point")
            elif downstream_file not in recorded_files:
                failures.append("downstream verification file not recorded")
            else:
                target=manifest_path.parent/str(downstream_file)
                if target.is_file() and sha256(target).lower()!=downstream_digest.lower():
                    failures.append("downstream verification sha256 does not match vendored file")
    retrieved_at=authoritative.get("retrieved_at")
    if not retrieved_at:
        failures.append("authoritative source retrieval date required")
    else:
        try:
            retrieved_date=date.fromisoformat(str(retrieved_at))
            if retrieved_date>date.today(): failures.append("authoritative source retrieval date cannot be in the future")
        except ValueError:
            failures.append("authoritative source retrieval date must be ISO YYYY-MM-DD")
    for record in files:
        if not isinstance(record,dict) or not record.get("path") or not record.get("sha256"):
            failures.append("invalid file record"); continue
        digest=str(record["sha256"])
        if len(digest)!=64 or any(ch not in "0123456789abcdefABCDEF" for ch in digest):
            failures.append(f"invalid sha256: {record['path']}"); continue
        raw_path=str(record["path"])
        rel=Path(raw_path)
        canonical=rel.as_posix()
        if rel.is_absolute() or ".." in rel.parts or "\\" in raw_path or raw_path.startswith("./") or canonical!=raw_path:
            failures.append(f"non-canonical schema path: {record['path']}"); continue
        p=manifest_path.parent/rel
        if not p.is_file(): failures.append(f"missing {record['path']}"); continue
        actual=sha256(p)
        if actual.lower()!=str(record["sha256"]).lower():
            failures.append(f"sha256 mismatch: {record['path']}")
    for failure in failures: print("ERROR:",failure)
    if failures: return 1
    print(f"ONIX schema bundle OK: {len(files)} file(s)")
    return 0

def onix_bundle_validate(path,manifest_path):
    manifest_path=Path(manifest_path)
    if onix_schema_bundle_verify(manifest_path)!=0: return 1
    manifest=yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    return onix_validate_file(path,manifest_path.parent/manifest["entry_point"])

def onix_schema_validate(path,schema_path):
    try:
        from lxml import etree
    except ImportError:
        print("ERROR: lxml is required for ONIX XSD validation"); return 1
    try:
        schema_doc=etree.parse(str(schema_path))
        schema=etree.XMLSchema(schema_doc)
        document=etree.parse(str(path))
    except Exception as exc:
        print("ERROR: unable to load ONIX XML/XSD:",exc); return 1
    if not schema.validate(document):
        for error in schema.error_log:
            print(f"ERROR: XSD line {error.line}: {error.message}")
        return 1
    print(f"ONIX XSD validation OK: {schema_path}"); return 0

def onix_validate_file(path,schema_path=None):
    p=Path(path)
    try: root=ET.parse(p).getroot()
    except Exception as exc: print("ERROR: invalid ONIX XML:",exc); return 1
    ns={"o":"http://ns.editeur.org/onix/3.0/reference"}
    errors=[]
    if root.tag!="{http://ns.editeur.org/onix/3.0/reference}ONIXMessage": errors.append("invalid ONIX namespace/root")
    if root.get("release")!="3.0": errors.append("ONIX release must be 3.0")
    products=root.findall("o:Product",ns)
    if not products: errors.append("missing Product")
    for i,product in enumerate(products):
        def req(path,label):
            el=product.find(path,ns)
            if el is None or not (el.text or "").strip(): errors.append(f"product {i}: missing {label}")
            return el
        req("o:RecordReference","RecordReference"); req("o:NotificationType","NotificationType")
        idv=req("o:ProductIdentifier/o:IDValue","ISBN-13")
        if idv is not None and not isbn13_valid(idv.text): errors.append(f"product {i}: invalid ISBN-13")
        req("o:DescriptiveDetail/o:ProductForm","ProductForm")
        req("o:DescriptiveDetail/o:TitleDetail/o:TitleElement/o:TitleText","TitleText")
        req("o:DescriptiveDetail/o:Contributor/o:ContributorRole","ContributorRole")
        req("o:DescriptiveDetail/o:Language/o:LanguageCode","LanguageCode")
        req("o:PublishingDetail/o:Publisher/o:PublisherName","PublisherName")
    for e in errors: print("ERROR:",e)
    if errors: return 1
    print(f"ONIX structural validation OK: {len(products)} product(s)")
    if schema_path:
        return onix_schema_validate(p,Path(schema_path))
    return 0

def onix(metadata,language,product_name,output):
    data=load(metadata); errors=validate_data(data)
    if errors:
        for e in errors: print("ERROR:",e)
        return 1
    pub=data.get("publications",{}).get(language)
    if not pub: print("ERROR: unknown publication language:",language); return 1
    product=pub.get("products",{}).get(product_name)
    if not product: print("ERROR: product not found:",product_name); return 1
    isbn=product.get("isbn")
    if not isbn or isbn=="PENDING":
        print("ERROR: ONIX export requires an assigned ISBN"); return 1
    root=ET.Element("ONIXMessage",{"release":"3.0","xmlns":"http://ns.editeur.org/onix/3.0/reference"})
    header=ET.SubElement(root,"Header")
    sender=ET.SubElement(header,"Sender"); ET.SubElement(sender,"SenderName").text=PUBLISHER
    product_el=ET.SubElement(root,"Product")
    ET.SubElement(product_el,"RecordReference").text=f"{data.get('work',{}).get('id',data.get('project'))}-{language}-{product_name}"
    ET.SubElement(product_el,"NotificationType").text="03"
    ident=ET.SubElement(product_el,"ProductIdentifier")
    ET.SubElement(ident,"ProductIDType").text="15"; ET.SubElement(ident,"IDValue").text=str(isbn)
    desc=ET.SubElement(product_el,"DescriptiveDetail")
    ET.SubElement(desc,"ProductComposition").text="00"
    ET.SubElement(desc,"ProductForm").text=ONIX_PRODUCT_FORM.get(product_name,"ED")
    ET.SubElement(desc,"ProductFormDetail").text=ONIX_PRODUCT_DETAIL.get(product_name,"E101")
    title_detail=ET.SubElement(desc,"TitleDetail"); ET.SubElement(title_detail,"TitleType").text="01"
    title_el=ET.SubElement(title_detail,"TitleElement"); ET.SubElement(title_el,"TitleElementLevel").text="01"
    ET.SubElement(title_el,"TitleText").text=pub.get("title")
    if pub.get("subtitle"): ET.SubElement(title_el,"Subtitle").text=pub.get("subtitle")
    contributor=ET.SubElement(desc,"Contributor"); ET.SubElement(contributor,"SequenceNumber").text="1"
    ET.SubElement(contributor,"ContributorRole").text="A01"; ET.SubElement(contributor,"PersonName").text=pub.get("author")
    lang=ET.SubElement(desc,"Language"); ET.SubElement(lang,"LanguageRole").text="01"
    ET.SubElement(lang,"LanguageCode").text=ONIX_LANG.get(language,language)
    edition=data.get("edition",{})
    if edition.get("number"): ET.SubElement(desc,"EditionNumber").text=str(edition["number"])
    publishing=ET.SubElement(product_el,"PublishingDetail")
    publisher=ET.SubElement(publishing,"Publisher"); ET.SubElement(publisher,"PublishingRole").text="01"
    ET.SubElement(publisher,"PublisherName").text=pub.get("publisher")
    if edition.get("year"):
        pd=ET.SubElement(publishing,"PublishingDate"); ET.SubElement(pd,"PublishingDateRole").text="01"
        ET.SubElement(pd,"Date",{"dateformat":"05"}).text=str(edition["year"])
    tree=ET.ElementTree(root); ET.indent(tree,space="  ")
    out=Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    tree.write(out,encoding="utf-8",xml_declaration=True)
    print(out); return 0

def catalog(metadata_files,output,include_unpublished=False):
    books=[]
    for metadata in metadata_files:
        data=load(metadata); errors=validate_data(data)
        if errors:
            print(f"ERROR: invalid metadata: {metadata}"); return 1
        state=data.get("lifecycle",{}).get("status","draft")
        if state!="published" and not include_unpublished: continue
        for language,pub in data.get("publications",{}).items():
            products={}
            for name,product in pub.get("products",{}).items():
                products[name]={"isbn":product.get("isbn")}
            books.append({"project":data.get("project"),"work_id":data.get("work",{}).get("id"),
                          "language":language,"title":pub.get("title"),"subtitle":pub.get("subtitle"),"author":pub.get("author"),
                          "publisher":pub.get("publisher"),"edition":data.get("edition"),
                          "lifecycle":state,"products":products})
    books.sort(key=lambda x:(x["title"].casefold(),x["language"]))
    doc={"schema_version":1,"publisher":PUBLISHER,"books":books}
    out=Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"{len(books)} publications: {out}"); return 0


def books_site(catalog_file,output_dir):
    src=Path(catalog_file)
    try: catalog_data=json.loads(src.read_text(encoding="utf-8"))
    except Exception as exc: print("ERROR: invalid catalog:",exc); return 1
    books=catalog_data.get("books")
    if not isinstance(books,list): print("ERROR: catalog missing books array"); return 1
    root=Path(output_dir)
    if root.exists(): shutil.rmtree(root)
    api=root/"api"; api.mkdir(parents=True)
    api_doc={"schema_version":1,"publisher":catalog_data.get("publisher",PUBLISHER),"books":books}
    (api/"books.json").write_text(json.dumps(api_doc,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    cards=[]
    for book in books:
        title=html.escape(str(book.get("title","")))
        author=html.escape(str(book.get("author","")))
        lang=html.escape(str(book.get("language","")))
        edition=book.get("edition") or {}
        ed=html.escape(str(edition.get("number","")))
        products=[]
        for name,product in sorted((book.get("products") or {}).items()):
            isbn=product.get("isbn")
            suffix=f" — ISBN {html.escape(str(isbn))}" if isbn and isbn!="PENDING" else ""
            products.append(f"<li>{html.escape(str(name).upper())}{suffix}</li>")
        cards.append(f'<article class="book"><h2>{title}</h2><p>{author} · {lang}' + (f" · edition {ed}" if ed else "") + f'</p><ul>{"".join(products)}</ul></article>')
    page='''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ploos Books</title><style>body{font-family:system-ui,sans-serif;max-width:72rem;margin:auto;padding:2rem;line-height:1.5}header{border-bottom:1px solid #bbb;margin-bottom:2rem}.book{padding:1rem 0;border-bottom:1px solid #ddd}h1,h2{line-height:1.15}</style></head>
<body><header><h1>Ploos Books</h1><p>Publications from Ploos AS</p></header><main>'''+"".join(cards)+'''</main></body></html>
'''
    (root/"index.html").write_text(page,encoding="utf-8")
    for p in (root/"index.html",api/"books.json"): os.utime(p,(0,0))
    print(f"{len(books)} publications: {root}"); return 0


LEGAL_DEPOSIT_STATES=("not_required","pending","submitted","confirmed")

def legal_deposit(metadata,status=None,artifacts=None,reference=None,method=None,write=False):
    p=Path(metadata); data=load(p); node=data.setdefault("legal_deposit",{}).setdefault("norway",{})
    current=node.get("status","pending" if node.get("required",True) else "not_required")
    if status is None:
        print(json.dumps({"required":node.get("required",True),"status":current,"deposited_at":node.get("deposited_at"),
                          "method":node.get("method"),"reference":node.get("reference"),"artifacts":node.get("artifacts",[])},
                         indent=2,ensure_ascii=False)); return 0
    if status not in LEGAL_DEPOSIT_STATES: print("ERROR: invalid legal deposit status:",status); return 1
    if status in ("submitted","confirmed") and not artifacts and not node.get("artifacts"):
        print("ERROR: submitted/confirmed legal deposit requires at least one artifact"); return 1
    records=[]
    for item in artifacts or []:
        a=Path(item)
        if not a.is_file(): print("ERROR: deposit artifact not found:",a); return 1
        records.append({"path":str(a),"bytes":a.stat().st_size,"sha256":sha256(a)})
    if write:
        node["status"]=status
        if records: node["artifacts"]=records
        if reference is not None: node["reference"]=reference
        if method is not None: node["method"]=method
        p.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding="utf-8")
        print(p)
    else: print(f"{current} -> {status}")
    return 0

def accessibility_report(metadata,epub,language,output):
    data=load(metadata); pub=data.get("publications",{}).get(language)
    if not pub: print("ERROR: unknown publication language:",language); return 1
    basic=epub_basic(epub)
    if basic:
        errors,warnings=basic,[]
    else:
        errors,warnings=qa_epub(epub)
    checks=[
        {"id":"epub-structure","status":"FAIL" if basic else "PASS","issues":basic},
        {"id":"internal-accessibility-qa","status":"FAIL" if errors else ("WARN" if warnings else "PASS"),
         "issues":errors,"warnings":warnings}
    ]
    status="FAIL" if errors else ("WARN" if warnings else "PASS")
    doc={"schema_version":1,"project":data.get("project"),"work_id":data.get("work",{}).get("id"),
         "language":language,"title":pub.get("title"),"subtitle":pub.get("subtitle"),"edition":data.get("edition"),
         "artifact":{"path":str(epub),"sha256":sha256(epub) if Path(epub).is_file() else None},
         "status":status,"summary":{"errors":len(errors),"warnings":len(warnings)},"checks":checks,
         "scope":"Automated internal EPUB accessibility checks; not a complete WCAG/EPUB Accessibility conformance certification."}
    out=Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"{status}: {out}")
    return 1 if status=="FAIL" else 0

STORE_KEYS={"amazon":"amazon_kdp","kobo":"kobo","apple":"apple_books","google":"google_play_books"}

def store_metadata(metadata,channel,language,output):
    data=load(metadata); errors=validate_data(data)
    if errors:
        for e in errors: print("ERROR:",e)
        return 1
    pub=data.get("publications",{}).get(language)
    if not pub: print("ERROR: unknown publication language:",language); return 1
    key=STORE_KEYS[channel]; dist=data.get("distribution",{}).get(key,{})
    if not dist.get("enabled",False): print("ERROR: channel disabled:",channel); return 1
    product_name=dist.get("product","epub"); product=pub.get("products",{}).get(product_name)
    if not product: print("ERROR: product not found:",product_name); return 1
    doc={"schema_version":1,"channel":channel,"project":data.get("project"),
         "work_id":data.get("work",{}).get("id"),"language":language,
         "title":pub.get("title"),"author":pub.get("author"),"publisher":pub.get("publisher"),
         "copyright_holder":pub.get("copyright_holder"),"license":pub.get("license"),
         "edition":data.get("edition"),"product":product_name,"isbn":product.get("isbn"),
         "external_id":dist.get("external_id")}
    out=Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(out); return 0

def paperback_geometry(page_count, config, output):
    cfg=load(config)
    trim=cfg.get("trim",{}); paper=cfg.get("paper",{}); bleed=float(cfg.get("bleed_in",0.125))
    width=float(trim.get("width_in",6)); height=float(trim.get("height_in",9))
    ppi=float(paper.get("spine_in_per_page",0))
    provider=cfg.get("provider","generic")
    if page_count < 1 or ppi <= 0:
        print("ERROR: page_count and spine_in_per_page must be positive"); return 1
    spine=page_count*ppi
    doc={"schema_version":1,"page_count":page_count,"trim_in":{"width":width,"height":height},
         "bleed_in":bleed,"provider":provider,"paper":{"id":paper.get("id"),"spine_in_per_page":ppi},
         "spine_width_in":round(spine,6),
         "cover_in":{"width":round(2*width+spine+2*bleed,6),"height":round(height+2*bleed,6)},
         "spine_text_allowed": (page_count > 79) if provider=="kdp" else None}
    out=Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(out); return 0


def paperback_cover(metadata, language, pages, config, output):
    meta=load(metadata); pub=meta.get("publications",{}).get(language,{})
    if not pub:
        print("ERROR: language publication not found:",language); return 1
    cfg=load(config); paper=cfg.get("paper",{}); ppi=float(paper.get("spine_in_per_page",0))
    if ppi <= 0:
        print("ERROR: paperback cover requires a calculable spine profile"); return 1
    trim=cfg.get("trim",{}); tw=float(trim.get("width_in",6)); th=float(trim.get("height_in",9))
    bleed=float(cfg.get("bleed_in",0.125)); spine=pages*ppi
    width=2*tw+spine+2*bleed; height=th+2*bleed
    title=html.escape(str(pub.get("title",""))); subtitle=html.escape(str(pub.get("subtitle","") or ""))
    author=html.escape(str(pub.get("author",AUTHOR))); publisher=html.escape(str(pub.get("publisher",PUBLISHER)))
    out=Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    svg=out.with_suffix(".svg")
    def x(v): return f"{v:.6f}in"
    front_x=bleed+tw+spine
    spine_x=bleed+tw
    safe=0.25
    spine_text = pages > 79 if cfg.get("provider")=="kdp" else True
    parts=[
      f'<svg xmlns="http://www.w3.org/2000/svg" width="{x(width)}" height="{x(height)}" viewBox="0 0 {width*72:.3f} {height*72:.3f}">',
      '<rect width="100%" height="100%" fill="white"/>',
      f'<rect x="{front_x*72:.3f}" y="{bleed*72:.3f}" width="{tw*72:.3f}" height="{th*72:.3f}" fill="none" stroke="black" stroke-width="0.5"/>',
      f'<rect x="{bleed*72:.3f}" y="{bleed*72:.3f}" width="{tw*72:.3f}" height="{th*72:.3f}" fill="none" stroke="black" stroke-width="0.5"/>',
      f'<text x="{(front_x+tw/2)*72:.3f}" y="{(bleed+th*0.36)*72:.3f}" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold">{title}</text>',
      f'<text x="{(front_x+tw/2)*72:.3f}" y="{(bleed+th*0.43)*72:.3f}" text-anchor="middle" font-family="sans-serif" font-size="12">{subtitle}</text>',
      f'<text x="{(front_x+tw/2)*72:.3f}" y="{(bleed+th*0.82)*72:.3f}" text-anchor="middle" font-family="sans-serif" font-size="14">{author}</text>',
      f'<text x="{(bleed+safe)*72:.3f}" y="{(bleed+safe+0.15)*72:.3f}" font-family="sans-serif" font-size="10">{publisher}</text>',
      f'<rect x="{(bleed+tw-2.25)*72:.3f}" y="{(bleed+th-1.45)*72:.3f}" width="{2*72:.3f}" height="{1.2*72:.3f}" fill="none" stroke="black" stroke-dasharray="4 3"/>',
      f'<text x="{(bleed+tw-1.25)*72:.3f}" y="{(bleed+th-0.82)*72:.3f}" text-anchor="middle" font-family="sans-serif" font-size="8">BARCODE / ISBN AREA</text>'
    ]
    if spine_text:
        cx=(spine_x+spine/2)*72; cy=(bleed+th/2)*72
        parts.append(f'<text x="{cx:.3f}" y="{cy:.3f}" text-anchor="middle" font-family="sans-serif" font-size="10" transform="rotate(90 {cx:.3f} {cy:.3f})">{title} — {author}</text>')
    parts.append('</svg>')
    svg.write_text("\n".join(parts)+"\n",encoding="utf-8")
    if out.suffix.lower()==".pdf":
        tool=shutil.which("rsvg-convert")
        if not tool:
            print(svg); print("ERROR: rsvg-convert required for PDF output"); return 1
        subprocess.run([tool,"-f","pdf","-o",str(out),str(svg)],check=True)
        print(out)
    else:
        if out != svg: shutil.copyfile(svg,out)
        print(svg)
    return 0


def paperback_cover_check(pdf, pages, config):
    path=Path(pdf); errors=[]
    if not path.is_file():
        print("ERROR: paperback cover not found:",path); return 1
    pdfinfo=shutil.which("pdfinfo")
    pdffonts=shutil.which("pdffonts")
    if not pdfinfo or not pdffonts:
        print("ERROR: pdfinfo and pdffonts are required for paperback cover QA"); return 2
    info=subprocess.run([pdfinfo,str(path)],capture_output=True,text=True,check=False)
    if info.returncode!=0:
        print("ERROR: pdfinfo failed"); return 1
    import re
    pm=re.search(r"^Pages:\s*(\d+)\s*$",info.stdout,re.MULTILINE|re.IGNORECASE)
    sm=re.search(r"^Page\s+size:\s*([0-9.]+)\s*x\s*([0-9.]+)\s*pts(?:\s.*)?$",info.stdout,re.MULTILINE|re.IGNORECASE)
    if not pm or int(pm.group(1))!=1: errors.append("cover PDF must contain exactly one page")
    cfg=load(config); trim=cfg.get("trim",{}); paper=cfg.get("paper",{})
    tw=float(trim.get("width_in",6)); th=float(trim.get("height_in",9)); bleed=float(cfg.get("bleed_in",0.125)); ppi=float(paper.get("spine_in_per_page",0))
    if pages < 1 or ppi <= 0: errors.append("page count and spine profile must be positive")
    if sm and ppi > 0:
        actual_w=float(sm.group(1)); actual_h=float(sm.group(2))
        expected_w=(2*tw+pages*ppi+2*bleed)*72; expected_h=(th+2*bleed)*72
        if abs(actual_w-expected_w)>1.0 or abs(actual_h-expected_h)>1.0:
            errors.append(f"cover size {actual_w:.3f} x {actual_h:.3f} pt; expected {expected_w:.3f} x {expected_h:.3f} pt")
    elif not sm: errors.append("could not read cover page size")
    fonts=subprocess.run([pdffonts,str(path)],capture_output=True,text=True,check=False)
    if fonts.returncode!=0: errors.append("pdffonts failed")
    else:
        rows=[line.split() for line in fonts.stdout.splitlines()[2:] if line.strip()]
        if not rows: errors.append("cover PDF contains no fonts")
        elif any(len(row)<5 or row[4].lower()!="yes" for row in rows): errors.append("cover PDF contains a non-embedded font")
    for error in errors: print("ERROR:",error)
    if errors: return 1
    print("Paperback cover QA PASS"); return 0


def main():
    ap=argparse.ArgumentParser(prog="ploos-publish")
    sub=ap.add_subparsers(dest="cmd",required=True)
    v=sub.add_parser("validate"); v.add_argument("metadata")
    iv=sub.add_parser("isbn-validate"); iv.add_argument("registry")
    imc=sub.add_parser("isbn-metadata-check"); imc.add_argument("registry"); imc.add_argument("metadata")
    ii=sub.add_parser("isbn-import"); ii.add_argument("registry"); ii.add_argument("isbn_file"); ii.add_argument("--write",action="store_true")
    ia=sub.add_parser("isbn-allocate"); ia.add_argument("registry"); ia.add_argument("--project",required=True); ia.add_argument("--edition",required=True,type=int); ia.add_argument("--language",required=True); ia.add_argument("--product",required=True); ia.add_argument("--write",action="store_true")
    e=sub.add_parser("epubcheck"); e.add_argument("epub")
    m=sub.add_parser("manifest"); m.add_argument("metadata"); m.add_argument("artifacts",nargs="*"); m.add_argument("-o","--output",default="release-manifest.json")
    pr=sub.add_parser("provenance"); pr.add_argument("metadata"); pr.add_argument("--git-commit",required=True); pr.add_argument("--qualification",required=True); pr.add_argument("--artifact",action="append",default=[]); pr.add_argument("-o","--output",default="provenance.json")
    pv=sub.add_parser("provenance-verify"); pv.add_argument("manifest")
    q=sub.add_parser("qualify"); q.add_argument("metadata"); q.add_argument("--epub",action="append",default=[]); q.add_argument("-o","--output",default="qualification-report.json")
    b=sub.add_parser("build"); b.add_argument("config"); b.add_argument("--target")
    pc=sub.add_parser("paperback-cover"); pc.add_argument("metadata"); pc.add_argument("--language",required=True); pc.add_argument("--pages",required=True,type=int); pc.add_argument("--config",required=True); pc.add_argument("-o","--output",required=True)
    pg=sub.add_parser("paperback-geometry"); pg.add_argument("--pages",required=True,type=int); pg.add_argument("--config",required=True); pg.add_argument("-o","--output",default="paperback-geometry.json")
    pq=sub.add_parser("paperback-cover-check"); pq.add_argument("pdf"); pq.add_argument("--pages",required=True,type=int); pq.add_argument("--config",required=True)
    cc=sub.add_parser("cover-check"); cc.add_argument("image"); cc.add_argument("config")
    cb=sub.add_parser("cover-build"); cb.add_argument("image"); cb.add_argument("config"); cb.add_argument("--output-dir",default="dist/covers")
    am=sub.add_parser("archive"); am.add_argument("metadata"); am.add_argument("artifacts",nargs="*"); am.add_argument("-o","--output",default="archive-manifest.json")
    au=sub.add_parser("audit"); au.add_argument("manifest")
    ox=sub.add_parser("onix"); ox.add_argument("metadata"); ox.add_argument("--language",required=True); ox.add_argument("--product",required=True); ox.add_argument("-o","--output",default="onix.xml")
    ov=sub.add_parser("onix-validate"); ov.add_argument("onix"); ov.add_argument("--schema")
    osb=sub.add_parser("onix-schema-verify"); osb.add_argument("manifest")
    obv=sub.add_parser("onix-bundle-validate"); obv.add_argument("onix"); obv.add_argument("manifest")
    cat=sub.add_parser("catalog"); cat.add_argument("metadata",nargs="+"); cat.add_argument("-o","--output",default="catalog.json"); cat.add_argument("--include-unpublished",action="store_true")
    bs=sub.add_parser("books-site"); bs.add_argument("catalog"); bs.add_argument("--output-dir",default="dist/books")
    ld=sub.add_parser("legal-deposit"); ld.add_argument("metadata"); ld.add_argument("--status",choices=LEGAL_DEPOSIT_STATES); ld.add_argument("--artifact",action="append",default=[]); ld.add_argument("--reference"); ld.add_argument("--method"); ld.add_argument("--write",action="store_true")
    ar=sub.add_parser("accessibility-report"); ar.add_argument("metadata"); ar.add_argument("--epub",required=True); ar.add_argument("--language",required=True); ar.add_argument("-o","--output",default="accessibility-report.json")
    sm=sub.add_parser("store-metadata"); sm.add_argument("metadata"); sm.add_argument("--channel",required=True,choices=STORE_KEYS); sm.add_argument("--language",required=True); sm.add_argument("-o","--output",required=True)
    l=sub.add_parser("lifecycle"); l.add_argument("metadata"); l.add_argument("status",choices=LIFECYCLE_STATES); l.add_argument("--write",action="store_true")
    p=sub.add_parser("package"); p.add_argument("metadata"); p.add_argument("config"); p.add_argument("--channel",required=True,choices=["amazon","kobo","apple","google"]); p.add_argument("--language",required=True); p.add_argument("--epub"); p.add_argument("--pdf"); p.add_argument("--cover")
    a=ap.parse_args()
    if a.cmd=="validate": return validate(a.metadata)
    if a.cmd=="isbn-validate": return isbn_registry_validate(a.registry)
    if a.cmd=="isbn-metadata-check": return isbn_metadata_check(a.registry,a.metadata)
    if a.cmd=="isbn-import": return isbn_import(a.registry,a.isbn_file,a.write)
    if a.cmd=="isbn-allocate": return isbn_allocate(a.registry,a.project,a.edition,a.language,a.product,a.write)
    if a.cmd=="epubcheck": return epubcheck(a.epub)
    if a.cmd=="manifest": return manifest(a.metadata,a.output,a.artifacts)
    if a.cmd=="provenance": return provenance(a.metadata,a.git_commit,a.qualification,a.artifact,a.output)
    if a.cmd=="provenance-verify": return provenance_verify(a.manifest)
    if a.cmd=="build": return build(a.config,a.target)
    if a.cmd=="paperback-cover": return paperback_cover(a.metadata,a.language,a.pages,a.config,a.output)
    if a.cmd=="paperback-geometry": return paperback_geometry(a.pages,a.config,a.output)
    if a.cmd=="paperback-cover-check": return paperback_cover_check(a.pdf,a.pages,a.config)
    if a.cmd=="cover-check": return cover_check(a.image,a.config)
    if a.cmd=="cover-build": return cover_build(a.image,a.config,a.output_dir)
    if a.cmd=="archive": return archive_manifest(a.metadata,a.artifacts,a.output)
    if a.cmd=="audit": return audit_archive(a.manifest)
    if a.cmd=="onix": return onix(a.metadata,a.language,a.product,a.output)
    if a.cmd=="onix-validate": return onix_validate_file(a.onix,a.schema)
    if a.cmd=="onix-schema-verify": return onix_schema_bundle_verify(a.manifest)
    if a.cmd=="onix-bundle-validate": return onix_bundle_validate(a.onix,a.manifest)
    if a.cmd=="catalog": return catalog(a.metadata,a.output,a.include_unpublished)
    if a.cmd=="books-site": return books_site(a.catalog,a.output_dir)
    if a.cmd=="legal-deposit": return legal_deposit(a.metadata,a.status,a.artifact,a.reference,a.method,a.write)
    if a.cmd=="accessibility-report": return accessibility_report(a.metadata,a.epub,a.language,a.output)
    if a.cmd=="store-metadata": return store_metadata(a.metadata,a.channel,a.language,a.output)
    if a.cmd=="lifecycle": return lifecycle(a.metadata,a.status,a.write)
    if a.cmd=="package": return package(a.metadata,a.config,a.channel,a.language,a.epub,a.pdf,a.cover)
    return qualify(a.metadata,a.epub,a.output)

if __name__=="__main__":
    raise SystemExit(main())
