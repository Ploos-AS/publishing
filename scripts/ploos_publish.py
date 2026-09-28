#!/usr/bin/env python3
"""Ploos Publishing CLI."""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess, zipfile
from xml.etree import ElementTree as ET
from pathlib import Path
import yaml
from PIL import Image, ImageOps
from epub_qa import qa_epub

AUTHOR="Per Gustav Ousdal"
PUBLISHER="Ploos AS"
COPYRIGHT_HOLDER="Ploos AS"
LICENSE="CC-BY-4.0"
LIFECYCLE_STATES=("draft","candidate","qualified","published","archived")
LIFECYCLE_TRANSITIONS={"draft":{"candidate"},"candidate":{"draft","qualified"},"qualified":{"draft","published"},"published":{"archived"},"archived":set()}

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
        dst=root/src.name; shutil.copy2(src,dst)
        copied.append({"kind":kind,"file":dst.name,"bytes":dst.stat().st_size,"sha256":sha256(dst)})
    meta={"project":data.get("project"),"language":language,"channel":channel,
          "title":pub.get("title"),"author":pub.get("author"),"publisher":pub.get("publisher"),
          "copyright_holder":pub.get("copyright_holder"),"license":pub.get("license"),
          "edition":data.get("edition"),"products":pub.get("products",{})}
    (root/"metadata.json").write_text(json.dumps(meta,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    package_manifest={"schema_version":1,"channel":channel,"language":language,"artifacts":copied}
    (root/"manifest.json").write_text(json.dumps(package_manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
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






ONIX_LANG={"nb":"nor","nn":"nno","en":"eng"}
ONIX_PRODUCT_FORM={"epub":"ED","pdf":"ED"}

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
    title_detail=ET.SubElement(desc,"TitleDetail"); ET.SubElement(title_detail,"TitleType").text="01"
    title_el=ET.SubElement(title_detail,"TitleElement"); ET.SubElement(title_el,"TitleElementLevel").text="01"
    ET.SubElement(title_el,"TitleText").text=pub.get("title")
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
                          "language":language,"title":pub.get("title"),"author":pub.get("author"),
                          "publisher":pub.get("publisher"),"edition":data.get("edition"),
                          "lifecycle":state,"products":products})
    books.sort(key=lambda x:(x["title"].casefold(),x["language"]))
    doc={"schema_version":1,"publisher":PUBLISHER,"books":books}
    out=Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"{len(books)} publications: {out}"); return 0

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
         "language":language,"title":pub.get("title"),"edition":data.get("edition"),
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

def main():
    ap=argparse.ArgumentParser(prog="ploos-publish")
    sub=ap.add_subparsers(dest="cmd",required=True)
    v=sub.add_parser("validate"); v.add_argument("metadata")
    e=sub.add_parser("epubcheck"); e.add_argument("epub")
    m=sub.add_parser("manifest"); m.add_argument("metadata"); m.add_argument("artifacts",nargs="*"); m.add_argument("-o","--output",default="release-manifest.json")
    q=sub.add_parser("qualify"); q.add_argument("metadata"); q.add_argument("--epub",action="append",default=[]); q.add_argument("-o","--output",default="qualification-report.json")
    b=sub.add_parser("build"); b.add_argument("config"); b.add_argument("--target")
    cc=sub.add_parser("cover-check"); cc.add_argument("image"); cc.add_argument("config")
    cb=sub.add_parser("cover-build"); cb.add_argument("image"); cb.add_argument("config"); cb.add_argument("--output-dir",default="dist/covers")
    ox=sub.add_parser("onix"); ox.add_argument("metadata"); ox.add_argument("--language",required=True); ox.add_argument("--product",required=True); ox.add_argument("-o","--output",default="onix.xml")
    cat=sub.add_parser("catalog"); cat.add_argument("metadata",nargs="+"); cat.add_argument("-o","--output",default="catalog.json"); cat.add_argument("--include-unpublished",action="store_true")
    ld=sub.add_parser("legal-deposit"); ld.add_argument("metadata"); ld.add_argument("--status",choices=LEGAL_DEPOSIT_STATES); ld.add_argument("--artifact",action="append",default=[]); ld.add_argument("--reference"); ld.add_argument("--method"); ld.add_argument("--write",action="store_true")
    ar=sub.add_parser("accessibility-report"); ar.add_argument("metadata"); ar.add_argument("--epub",required=True); ar.add_argument("--language",required=True); ar.add_argument("-o","--output",default="accessibility-report.json")
    sm=sub.add_parser("store-metadata"); sm.add_argument("metadata"); sm.add_argument("--channel",required=True,choices=STORE_KEYS); sm.add_argument("--language",required=True); sm.add_argument("-o","--output",required=True)
    l=sub.add_parser("lifecycle"); l.add_argument("metadata"); l.add_argument("status",choices=LIFECYCLE_STATES); l.add_argument("--write",action="store_true")
    p=sub.add_parser("package"); p.add_argument("metadata"); p.add_argument("config"); p.add_argument("--channel",required=True,choices=["amazon","kobo","apple","google"]); p.add_argument("--language",required=True); p.add_argument("--epub"); p.add_argument("--pdf"); p.add_argument("--cover")
    a=ap.parse_args()
    if a.cmd=="validate": return validate(a.metadata)
    if a.cmd=="epubcheck": return epubcheck(a.epub)
    if a.cmd=="manifest": return manifest(a.metadata,a.output,a.artifacts)
    if a.cmd=="build": return build(a.config,a.target)
    if a.cmd=="cover-check": return cover_check(a.image,a.config)
    if a.cmd=="cover-build": return cover_build(a.image,a.config,a.output_dir)
    if a.cmd=="onix": return onix(a.metadata,a.language,a.product,a.output)
    if a.cmd=="catalog": return catalog(a.metadata,a.output,a.include_unpublished)
    if a.cmd=="legal-deposit": return legal_deposit(a.metadata,a.status,a.artifact,a.reference,a.method,a.write)
    if a.cmd=="accessibility-report": return accessibility_report(a.metadata,a.epub,a.language,a.output)
    if a.cmd=="store-metadata": return store_metadata(a.metadata,a.channel,a.language,a.output)
    if a.cmd=="lifecycle": return lifecycle(a.metadata,a.status,a.write)
    if a.cmd=="package": return package(a.metadata,a.config,a.channel,a.language,a.epub,a.pdf,a.cover)
    return qualify(a.metadata,a.epub,a.output)

if __name__=="__main__":
    raise SystemExit(main())
