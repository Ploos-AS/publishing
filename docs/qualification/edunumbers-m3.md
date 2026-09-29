# M3 production qualification — EduNumbers

EduNumbers is the first real Ploos publication qualified through the M3 reusable release pipeline with canonical metadata, pinned publishing tooling and the canonical ISBN registry gate enabled.

## Current qualified source

- Repository: `Ploos-AS/EduNumbers`
- Commit: `6ffa5940dde857661ae79abe12a644f2c1226efa`
- GitHub Actions run: `36567797576`
- Publishing workflow/toolchain: `fbe925104c8553b6a997a044fdf4703a32a21dfc`
- ISBN registry: `.ploos-publishing/isbn/registry.yaml`
- Result: **PASS**
- Languages: Norwegian (nb) and English (en)

The caller pins both the reusable workflow reference and `publishing_ref` to the publishing commit above. Both language jobs therefore use the same immutable publishing implementation and cross-check `publication.yaml` against the canonical Ploos ISBN registry.

## Verified jobs

- `qualify-no / qualify-release`: PASS
- `qualify-en / qualify-release`: PASS

Both jobs completed publication build, canonical metadata validation, ISBN registry cross-check, external EPUBCheck, internal qualification, provenance generation, provenance verification and qualified-artifact upload.

## Qualified artifacts

- `edunumbers-no-qualified` — artifact `11032607711`
- `edunumbers-en-qualified` — artifact `11032692754`

## Qualification history

The pinned qualification at EduNumbers commit `823a8c37a97de5e4729941991922eb0130d2ba71`, Actions run `36507604701`, proved the pinned reusable pipeline using publishing commit `2adcb5a3dbc8d06249731d3ff926ac9b51cc8edf`.

A later run at commit `c278733d965fe2968a59fe1e1e9aa278a502d4f3`, Actions run `36509810586`, qualified the source after the Pandoc book metadata was aligned with the canonical titles and author.

The earlier pilot at commit `839517114abd87eca24f62ab65bdab46d2775a61`, Actions run `36495599745`, established the pipeline before strict toolchain pinning.

The current qualification supersedes these as production evidence because it combines canonical source metadata, immutable publishing tooling and the ISBN registry consistency gate.

This qualification does not assign or imply production ISBNs. EduNumbers ISBN values remain `PENDING` until official Ploos AS ISBN allocation is available.
