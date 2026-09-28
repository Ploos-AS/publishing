#!/usr/bin/env python3
"""Internal EPUB QA for Ploos publications."""
from __future__ import annotations
import posixpath, re, zipfile
from html.parser import HTMLParser
from pathlib import PurePosixPath
from xml.etree import ElementTree as ET

class HTMLQA(HTMLParser):
    def __init__(self):
        super().__init__(); self.refs=[]; self.images=[]; self.lang=False; self.title=False; self.headings=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="html" and (a.get("lang") or a.get("xml:lang")): self.lang=True
        if tag=="title": self.title=True
        if tag=="a" and a.get("href"): self.refs.append(a["href"])
        if tag=="img":
            self.images.append((a.get("src"),a.get("alt")))
        if re.fullmatch(r"h[1-6]",tag): self.headings.append(int(tag[1]))

def qa_epub(path):
    errors=[]; warnings=[]
    with zipfile.ZipFile(path) as z:
        names=set(z.namelist())
        docs=[n for n in names if n.lower().endswith((".xhtml",".html",".htm"))]
        nav=[n for n in names if n.lower().endswith((".xhtml",".html")) and "nav" in PurePosixPath(n).name.lower()]
        if not docs: errors.append("no HTML/XHTML content documents")
        if not nav: warnings.append("navigation document not obvious from filename; EPUBCheck must verify navigation")
        for name in docs:
            try: text=z.read(name).decode("utf-8")
            except UnicodeDecodeError:
                errors.append(f"{name}: not UTF-8"); continue
            q=HTMLQA()
            try: q.feed(text)
            except Exception as exc:
                errors.append(f"{name}: HTML parse error: {exc}"); continue
            if not q.lang: warnings.append(f"{name}: missing html lang/xml:lang")
            for src,alt in q.images:
                if not src: errors.append(f"{name}: img missing src"); continue
                target=posixpath.normpath(posixpath.join(posixpath.dirname(name),src.split("#")[0].split("?")[0]))
                if target not in names: errors.append(f"{name}: missing image {src}")
                if alt is None: warnings.append(f"{name}: image missing alt attribute: {src}")
            for href in q.refs:
                if href.startswith(("#","http:","https:","mailto:","tel:")): continue
                target=href.split("#")[0].split("?")[0]
                if not target: continue
                target=posixpath.normpath(posixpath.join(posixpath.dirname(name),target))
                if target not in names: errors.append(f"{name}: broken internal link {href}")
            for a,b in zip(q.headings,q.headings[1:]):
                if b>a+1: warnings.append(f"{name}: heading level jumps h{a} to h{b}")
        opfs=[n for n in names if n.lower().endswith(".opf")]
        if not opfs: errors.append("missing OPF package document")
        else:
            try:
                root=ET.fromstring(z.read(opfs[0]))
                values={"title":False,"language":False,"identifier":False}
                for el in root.iter():
                    local=el.tag.rsplit("}",1)[-1]
                    if local in values and (el.text or "").strip(): values[local]=True
                for k,v in values.items():
                    if not v: errors.append(f"OPF missing dc:{k}")
            except ET.ParseError as exc: errors.append(f"invalid OPF XML: {exc}")
    return errors,warnings
