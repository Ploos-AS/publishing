# Archive and reproducibility audit

Ploos Publishing records the exact files that make up publication evidence.

Create an archive manifest:

```sh
ploos-publish archive publication.yaml \
  dist/book.epub dist/book.pdf dist/accessibility.json dist/onix.xml \
  -o dist/archive-manifest.json
```

The manifest records canonical metadata identity, edition/revision, byte size and SHA-256 for the metadata file and every supplied release artifact. Artifact records are sorted by path and JSON keys are sorted to make repeated manifest generation deterministic for the same inputs and paths.

Audit it later:

```sh
ploos-publish audit dist/archive-manifest.json
```

The audit fails if metadata or an artifact is missing, has a different byte size, or has a different SHA-256 digest. This detects modification and loss of archived publication evidence.

The manifest proves integrity of the recorded files. Bit-for-bit reproducible *rebuilding* additionally requires deterministic upstream book builds and pinned toolchains; that is a separate property and should not be inferred solely from a passing archive audit.
