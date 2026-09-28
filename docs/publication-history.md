# Publication history and superseded editions

Ploos Publishing preserves publication history instead of overwriting an older edition.

A new edition may identify the edition it supersedes:

```yaml
edition:
  number: 2
  revision: 1
  supersedes:
    work_id: edu-numbers
    edition: 1
```

`work_id` identifies the work and `edition` identifies the prior edition. A publication cannot supersede itself.

## Rules

- A new edition is a new bibliographic edition, not a rewrite of the previous record.
- Existing ISBN allocations remain attached to their original products.
- New products receive their own ISBNs when ISBN policy requires it.
- Revisions remain changes within an edition and do not use `supersedes`.
- Archived metadata and artifacts for older editions remain auditable.
- Catalog/API output carries the edition object, including `supersedes`, so clients can reconstruct edition history.

This model also permits a future edition to supersede an edition represented by a different work ID when a work has been deliberately replaced or renamed.
