# books.ploos.no

The public Ploos AS book catalog is generated from the canonical publishing catalog. No separate book database is required.

## Build

```sh
python scripts/ploos_publish.py catalog publication.yaml -o dist/catalog.json
python scripts/ploos_publish.py books-site dist/catalog.json --output-dir dist/books
```

The generated tree contains:

- `index.html` — static human-readable catalog
- `api/books.json` — machine-readable catalog API

Only publications present in the input catalog are exposed. The normal `catalog` command includes only lifecycle state `published`; use of `--include-unpublished` is intended for previews and tests.

Generation is deterministic for identical catalog input, and generated file timestamps are normalized.
