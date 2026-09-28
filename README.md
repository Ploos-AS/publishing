# Ploos Publishing

Central repository for publishing standards, metadata, ISBN allocation and reusable book-production assets for Ploos AS.

## Status

ISBN application has been submitted to ISBN Norway / the National Library of Norway. Until a publisher prefix and ISBN range are assigned, this repository uses explicit `PENDING` values only. Do not invent, reserve locally, or publish placeholder ISBNs that resemble real ISBNs.

## Scope

This repository is the canonical source for:

- publishing policy and edition rules
- ISBN allocation and status
- reusable `book.yaml` metadata schema/examples
- colophon/front-matter templates
- language and format conventions
- CI validation rules for book repositories
- release/publication checklists
- the cross-project `PLOOS-PROJECT-1` lifecycle and integration standard

## Initial format policy

Ploos AS course books are expected to be published in four first-class outputs where applicable:

- Web/HTML
- EPUB
- Kindle-friendly ebook
- PDF

Norwegian (`nb`) is normally the primary language and English (`en`) a parallel edition when the project supports both.

ISBN assignment is tracked per publication product. No ISBN is assigned until the official ISBN range has been received.

## Repository layout

```text
publishing/
├── README.md
├── POLICY.md
├── isbn/
│   └── registry.yaml
├── metadata/
│   ├── book.schema.yaml
│   └── book.example.yaml
└── templates/
    └── colophon.md
```

## Ploos project standard

Ploos AS projects should adopt [PLOOS-PROJECT-1](standards/PLOOS-PROJECT-1.md). It defines the shared capability-based lifecycle:

`source -> validate -> test -> qualify -> build -> publish -> release`

Qualification is delegated to stable `Ploos-AS/hardware-ci` workflows where applicable. Publishing policy and reusable production conventions remain canonical here.

## Reusable workflow

Publishing-capable PLOOS-PROJECT-1 consumers use the versioned reusable workflow contract documented in [docs/reusable-workflow.md](docs/reusable-workflow.md). Release qualification must use a qualified stable major alias such as `@v1`, not `@main`.

## Canonicality

`main` is canonical. Project repositories should consume or copy versioned publishing metadata/templates from this repository rather than inventing incompatible local conventions.
