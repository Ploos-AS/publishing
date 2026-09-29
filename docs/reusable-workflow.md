# Reusable publishing workflow contract

This document defines the stable consumer interface for the Ploos Publishing reusable validation workflow.

## Consumer

Projects adopting `PLOOS-PROJECT-1` with the `publishing` capability should consume the reusable workflow through a qualified stable major tag:

```yaml
jobs:
  publishing:
    uses: Ploos-AS/publishing/.github/workflows/reusable-book-validate.yml@v1
    with:
      metadata: publication.yaml
      epub: dist/book.epub
```

Do not use `@main` for release qualification.

## v1 inputs

- `metadata`: publication metadata path; default `publication.yaml`.
- `epub`: optional EPUB path. When supplied, EPUBCheck and publication qualification run.
- `qualification_artifact`: optional artifact name; default `publishing-qualification`.

The workflow checks out the consumer repository, obtains the versioned Ploos Publishing tooling, validates publication metadata, optionally validates EPUB, and emits qualification evidence.

## Ownership boundary

The consumer repository owns:

- canonical manuscript/course sources;
- project-specific build commands;
- project-specific publication metadata;
- generated outputs before validation.

Ploos Publishing owns:

- the canonical `publication.yaml` contract and policy;
- reusable validation;
- EPUB qualification;
- publication qualification/report conventions.

## Compatibility

The `v1` major alias is a compatibility promise. New optional inputs and stricter checks that only reject previously invalid publications may be added compatibly. Removing or renaming inputs, changing valid metadata meaning, or otherwise breaking conforming consumers requires a new major contract.

The stable `v1` alias must only be moved to a revision after the publishing repository's own validation and self-test workflows are green.


## Metadata format

The v1 workflow consumes the canonical `publication.yaml` shape documented in `metadata/publication.example.yaml`. The older `metadata/book.schema.yaml` / `book.example.yaml` shape is pre-v1 legacy material and is not a valid substitute for this workflow contract.
