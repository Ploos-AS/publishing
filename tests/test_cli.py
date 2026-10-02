#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, json, subprocess, sys, tempfile, zipfile
import yaml
from PIL import Image
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/"scripts"/"ploos_publish.py"
META=ROOT/"tests"/"fixtures"/"publication.yaml"
PKG=ROOT/"metadata"/"package.example.yaml"
COVER=ROOT/"metadata"/"cover.example.yaml"
ISBN_REGISTRY=ROOT/"isbn"/"registry.yaml"

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
    assert run("isbn-validate",ISBN_REGISTRY).returncode==0
    assert run("isbn-metadata-check",ISBN_REGISTRY,META).returncode==0
    with tempfile.TemporaryDirectory() as isbn_td:
        isbn_td=Path(isbn_td)
        valid=yaml.safe_load(ISBN_REGISTRY.read_text())
        bad_prefix=copy.deepcopy(valid); bad_prefix["publisher"]["prefix_status"]="pending"; bad_prefix["publisher"]["publisher_prefix"]="978-82-94310"; bad_prefix["isbn_pool"]=[]
        bad_prefix_path=isbn_td/"bad-prefix.yaml"; bad_prefix_path.write_text(yaml.safe_dump(bad_prefix,sort_keys=False,allow_unicode=True))
        assert run("isbn-validate",bad_prefix_path).returncode!=0
        assigned=copy.deepcopy(valid); assigned["publisher"]["prefix_status"]="assigned"; assigned["publisher"]["publisher_prefix"]="978-82-00000"
        assigned_path=isbn_td/"assigned-prefix.yaml"; assigned_path.write_text(yaml.safe_dump(assigned,sort_keys=False,allow_unicode=True))
        assert run("isbn-validate",assigned_path).returncode==0
        valid["allocations"]=[{"isbn":"9780000000002","project":"EduNumbers","edition":1,"language":"nb","product":"epub"}]
        valid_path=isbn_td/"valid.yaml"; valid_path.write_text(yaml.safe_dump(valid,sort_keys=False,allow_unicode=True))
        assert run("isbn-validate",valid_path).returncode==0
        normalized_dup=copy.deepcopy(valid)
        normalized_dup["publisher"]["prefix_status"]="assigned"
        normalized_dup["publisher"]["publisher_prefix"]="978-82-00000"
        normalized_dup["isbn_pool"]=["978-0-00-000000-2"]
        normalized_dup_path=isbn_td/"normalized-duplicate.yaml"; normalized_dup_path.write_text(yaml.safe_dump(normalized_dup,sort_keys=False,allow_unicode=True))
        assert run("isbn-validate",normalized_dup_path).returncode==0
        normalized_dup["allocations"].append({"isbn":"9780000000002","project":"Other","edition":1,"language":"en","product":"pdf"})
        normalized_dup_path.write_text(yaml.safe_dump(normalized_dup,sort_keys=False,allow_unicode=True))
        assert run("isbn-validate",normalized_dup_path).returncode!=0
        bad=copy.deepcopy(valid); bad["allocations"][0]["isbn"]="9780000000003"
        bad_path=isbn_td/"bad.yaml"; bad_path.write_text(yaml.safe_dump(bad,sort_keys=False,allow_unicode=True))
        assert run("isbn-validate",bad_path).returncode!=0
        bad_target=copy.deepcopy(valid); bad_target["allocations"][0]["project"]="Unknown"
        bad_target_path=isbn_td/"bad-target.yaml"; bad_target_path.write_text(yaml.safe_dump(bad_target,sort_keys=False,allow_unicode=True))
        assert run("isbn-validate",bad_target_path).returncode!=0
        dup=copy.deepcopy(valid); dup["allocations"].append(copy.deepcopy(dup["allocations"][0]))
        dup_path=isbn_td/"duplicate.yaml"; dup_path.write_text(yaml.safe_dump(dup,sort_keys=False,allow_unicode=True))
        assert run("isbn-validate",dup_path).returncode!=0
        registry=isbn_td/"registry.yaml"
        registry_data=yaml.safe_load(ISBN_REGISTRY.read_text())
        registry_data["publisher"]["prefix_status"]="assigned"
        registry_data["publisher"]["publisher_prefix"]="978-82-00000"
        registry_data["isbn_pool"]=[]
        registry_data["allocations"]=[]
        registry.write_text(yaml.safe_dump(registry_data,sort_keys=False,allow_unicode=True))
        pool=isbn_td/"pool.txt"; pool.write_text("9780000000002\n9780000000019\n9780000000026\n9780000000033\n")
        pending_data=copy.deepcopy(registry_data); pending_data["publisher"]["prefix_status"]="pending"; pending_data["publisher"]["publisher_prefix"]=None; pending_data["isbn_pool"]=[]
        pending_registry=isbn_td/"pending-registry.yaml"; pending_registry.write_text(yaml.safe_dump(pending_data,sort_keys=False,allow_unicode=True))
        assert run("isbn-import",pending_registry,pool,"--write").returncode!=0
        assert yaml.safe_load(pending_registry.read_text())["isbn_pool"]==[]
        assert run("isbn-import",registry,pool,"--write").returncode==0
        imported=yaml.safe_load(registry.read_text())
        assert imported["isbn_pool"]==["9780000000002","9780000000019","9780000000026","9780000000033"]
        assert imported["publisher"]["prefix_status"]=="assigned"
        assert run("isbn-allocate",registry,"--project","EduNumbers","--edition","1","--language","nb","--product","epub","--write").returncode==0
        allocated=yaml.safe_load(registry.read_text())
        assert allocated["allocations"][0]["isbn"]=="9780000000002"
        assert run("isbn-allocate",registry,"--project","EduNumbers","--edition","1","--language","nb","--product","epub","--write").returncode!=0
        assert run("isbn-allocate",registry,"--project","EduNumbers","--edition","2","--language","nb","--product","epub","--write").returncode==0
        assert run("isbn-allocate",registry,"--project","EduNumbers","--edition","1","--language","en","--product","epub","--write").returncode==0
        assert run("isbn-allocate",registry,"--project","EduNumbers","--edition","1","--language","nb","--product","kindle","--write").returncode==0
        assert yaml.safe_load(registry.read_text())["allocations"][3]["isbn"]=="9780000000033"
        assert run("isbn-allocate",registry,"--project","EduNumbers","--edition","1","--language","nb","--product","pdf","--write").returncode!=0
        assert run("isbn-allocate",registry,"--project","Unknown","--edition","1","--language","nb","--product","epub").returncode!=0
        assert run("isbn-allocate",registry,"--project","EduNumbers","--edition","0","--language","nb","--product","epub").returncode!=0
        assert run("isbn-allocate",registry,"--project","EduNumbers","--edition","1","--language","xx","--product","epub").returncode!=0
        assert run("isbn-allocate",registry,"--project","EduNumbers","--edition","1","--language","nb","--product","web").returncode!=0
        assert run("isbn-validate",registry).returncode==0
        synced_meta=isbn_td/"synced-metadata.yaml"; synced=yaml.safe_load(META.read_text())
        synced["project"]="EduNumbers"; synced["edition"]["number"]=1
        synced["publications"]["nb"]["products"]["epub"]["isbn"]="9780000000002"
        synced_meta.write_text(yaml.safe_dump(synced,sort_keys=False,allow_unicode=True))
        assert run("isbn-metadata-check",registry,synced_meta).returncode==0
        kindle_synced=copy.deepcopy(synced)
        kindle_synced["publications"]["nb"]["products"]["kindle"]={"isbn":"9780000000033","external_id_type":"ASIN","external_id":None,"source":"epub"}
        kindle_synced_meta=isbn_td/"kindle-synced-metadata.yaml"; kindle_synced_meta.write_text(yaml.safe_dump(kindle_synced,sort_keys=False,allow_unicode=True))
        assert run("isbn-metadata-check",registry,kindle_synced_meta).returncode==0
        kindle_missing=copy.deepcopy(kindle_synced); kindle_missing["publications"]["nb"]["products"]["kindle"]["isbn"]=None
        kindle_missing_meta=isbn_td/"kindle-missing-isbn.yaml"; kindle_missing_meta.write_text(yaml.safe_dump(kindle_missing,sort_keys=False,allow_unicode=True))
        assert run("isbn-metadata-check",registry,kindle_missing_meta).returncode!=0
        mismatched=copy.deepcopy(synced); mismatched["publications"]["nb"]["products"]["epub"]["isbn"]="9780000000095"
        mismatch_meta=isbn_td/"mismatch-metadata.yaml"; mismatch_meta.write_text(yaml.safe_dump(mismatched,sort_keys=False,allow_unicode=True))
        assert run("isbn-metadata-check",registry,mismatch_meta).returncode!=0
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
        successor=copy.deepcopy(base)
        successor["edition"]["number"]=2
        successor["edition"]["supersedes"]={"work_id":successor["work"]["id"],"edition":1}
        successor_meta=policy_td/"successor.yaml"; successor_meta.write_text(yaml.safe_dump(successor,sort_keys=False,allow_unicode=True))
        assert run("validate",successor_meta).returncode==0
        self_supersede=copy.deepcopy(successor); self_supersede["edition"]["supersedes"]["edition"]=2
        self_meta=policy_td/"self-supersede.yaml"; self_meta.write_text(yaml.safe_dump(self_supersede,sort_keys=False,allow_unicode=True))
        assert run("validate",self_meta).returncode!=0
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); epub=td/"fixture.epub"; master=td/"cover-master.jpg"; bad_cover=td/"bad-cover.jpg"; pdf=td/"fixture.pdf"
        make_epub(epub); pdf.write_bytes(b"%PDF-fixture")
        Image.new("RGB",(2000,3200)).save(master,"JPEG",quality=95)
        Image.new("RGB",(400,400)).save(bad_cover,"JPEG",quality=90)
        assert run("cover-check",master,COVER).returncode==0
        assert run("cover-check",bad_cover,COVER).returncode!=0
        covers=td/"covers"
        assert run("cover-build",master,COVER,"--output-dir",covers).returncode==0
        for channel in ("amazon","kobo","apple","google"):
            assert (covers/f"{channel}.jpg").is_file(), channel
        cover=covers/"amazon.jpg"
        for channel in ("amazon","kobo","apple","google"):
            store_out=td/f"{channel}-nb.json"
            assert run("store-metadata",META,"--channel",channel,"--language","nb","-o",store_out).returncode==0
            store_doc=json.loads(store_out.read_text())
            assert store_doc["isbn"]=="PENDING"
            assert "external_id" in store_doc
            assert store_doc["external_id"] is None
        assert run("onix",META,"--language","nb","--product","epub","-o",td/"pending-onix.xml").returncode!=0
        onix_meta=td/"onix.yaml"; onix_data=copy.deepcopy(base)
        onix_data["publications"]["nb"]["products"]["epub"]["isbn"]="9780000000002"
        onix_meta.write_text(yaml.safe_dump(onix_data,sort_keys=False,allow_unicode=True))
        onix_out=td/"onix.xml"
        assert run("onix",onix_meta,"--language","nb","--product","epub","-o",onix_out).returncode==0
        onix_text=onix_out.read_text()
        assert 'release="3.0"' in onix_text and "9780000000002" in onix_text
        assert "<ProductFormDetail>E101</ProductFormDetail>" in onix_text
        assert run("onix-validate",onix_out).returncode==0
        broken_onix=td/"broken-onix.xml"; broken_onix.write_text(onix_text.replace("9780000000002","9780000000003"))
        assert run("onix-validate",broken_onix).returncode!=0
        catalog_out=td/"catalog.json"
        assert run("catalog",META,"-o",catalog_out).returncode==0
        assert json.loads(catalog_out.read_text())["books"]==[]
        assert run("catalog",META,"-o",catalog_out,"--include-unpublished").returncode==0
        assert len(json.loads(catalog_out.read_text())["books"])==1
        site=td/"books-site"
        assert run("books-site",catalog_out,"--output-dir",site).returncode==0
        assert (site/"index.html").is_file()
        assert (site/"api"/"books.json").is_file()
        site_api=json.loads((site/"api"/"books.json").read_text())
        assert site_api["publisher"]=="Ploos AS" and len(site_api["books"])==1
        assert "Publishing Fixture" in (site/"index.html").read_text()
        first_site={str(p.relative_to(site)):hashlib.sha256(p.read_bytes()).hexdigest() for p in site.rglob("*") if p.is_file()}
        assert run("books-site",catalog_out,"--output-dir",site).returncode==0
        second_site={str(p.relative_to(site)):hashlib.sha256(p.read_bytes()).hexdigest() for p in site.rglob("*") if p.is_file()}
        assert first_site==second_site
        deposit_meta=td/"deposit.yaml"; deposit_meta.write_text(META.read_text())
        assert run("legal-deposit",deposit_meta).returncode==0
        assert run("legal-deposit",deposit_meta,"--status","submitted","--write").returncode!=0
        assert run("legal-deposit",deposit_meta,"--status","submitted","--artifact",pdf,"--method","nb-digital","--reference","fixture-receipt","--write").returncode==0
        deposit_doc=yaml.safe_load(deposit_meta.read_text())["legal_deposit"]["norway"]
        assert deposit_doc["status"]=="submitted"
        assert deposit_doc["artifacts"][0]["sha256"]
        accessibility=td/"accessibility.json"
        assert run("accessibility-report",META,"--epub",epub,"--language","nb","-o",accessibility).returncode==0
        access_doc=json.loads(accessibility.read_text())
        assert access_doc["status"]=="PASS"
        assert access_doc["summary"]=={"errors":0,"warnings":0}
        assert access_doc["artifact"]["sha256"]
        report=td/"qualification.json"
        assert run("qualify",META,"--epub",epub,"-o",report).returncode==0
        assert json.loads(report.read_text())["status"]=="PASS"
        archive=td/"archive.json"
        assert run("archive",META,epub,pdf,accessibility,"-o",archive).returncode==0
        assert run("audit",archive).returncode==0
        original_pdf=pdf.read_bytes(); pdf.write_bytes(original_pdf+b"-changed")
        assert run("audit",archive).returncode!=0
        pdf.write_bytes(original_pdf)
        assert run("audit",archive).returncode==0
        manifest=td/"release.json"
        assert run("manifest",META,epub,pdf,"-o",manifest).returncode==0
        assert len(json.loads(manifest.read_text())["artifacts"])==2
        provenance=td/"provenance.json"
        fixture_commit="0123456789abcdef0123456789abcdef01234567"
        assert run("provenance",META,"--git-commit",fixture_commit,"--qualification",report,"--artifact",epub,"--artifact",pdf,"-o",provenance).returncode==0
        provenance_doc=json.loads(provenance.read_text())
        assert provenance_doc["git_commit"]==fixture_commit
        assert provenance_doc["qualification"]["status"]=="PASS"
        assert run("provenance-verify",provenance).returncode==0
        original_epub=epub.read_bytes(); epub.write_bytes(original_epub+b"tampered")
        assert run("provenance-verify",provenance).returncode!=0
        epub.write_bytes(original_epub)
        assert run("provenance-verify",provenance).returncode==0
        # Pinned ONIX schema bundle integrity gate.
        schema_dir=td/"onix-schema"; schema_dir.mkdir()
        required_schema_files=["ONIX_BookProduct_3.0_reference.xsd","ONIX_BookProduct_CodeLists.xsd","ONIX_XHTML_Subset.xsd","ONIX_BookProduct_3.0_short.xsd"]
        records=[]
        for name in required_schema_files:
            p=schema_dir/name; p.write_text("<schema/>")
            records.append({"path":name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
        schema_file=schema_dir/required_schema_files[0]
        schema_manifest=schema_dir/"MANIFEST.yaml"
        manifest_data={"manifest_version":1,"entry_point":"ONIX_BookProduct_3.0_reference.xsd","schema":{"release":"3.0","revision":7,"revised":"2020-05-18"},"codelists":{"issue":74},"sources":{"authoritative":{"authority":"EDItEUR","location":"https://www.editeur.org/93/Release-3.0-Downloads/","retrieved_at":"2026-09-29"}},"files":records}
        schema_manifest.write_text(yaml.safe_dump(manifest_data))
        assert run("onix-schema-verify",schema_manifest).returncode==0
        unsupported=copy.deepcopy(manifest_data); unsupported["manifest_version"]=2
        unsupported_manifest=schema_dir/"UNSUPPORTED-VERSION-MANIFEST.yaml"; unsupported_manifest.write_text(yaml.safe_dump(unsupported))
        assert run("onix-schema-verify",unsupported_manifest).returncode!=0
        bad_entry=copy.deepcopy(manifest_data); bad_entry["entry_point"]="ONIX_BookProduct_CodeLists.xsd"
        bad_entry_manifest=schema_dir/"BAD-ENTRY-MANIFEST.yaml"; bad_entry_manifest.write_text(yaml.safe_dump(bad_entry))
        assert run("onix-schema-verify",bad_entry_manifest).returncode!=0
        schema_file.write_text("<schema>tampered</schema>")
        assert run("onix-schema-verify",schema_manifest).returncode!=0
        schema_file.write_text("<schema/>")
        assert run("onix-schema-verify",schema_manifest).returncode==0
        incomplete=copy.deepcopy(manifest_data); incomplete["files"]=incomplete["files"][:-1]
        incomplete_manifest=schema_dir/"INCOMPLETE-MANIFEST.yaml"; incomplete_manifest.write_text(yaml.safe_dump(incomplete))
        assert run("onix-schema-verify",incomplete_manifest).returncode!=0
        unsafe=copy.deepcopy(manifest_data); unsafe["files"][0]["path"]="../outside.xsd"
        unsafe_manifest=schema_dir/"UNSAFE-MANIFEST.yaml"; unsafe_manifest.write_text(yaml.safe_dump(unsafe))
        assert run("onix-schema-verify",unsafe_manifest).returncode!=0
        duplicate=copy.deepcopy(manifest_data); duplicate["files"].append(copy.deepcopy(duplicate["files"][0]))
        duplicate_manifest=schema_dir/"DUPLICATE-MANIFEST.yaml"; duplicate_manifest.write_text(yaml.safe_dump(duplicate))
        assert run("onix-schema-verify",duplicate_manifest).returncode!=0
        alias=copy.deepcopy(manifest_data); alias["files"].append(copy.deepcopy(alias["files"][0])); alias["files"][-1]["path"]="./"+alias["files"][-1]["path"]
        alias_manifest=schema_dir/"ALIAS-MANIFEST.yaml"; alias_manifest.write_text(yaml.safe_dump(alias))
        assert run("onix-schema-verify",alias_manifest).returncode!=0
        backslash=copy.deepcopy(manifest_data); backslash["files"][0]["path"]="subdir\\\\ONIX_BookProduct_3.0_reference.xsd"
        backslash_manifest=schema_dir/"BACKSLASH-MANIFEST.yaml"; backslash_manifest.write_text(yaml.safe_dump(backslash))
        assert run("onix-schema-verify",backslash_manifest).returncode!=0
        invalid_hash=copy.deepcopy(manifest_data); invalid_hash["files"][0]["sha256"]="not-a-sha256"
        invalid_hash_manifest=schema_dir/"INVALID-HASH-MANIFEST.yaml"; invalid_hash_manifest.write_text(yaml.safe_dump(invalid_hash))
        assert run("onix-schema-verify",invalid_hash_manifest).returncode!=0
        bad=copy.deepcopy(manifest_data); bad["sources"]["authoritative"]["authority"]="Mirror"
        bad_schema_manifest=schema_dir/"BAD-MANIFEST.yaml"; bad_schema_manifest.write_text(yaml.safe_dump(bad))
        assert run("onix-schema-verify",bad_schema_manifest).returncode!=0
        bundle_dir=td/"valid-onix-bundle"; bundle_dir.mkdir()
        entry=bundle_dir/"ONIX_BookProduct_3.0_reference.xsd"
        entry.write_text("""<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:element name="root" type="xs:string"/></xs:schema>""")
        bundle_records=[]
        for name in required_schema_files:
            p=bundle_dir/name
            if name!=required_schema_files[0]: p.write_text("<schema/>")
            bundle_records.append({"path":name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
        bundle_manifest=bundle_dir/"MANIFEST.yaml"
        bundle_manifest.write_text(yaml.safe_dump({"manifest_version":1,"entry_point":required_schema_files[0],"schema":{"release":"3.0","revision":7,"revised":"2020-05-18"},"codelists":{"issue":74},"sources":{"authoritative":{"authority":"EDItEUR","location":"https://www.editeur.org/93/Release-3.0-Downloads/","retrieved_at":"2026-09-29"}},"files":bundle_records}))
        bundle_xml=td/"bundle.xml"
        bundle_xml.write_text("""<ONIXMessage xmlns="http://ns.editeur.org/onix/3.0/reference" release="3.0"><Product><RecordReference>fixture</RecordReference><NotificationType>03</NotificationType><ProductIdentifier><IDValue>9780000000002</IDValue></ProductIdentifier><DescriptiveDetail><ProductForm>ED</ProductForm><TitleDetail><TitleElement><TitleText>Fixture</TitleText></TitleElement></TitleDetail><Contributor><ContributorRole>A01</ContributorRole></Contributor><Language><LanguageCode>eng</LanguageCode></Language></DescriptiveDetail><PublishingDetail><Publisher><PublisherName>Ploos AS</PublisherName></Publisher></PublishingDetail></Product></ONIXMessage>""")
        entry.write_text("""<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="http://ns.editeur.org/onix/3.0/reference" xmlns="http://ns.editeur.org/onix/3.0/reference" elementFormDefault="qualified"><xs:element name="ONIXMessage" type="xs:anyType"/></xs:schema>""")
        bundle_records[0]["sha256"]=hashlib.sha256(entry.read_bytes()).hexdigest()
        bundle_manifest.write_text(yaml.safe_dump({"manifest_version":1,"entry_point":required_schema_files[0],"schema":{"release":"3.0","revision":7,"revised":"2020-05-18"},"codelists":{"issue":74},"sources":{"authoritative":{"authority":"EDItEUR","location":"https://www.editeur.org/93/Release-3.0-Downloads/","retrieved_at":"2026-09-29"}},"files":bundle_records}))
        assert run("onix-bundle-validate",bundle_xml,bundle_manifest).returncode==0
        entry.write_text("<tampered/>")
        assert run("onix-bundle-validate",bundle_xml,bundle_manifest).returncode!=0
        wrong_host=copy.deepcopy(manifest_data); wrong_host["sources"]["authoritative"]["location"]="https://example.invalid/onix.xsd"
        wrong_host_manifest=schema_dir/"WRONG-HOST-MANIFEST.yaml"; wrong_host_manifest.write_text(yaml.safe_dump(wrong_host))
        assert run("onix-schema-verify",wrong_host_manifest).returncode!=0
        insecure=copy.deepcopy(manifest_data); insecure["sources"]["authoritative"]["location"]="http://www.editeur.org/93/Release-3.0-Downloads/"
        insecure_manifest=schema_dir/"INSECURE-SOURCE-MANIFEST.yaml"; insecure_manifest.write_text(yaml.safe_dump(insecure))
        assert run("onix-schema-verify",insecure_manifest).returncode!=0
        downstream=copy.deepcopy(manifest_data); downstream["sources"]["downstream_verification"]={"authority":"Bokbasen","location":"https://api.boknett.no/schema/ONIX_BookProduct_3.0_reference.xsd","file":required_schema_files[0],"sha256":hashlib.sha256(schema_file.read_bytes()).hexdigest()}
        downstream_manifest=schema_dir/"DOWNSTREAM-MANIFEST.yaml"; downstream_manifest.write_text(yaml.safe_dump(downstream))
        assert run("onix-schema-verify",downstream_manifest).returncode==0
        bad_downstream=copy.deepcopy(downstream); bad_downstream["sources"]["downstream_verification"]["location"]="https://example.invalid/schema.xsd"
        bad_downstream_manifest=schema_dir/"BAD-DOWNSTREAM-MANIFEST.yaml"; bad_downstream_manifest.write_text(yaml.safe_dump(bad_downstream))
        assert run("onix-schema-verify",bad_downstream_manifest).returncode!=0
        mismatch_downstream=copy.deepcopy(downstream); mismatch_downstream["sources"]["downstream_verification"]["sha256"]="0"*64
        mismatch_downstream_manifest=schema_dir/"MISMATCH-DOWNSTREAM-MANIFEST.yaml"; mismatch_downstream_manifest.write_text(yaml.safe_dump(mismatch_downstream))
        assert run("onix-schema-verify",mismatch_downstream_manifest).returncode!=0
        bad_date=copy.deepcopy(manifest_data); bad_date["sources"]["authoritative"]["retrieved_at"]="not-a-date"
        bad_date_manifest=schema_dir/"BAD-DATE-MANIFEST.yaml"; bad_date_manifest.write_text(yaml.safe_dump(bad_date))
        assert run("onix-schema-verify",bad_date_manifest).returncode!=0
        future_date=copy.deepcopy(manifest_data); future_date["sources"]["authoritative"]["retrieved_at"]="2999-01-01"
        future_date_manifest=schema_dir/"FUTURE-DATE-MANIFEST.yaml"; future_date_manifest.write_text(yaml.safe_dump(future_date))
        assert run("onix-schema-verify",future_date_manifest).returncode!=0
        failed_report=td/"failed-qualification.json"; failed_report.write_text(json.dumps({"status":"FAIL"}))
        assert run("provenance",META,"--git-commit",fixture_commit,"--qualification",failed_report,"-o",td/"bad-provenance.json").returncode!=0
        cfg=td/"package.yaml"
        cfg.write_text(PKG.read_text().replace("output_dir: packages",f"output_dir: {td/'packages'}"))
        assert run("package",META,cfg,"--channel","amazon","--language","nb","--epub",epub,"--cover",cover).returncode!=0
        qualified_meta=td/"qualified.yaml"; qualified_data=copy.deepcopy(base)
        qualified_data["lifecycle"]["status"]="qualified"
        qualified_meta.write_text(yaml.safe_dump(qualified_data,sort_keys=False,allow_unicode=True))
        assert run("package",qualified_meta,cfg,"--channel","amazon","--language","nb","--epub",epub,"--cover",cover).returncode==0
        published_meta=td/"published.yaml"; published_data=copy.deepcopy(base)
        published_data["lifecycle"]["status"]="published"
        published_meta.write_text(yaml.safe_dump(published_data,sort_keys=False,allow_unicode=True))
        assert run("package",published_meta,cfg,"--channel","amazon","--language","nb","--epub",epub,"--cover",cover).returncode==0
        archived_meta=td/"archived.yaml"; archived_data=copy.deepcopy(base)
        archived_data["lifecycle"]["status"]="archived"
        archived_meta.write_text(yaml.safe_dump(archived_data,sort_keys=False,allow_unicode=True))
        assert run("package",archived_meta,cfg,"--channel","amazon","--language","nb","--epub",epub,"--cover",cover).returncode!=0
        package=td/"packages"/"amazon"/"nb"
        assert (package/"metadata.json").is_file()
        assert len(json.loads((package/"manifest.json").read_text())["artifacts"])==2
        first={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in package.iterdir() if p.is_file()}
        assert run("package",published_meta,cfg,"--channel","amazon","--language","nb","--epub",epub,"--cover",cover).returncode==0
        second={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in package.iterdir() if p.is_file()}
        assert first==second
        assert all(int(p.stat().st_mtime)==0 for p in package.iterdir() if p.is_file())
    print("Publishing M1/M2/M3 self-test PASS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
