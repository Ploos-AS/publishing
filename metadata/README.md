# Metadata contract

## Canonical v1 format

New and migrated Ploos publication projects use a repository-root `publication.yaml` based on `publication.example.yaml`.

Validation is performed by:

```sh
python scripts/ploos_publish.py validate publication.yaml
```

The active contract includes:

- stable project and work identity;
- structured edition/revision/year;
- lifecycle status;
- language-specific publication records;
- Ploos AS author/publisher/copyright/license policy;
- per-product ISBN state;
- distribution and optional legal-deposit metadata.

## Legacy pre-v1 format

`book.schema.yaml` and `book.example.yaml` are retained only as migration references. They are not the contract consumed by the reusable v1 workflow and must not be copied into new projects.

Do not add new features to the legacy shape. Migrate consumers to `publication.yaml`.
