# ISBN registry and allocation

`isbn/registry.yaml` is the canonical Ploos AS ISBN allocation registry.

## Model

Planned publications identify works that may later receive ISBN-bearing products. They do not carry an ISBN themselves.

Official ISBNs are imported into `isbn_pool`. Allocation moves an ISBN logically from the available pool to a product identity recorded in `allocations`.

The canonical allocation identity is:

```text
project + edition + language + product
```

For example, Norwegian EPUB and PDF editions are separate products, and a second edition is distinct from the first edition.

## Normalization

ISBN comparisons remove spaces and hyphens before checksum and uniqueness checks. Therefore formatted and compact spellings of the same ISBN cannot be allocated as separate identifiers.

## Commands

Validate the registry:

```sh
python scripts/ploos_publish.py isbn-validate isbn/registry.yaml
```

Import an official list:

```sh
python scripts/ploos_publish.py isbn-import isbn/registry.yaml official-isbns.txt --write
```

Allocate deterministically from the pool:

```sh
python scripts/ploos_publish.py isbn-allocate isbn/registry.yaml \
  --project EduNumbers --edition 1 --language nb --product epub --write
```

Production ISBNs must come from the official Ploos AS allocation. Do not use realistic placeholders.
