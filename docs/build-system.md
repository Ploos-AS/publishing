# Build system

`ploos-publish build` is an orchestrator, not a book authoring engine.

Each book repository owns its source format and declares deterministic build commands in a build configuration. Ploos Publishing runs those commands, records failures and verifies declared outputs.

This keeps the publishing layer compatible with Markdown/Pandoc, Sphinx, custom Python tooling, or future authoring systems without changing the publication model.

## Contract

A build configuration contains:

- optional clean/setup commands
- named targets
- one command per target
- one or more expected output files

A successful command is not sufficient: every declared output must exist.

## Recommended outputs

```text
dist/
  web/
  <localized-title>.epub
  <localized-title>.pdf
```

Build repositories should pin their own toolchain versions where practical. Release manifests record hashes of the resulting artifacts.
