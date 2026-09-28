# Ploos Publishing Policy

Version: 0.1-draft

## Publisher

Publisher: **Ploos AS**

This repository is the canonical source for publishing conventions used by Ploos AS book and course projects.

## Languages

- Norwegian Bokmål: `nb`
- English: `en`

A translation is treated as a distinct edition/product for metadata and ISBN tracking.

## Output formats

Projects may publish:

- Web/HTML
- EPUB
- Kindle-friendly ebook
- PDF

The web edition normally does not receive an ISBN. Ebook and PDF products are tracked separately so that an official ISBN can be assigned to each product when required.

## ISBN rules

1. Only officially assigned ISBNs may be entered as active ISBNs.
2. Before assignment, use the literal status `PENDING`; never create realistic-looking placeholders.
3. Each language/format product is tracked separately.
4. ISBN allocation is recorded centrally in `isbn/registry.yaml` before it is released in a project repository.
5. An ISBN must never be silently reused for a materially different edition or product.
6. Minor typo corrections that do not constitute a new edition should retain the existing product identity; substantial edition changes must be reviewed before reuse.
7. Metadata in generated EPUB/PDF/Kindle outputs must agree with the central registry.

## Edition and release metadata

Every publishable book should define at least:

- title
- optional subtitle
- publisher
- language
- edition
- publication year/date
- authors/contributors as applicable
- license/copyright statement
- output formats
- ISBN status for each ISBN-bearing product

## Colophon

Every ISBN-bearing artifact should contain a generated colophon/front-matter block with publisher, edition, copyright/license and the ISBNs for relevant formats.

## Source of truth

Book repositories own their editorial content. This repository owns the common publishing policy, metadata conventions, central ISBN registry and reusable templates.

## CI expectations

CI should eventually validate that:

- ISBN syntax/check digits are valid once assigned
- no ISBN occurs twice for different products
- project metadata matches the central registry
- required metadata is present
- `PENDING` cannot accidentally be shipped in a production release advertised as ISBN-assigned
