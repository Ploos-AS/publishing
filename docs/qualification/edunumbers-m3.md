# M3 production qualification — EduNumbers

EduNumbers is the first real Ploos publication qualified through the M3 reusable release pipeline with the publishing toolchain pinned by Git commit.

## Qualified source

- Repository: `Ploos-AS/EduNumbers`
- Commit: `823a8c37a97de5e4729941991922eb0130d2ba71`
- GitHub Actions run: `36507604701`
- Publishing workflow/toolchain: `2adcb5a3dbc8d06249731d3ff926ac9b51cc8edf`
- Result: **PASS**
- Languages: Norwegian (nb) and English (en)

GitHub recorded the referenced reusable workflow at the exact publishing commit above. The caller also supplied the same commit as `publishing_ref`, pinning the checked-out publishing implementation to the workflow definition.

## Verified jobs

- `qualify-no / qualify-release`: PASS
- `qualify-en / qualify-release`: PASS

Both jobs completed publication build, canonical metadata validation, external EPUBCheck, internal qualification, provenance generation, provenance verification and qualified-artifact upload.

## Qualified artifacts

- `edunumbers-no-qualified` — artifact `11007733294`
- `edunumbers-en-qualified` — artifact `11007738065`

## Earlier pilot

The earlier successful pilot at EduNumbers commit `839517114abd87eca24f62ab65bdab46d2775a61`, Actions run `36495599745`, established the pipeline before strict toolchain pinning. It remains useful historical evidence but is superseded by the pinned qualification above.

This qualification does not assign or imply production ISBNs. EduNumbers ISBN values remain `PENDING` until official Ploos AS ISBN allocation is available.
