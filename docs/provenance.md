# Release provenance

Ploos Publishing records a verifiable chain from source revision to qualified publication artifacts.

## Create

```sh
python scripts/ploos_publish.py provenance publication.yaml \
  --git-commit "$GITHUB_SHA" \
  --qualification qualification.json \
  --artifact book.epub \
  --artifact book.pdf \
  -o provenance.json
```

The qualification report must have status `PASS`. The manifest records the exact 40-character Git commit plus byte size and SHA-256 for metadata, qualification report and every publication artifact.

## Verify

```sh
python scripts/ploos_publish.py provenance-verify provenance.json
```

Verification checks the recorded files against their sizes and SHA-256 hashes and confirms that the qualification report still reports `PASS`.

This provides artifact integrity and traceability to a Git revision. It does not by itself prove that the artifacts were reproducibly built from that revision; reproducible build qualification remains a separate property.
