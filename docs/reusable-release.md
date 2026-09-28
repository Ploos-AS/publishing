# Reusable book release workflow

Book repositories can use the canonical Ploos Publishing release pipeline without copying publishing logic into each repository.

```yaml
jobs:
  release:
    uses: Ploos-AS/publishing/.github/workflows/reusable-book-release.yml@main
    with:
      metadata: publication.yaml
      build_config: metadata/build.yaml
      epub: dist/book.epub
      pdf: dist/book.pdf
      artifact_name: book-release
```

The workflow performs, in order:

1. optional project build
2. canonical metadata validation
3. external EPUBCheck
4. internal qualification
5. provenance generation tied to the caller's `GITHUB_SHA`
6. provenance verification
7. upload of metadata, publication artifacts, qualification report and provenance manifest

The EPUB is required. PDF and build configuration are optional.

For production releases, callers should pin this reusable workflow to a qualified version tag rather than `@main`. The example uses `@main` only to show the integration shape while M3 is in progress.
