# ISBN registry and allocation

`isbn/registry.yaml` is the canonical Ploos AS ISBN allocation registry.

## Model

Planned publications identify works that may later receive ISBN-bearing products. They do not carry an ISBN themselves.

Official ISBNs are imported into `isbn_pool`. Allocation moves an ISBN logically from the available pool to a product identity recorded in `allocations`.

The canonical allocation identity is:

```text
project + edition + language + product
```

For example, Norwegian EPUB, Kindle and PDF editions are separate products, and a second edition is distinct from the first edition.

## Publisher-prefix state

The initial registry state was:

```yaml
prefix_status: pending
publisher_prefix: null
isbn_pool: []
```

Ploos AS has now completed the prefix assignment and official pool import. The canonical registry records publisher prefix `978-82-94310`; the 100-number official pool is the only source for production allocation.

The allocation sequence is:

```text
pending
  -> record the official Ploos AS publisher prefix
assigned
  -> import official ISBNs
isbn_pool populated
  -> allocate by project + edition + language + product
```

`isbn-import` refuses to run while the prefix is pending. Registry validation also rejects a non-empty ISBN pool in that state. Importing ISBNs does not itself change agency status; the official prefix assignment must be recorded explicitly from the agency information.

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

Production ISBNs must come from the official Ploos AS allocation. Do not use realistic placeholders. The primary digital product set is EPUB, Kindle and PDF; store identifiers such as Amazon ASIN remain separate distribution metadata.
