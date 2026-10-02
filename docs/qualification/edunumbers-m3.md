# M3 production qualification — EduNumbers

EduNumbers is the first real Ploos publication qualified through the M3 reusable release pipeline with canonical metadata, pinned publishing tooling and the canonical ISBN registry gate enabled.

## Current qualified source

- Repository: `Ploos-AS/EduNumbers`
- Commit: `8e39dcd30babc35c5de25f23e4222c4d45aa659b`
- GitHub Actions run: `37043217337`
- Publishing workflow/toolchain: `4fc45a0a54b3ce1cb01d12ed3ca255b18d47ec91`
- ISBN registry: `.ploos-publishing/isbn/registry.yaml`
- Result: **PASS**
- Languages: Norwegian (nb) and English (en)

The caller pins both the reusable workflow reference and `publishing_ref` to the publishing commit above. Both language jobs therefore use the same immutable publishing implementation and cross-check `publication.yaml` against the canonical Ploos ISBN registry.

## Verified jobs

- `qualify-no / qualify-release`: PASS
- `qualify-en / qualify-release`: PASS

Both jobs completed publication build, canonical metadata validation, ISBN registry cross-check, external EPUBCheck, internal qualification, provenance generation, provenance verification and qualified-artifact upload.

## Qualified artifacts

- `edunumbers-no-qualified` — artifact `11243146508` — SHA-256 `4391a1ba758d4e5b8a8514a6d54673e998b11123c24cdb029b222c73256c60a7`
- `edunumbers-en-qualified` — artifact `11243330916` — SHA-256 `4d8269d7656d067719a0196de51483f2c0a709fc83dc82394aa4358024ea10c5`

## Qualification history

The pinned qualification at EduNumbers commit `823a8c37a97de5e4729941991922eb0130d2ba71`, Actions run `36507604701`, proved the pinned reusable pipeline using publishing commit `2adcb5a3dbc8d06249731d3ff926ac9b51cc8edf`.

A later run at commit `c278733d965fe2968a59fe1e1e9aa278a502d4f3`, Actions run `36509810586`, qualified the source after the Pandoc book metadata was aligned with the canonical titles and author.

The earlier pilot at commit `839517114abd87eca24f62ab65bdab46d2775a61`, Actions run `36495599745`, established the pipeline before strict toolchain pinning.

The current qualification supersedes these as production evidence because it combines canonical source metadata, immutable publishing tooling and the ISBN registry consistency gate.

Ploos AS has publisher prefix `978-82-94310`, and EduNumbers edition 1 has six canonical allocations: EPUB, Kindle and PDF for both Norwegian and English. The current qualification cross-checked production metadata against those canonical allocations successfully.


## ONIX Issue 74 qualification

The authoritative EDItEUR ONIX 3.0 bundle is now pinned under `vendor/onix/` with Codelists Issue 74 and SHA-256 integrity records in `MANIFEST.yaml`.

At publishing commit `9576921ba1c5b26f561cb33281fe7b391c45e43c`:

- Validate publishing metadata — run `37042091407`: **PASS**
- Publishing self-test — run `37042091378`: **PASS**
- pinned bundle integrity verification: **PASS**
- generated ONIX structural validation: **PASS**
- EDItEUR Release 3.0 Revision 7 XSD validation: **PASS**

This closes the authoritative ONIX-bundle gate. EduNumbers NO and EN have also passed the current production qualification, so the M3 qualification gates are complete.
