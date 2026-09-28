#!/usr/bin/env python3
from __future__ import annotations
import copy, json, subprocess, sys, tempfile, zipfile
import yaml
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/"scripts"/"ploos_publish.py"
META=ROOT/"tests"/"fixtures"/"publication.yaml"
PKG=ROOT/"metadata"/"package.example.yaml"

def run(*args,cwd=None):
    return subprocess.run([sys.executable,str(CLI),*map(str,args)],cwd=cwd or ROOT,capture_output=True,text=True)

def make_epub(path):
    container='<?xml version="1.0" encoding="UTF-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'
    opf='<?xml version="1.0" encoding="UTF-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="pub-id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="pub-id">urn:uuid:00000000-0000-0000-0000-000000000001</dc:identifier><dc:title>Publishing Fixture</dc:title><dc:language>nb</dc:language><meta property="dcterms:modified">2026-09-28T00:00:00Z</meta></metadata><manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/></manifest><spine><itemref idref="nav"/></spine></package>'
    nav='<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="nb" xml:lang="nb"><head><title>Publishing Fixture</title></head><body><nav epub:type="toc"><h1>Innhold</h1><ol><li><a href="nav.xhtml">Start</a></li></ol></nav><section><h1>Publishing Fixture</h1><p>Minimal EPUB 3 fixture for Ploos Publishing.</p></section></body></html>'
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("mimetype","application/epub+zip",compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml",container)
        z.writestr("EPUB/package.opf",opf)
        z.writestr("EPUB/nav.xhtml",nav)

def main():
    assert run("validate",META).returncode==0
    base=yaml.safe_load(META.read_text())
    with tempfile.TemporaryDirectory() as policy_td:
        policy_td=Path(policy_td)
        for field,bad in (("author","Wrong Author"),("publisher","Wrong Publisher"),("copyright_holder","Wrong Holder"),("license","CC-BY-NC-4.0")):
            data=copy.deepcopy(base); data["publications"]["nb"][field]=bad
            bad_meta=policy_td/f"bad-{field}.yaml"
            bad_meta.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True))
            assert run("validate",bad_meta).returncode!=0, field
        life=policy_td/"lifecycle.yaml"; life.write_text(META.read_text())
        for state in ("candidate","qualified","published","archived"):
            assert run("lifecycle",life,state,"--write").returncode==0
        assert run("lifecycle",life,"draft").returncode!=0
        invalid=policy_td/"invalid-transition.yaml"; invalid.write_text(META.read_text())
        assert run("lifecycle",invalid,"published").returncode!=0
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); epub=td/"fixture.epub"; cover=td/"cover.jpg"; pdf=td/"fixture.pdf"
        make_epub(epub); cover.write_bytes(b"fixture-cover"); pdf.write_bytes(b"%PDF-fixture")
        report=td/"qualification.json"
        assert run("qualify",META,"--epub",epub,"-o",report).returncode==0
        assert json.loads(report.read_text())["status"]=="PASS"
        manifest=td/"release.json"
        assert run("manifest",META,epub,pdf,"-o",manifest).returncode==0
        assert len(json.loads(manifest.read_text())["artifacts"])==2
        cfg=td/"package.yaml"
        cfg.write_text(PKG.read_text().replace("output_dir: packages",f"output_dir: {td/'packages'}"))
        assert run("package",META,cfg,"--channel","amazon","--language","nb","--epub",epub,"--cover",cover).returncode==0
        package=td/"packages"/"amazon"/"nb"
        assert (package/"metadata.json").is_file()
        assert len(json.loads((package/"manifest.json").read_text())["artifacts"])==2
    print("Publishing M1/M2 self-test PASS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
