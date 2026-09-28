# M3 production qualification — EduNumbers

EduNumbers is the first real Ploos publication qualified through the M3 reusable release pipeline.

## Qualified source

- Repository: `Ploos-AS/EduNumbers`
- Commit: `839517114abd87eca24f62ab65bdab46d2775a61`
- GitHub Actions run: `36495599745`
- Result: **PASS**
- Languages: Norwegian (nb) and English (en)

## Verified jobs

- `qualify-no / qualify-release`: PASS
- `qualify-en / qualify-release`: PASS

The same source revision also passed the project's normal course build, Pages deployment and desktop workflows.

## Qualified artifacts

The M3 pilot produced two GitHub Actions artifact bundles:

- `edunumbers-no-qualified`
- `edunumbers-en-qualified`

Each reusable release job performed the publication build, canonical metadata validation, external EPUBCheck, internal qualification, provenance generation and provenance verification before uploading the qualified artifacts.

This qualification demonstrates the production pipeline on real Ploos publication sources. It does not assign or imply production ISBNs; EduNumbers ISBN values remain `PENDING` until official Ploos AS ISBN allocation is available.
